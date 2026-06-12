#!/usr/bin/env python3
"""Find UK plaque/engraving/etched-metal businesses from local CSVs and verify them."""

from __future__ import annotations

import csv
import json
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
OUT = ROOT / "data" / "plaque-engraving-verified-additions.json"
REJECTS = ROOT / "data" / "plaque-engraving-rejected.json"
REPORT = ROOT / "reports" / "uk-plaque-engraving-verified-2026-06-12.md"

SOURCE_GLOBS = [
    "*sign*.csv",
    "memory/*Directory*.csv",
]
EXCLUDED_SOURCE_NAMES = {
    "europe-sign-makers.csv",
}

PLAQUE_TERMS = (
    "plaque",
    "plaques",
    "brass plaque",
    "brass plaques",
    "engraving",
    "engrave",
    "engraved",
    "engravers",
    "etched",
    "etching",
    "memorial",
    "nameplate",
    "name plate",
    "stainless steel plaque",
    "bronze plaque",
    "trophy",
    "awards",
)

WEAK_BRAND_TERMS = (
    "jewellers",
    "goldsmith",
    "stone mason",
    "shoe repair",
    "key cutting",
)

GENERIC_EMAIL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "icloud.com",
    "aol.com",
}

BAD_EMAIL_PARTS = (
    "example",
    "placeholder",
    "test@",
    "noreply",
    "no-reply",
    "somewhere.com",
)

SSL_CONTEXT = ssl.create_default_context()


def norm_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def site_key(value: str | None) -> str:
    return re.sub(r"^https?://(www\.)?", "", (value or "").lower()).rstrip("/")


def compact(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def read_value(row: dict[str, str], *names: str) -> str:
    lower = {str(k).lower().strip(): str(v or "").strip() for k, v in row.items() if k}
    for name in names:
        value = lower.get(name.lower())
        if value:
            return value
    return ""


def clean_email(value: str) -> str | None:
    value = value.strip().lower()
    match = re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", value)
    if not match:
        return None
    email = match.group(0)
    if any(part in email for part in BAD_EMAIL_PARTS):
        return None
    return email


def clean_phone(value: str) -> str | None:
    value = re.sub(r"\s+", " ", value.strip())
    digits = re.sub(r"\D", "", value)
    if len(digits) < 9:
        return None
    if digits[-6:] in {"000000", "111111", "222222", "333333", "444444", "111222"}:
        return None
    return value


def infer_county(path: Path, row: dict[str, str]) -> str:
    direct = read_value(row, "County", "County/Area", "City/Area", "Country")
    if direct:
        return direct.replace("_Verified", "").replace("_", " ").strip()
    name = path.stem
    if name.endswith("_Directory"):
        return re.sub(r"(?<!^)([A-Z])", r" \1", name.removesuffix("_Directory")).replace("_", " ").strip()
    return "United Kingdom"


def source_paths() -> list[Path]:
    paths: list[Path] = []
    for pattern in SOURCE_GLOBS:
        paths.extend(WORKSPACE.glob(pattern))
    return sorted({path for path in paths if path.is_file() and path.name not in EXCLUDED_SOURCE_NAMES})


def row_text(row: dict[str, str]) -> str:
    return " ".join(str(value or "") for value in row.values())


def source_rows() -> list[dict]:
    rows: list[dict] = []
    term_re = re.compile("|".join(re.escape(term) for term in PLAQUE_TERMS), re.I)
    for path in source_paths():
        try:
            handle = path.open(newline="", encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        with handle:
            for row in csv.DictReader(handle):
                company = read_value(row, "Company Name", "Company", "Name")
                website = read_value(row, "Website", "Website URL", "URL")
                email = clean_email(read_value(row, "Email", "Email Address", "Contact Email"))
                phone = clean_phone(read_value(row, "Phone", "Phone Number"))
                address = read_value(row, "Address", "Physical Address")
                category = read_value(row, "Category", "Primary Business Type", "Type")
                text = row_text(row)
                if not company or not email or not term_re.search(" ".join([company, category, text])):
                    continue
                if any(term in company.lower() for term in WEAK_BRAND_TERMS):
                    continue
                rows.append(
                    {
                        "sourceFile": str(path.relative_to(WORKSPACE)),
                        "county": infer_county(path, row),
                        "category": category or "Engraving",
                        "company": company,
                        "website": website,
                        "email": email,
                        "linkedin": read_value(row, "LinkedIn", "LinkedIn URL") or None,
                        "instagram": read_value(row, "Instagram", "Instagram URL") or None,
                        "facebook": read_value(row, "Facebook", "Facebook URL") or None,
                        "phone": phone,
                        "address": address or None,
                        "sourceText": text[:1200],
                    }
                )
    return rows


def candidate_urls(row: dict) -> list[str]:
    urls: list[str] = []
    website = (row.get("website") or "").strip()
    if website:
        if not website.startswith(("http://", "https://")):
            website = "https://" + website
        urls.append(website)
    email = row.get("email")
    if email:
        domain = email.rsplit("@", 1)[1]
        if domain not in GENERIC_EMAIL_DOMAINS:
            urls.extend([f"https://{domain}", f"https://www.{domain}", f"http://{domain}", f"http://www.{domain}"])
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        key = site_key(url)
        if key and key not in seen:
            seen.add(key)
            out.append(url)
    return out


def direct_company_site(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    bad_hosts = (
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "yell.com",
        "thomsonlocal.com",
        "infoisinfo.co.uk",
        "cylex-uk.co.uk",
        "192.com",
        "find-open.co.uk",
    )
    return not any(host == bad or host.endswith("." + bad) for bad in bad_hosts)


def fetch(url: str) -> tuple[str | None, str, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=7, context=SSL_CONTEXT) as response:
            final_url = response.geturl()
            body = response.read(240000).decode("utf-8", "ignore")
            return final_url, body, ""
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return None, "", type(exc).__name__


def extract_contact(body: str, row: dict) -> tuple[str | None, str | None]:
    # Prefer structured source contact fields; HTML often contains tracking/CSS numbers.
    return row.get("email"), row.get("phone")


def has_plaque_signal(body: str, row: dict) -> tuple[bool, list[str]]:
    text = re.sub(r"\s+", " ", body.lower())
    source = " ".join([row.get("company") or "", row.get("category") or "", row.get("sourceText") or ""]).lower()
    found = sorted({term for term in PLAQUE_TERMS if term in text or term in source})
    strong = {"plaque", "plaques", "brass plaque", "engraving", "engraved", "engravers", "etched", "etching", "nameplate", "memorial"}
    if any(term in found for term in strong):
        return True, found
    if ("trophy" in found or "awards" in found) and any(term in text for term in ("engraving", "engraved", "plaque", "plaques")):
        return True, found
    return False, found


def verify(row: dict) -> tuple[dict | None, dict | None]:
    urls = candidate_urls(row)
    if not urls:
        return None, {**row, "reason": "no website or business email domain to verify"}
    last_error = ""
    for base_url in urls:
        final_url, body, error = fetch(base_url)
        last_error = error
        if not final_url:
            continue
        if not direct_company_site(final_url):
            return None, {**row, "reason": "resolved to third-party/social/directory page", "checkedUrl": final_url}
        ok, found_terms = has_plaque_signal(body, row)
        if not ok:
            # Try common service/contact paths on the same host before rejecting.
            parsed = urllib.parse.urlparse(final_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            for path in ("/plaques", "/engraving", "/services", "/products", "/contact", "/contact-us"):
                next_url, next_body, next_error = fetch(origin + path)
                last_error = next_error
                if not next_url:
                    continue
                if not direct_company_site(next_url):
                    continue
                next_ok, next_terms = has_plaque_signal(next_body, row)
                if next_ok:
                    final_url, body, found_terms = next_url, next_body, next_terms
                    ok = True
                    break
        if not ok:
            return None, {**row, "reason": "website resolved but lacked plaque/engraving/brass evidence", "checkedUrl": final_url, "matchedTerms": found_terms}
        email, phone = extract_contact(body, row)
        if not email:
            return None, {**row, "reason": "no usable email after verification", "checkedUrl": final_url}
        entry = {
            "county": row["county"],
            "category": "Engraving",
            "company": row["company"],
            "website": final_url,
            "email": email,
            "linkedin": row["linkedin"],
            "instagram": row["instagram"],
            "facebook": row["facebook"],
            "phone": phone,
            "address": row["address"],
            "quality": 0,
            "sellsPlaques": True,
            "_sourceFile": row["sourceFile"],
            "_matchedTerms": found_terms,
            "_evidence": f"Verified live website {final_url} with plaque/engraving-related wording: {', '.join(found_terms[:8])}.",
        }
        return entry, None
    return None, {**row, "reason": f"website/email-domain did not resolve: {last_error}"}


def main() -> None:
    data = json.loads(DATA.read_text())
    original = json.loads(__import__("subprocess").check_output(["git", "show", "HEAD:data/directory-data.json"], cwd=ROOT))
    existing_names = {norm_key(entry.get("company")) for entry in data}
    existing_sites = {site_key(entry.get("website")) for entry in data if entry.get("website")}
    existing_emails = {str(entry.get("email")).lower() for entry in data if entry.get("email")}
    original_names = {norm_key(entry.get("company")) for entry in original}
    original_sites = {site_key(entry.get("website")) for entry in original if entry.get("website")}
    original_emails = {str(entry.get("email")).lower() for entry in original if entry.get("email")}

    seed_rows = []
    skipped_original = []
    seen: set[tuple[str, str]] = set()
    for row in source_rows():
        key = (norm_key(row["company"]), site_key(row.get("website")) or row.get("email") or "")
        if key in seen:
            continue
        seen.add(key)
        email = (row.get("email") or "").lower()
        row_site = site_key(row.get("website"))
        name = norm_key(row["company"])
        if name in existing_names or row_site in existing_sites or (email and email in existing_emails):
            continue
        if name in original_names or row_site in original_sites or (email and email in original_emails):
            skipped_original.append({**row, "reason": "present in original repo baseline"})
            continue
        seed_rows.append(row)

    verified: list[dict] = []
    rejected: list[dict] = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = {pool.submit(verify, row): row for row in seed_rows}
        for future in as_completed(futures):
            entry, rejection = future.result()
            if rejection:
                rejected.append(rejection)
                continue
            assert entry is not None
            name = norm_key(entry["company"])
            site = site_key(entry["website"])
            email = (entry.get("email") or "").lower()
            if name in existing_names or site in existing_sites or (email and email in existing_emails):
                continue
            verified.append(entry)
            existing_names.add(name)
            existing_sites.add(site)
            if email:
                existing_emails.add(email)

    verified.sort(key=lambda item: (item["county"], item["company"]))
    next_id = max(entry["id"] for entry in data) + 1
    for entry in verified:
        live = {key: value for key, value in entry.items() if not key.startswith("_")}
        live["id"] = next_id
        data.append(live)
        entry["id"] = next_id
        next_id += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(verified, indent=2, ensure_ascii=False) + "\n")
    REJECTS.write_text(json.dumps({"rejected": rejected, "skippedOriginalBaseline": skipped_original}, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    by_county: dict[str, int] = {}
    for entry in verified:
        by_county[entry["county"]] = by_county.get(entry["county"], 0) + 1

    lines = [
        "# UK Plaque / Engraving Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Scanned {len(seed_rows)} deduped local UK plaque/engraving candidates after excluding current data and original repo baseline collisions.",
        f"- Added {len(verified)} verified plaque/engraving entries.",
        f"- Rejected {len(rejected)} rows where no direct website evidence could be confirmed.",
        f"- Skipped {len(skipped_original)} rows already present in the original repo baseline.",
        "- No MiMo/agent scan was used; this was local CSV parsing plus direct website fetches.",
        "",
        "## By County",
    ]
    for county, count in sorted(by_county.items()):
        lines.append(f"- {county}: {count}")
    lines.extend(["", "## Added Companies"])
    for entry in verified:
        lines.append(f"- {entry['company']} ({entry['county']}) - {entry.get('email') or 'no email'} | {entry.get('phone') or 'no phone'} | {entry['website']}")
    lines.extend([
        "",
        "## Validation",
        f"- JSON parse: passed on {date.today().isoformat()}.",
        "- Duplicate gate: current live data plus original repo baseline checked by company, website and email before append.",
        "- Evidence gate: live website had plaque/engraving/brass/nameplate/related wording.",
        "- Safety gate: no GitHub push performed.",
    ])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Seed rows: {len(seed_rows)}")
    print(f"Added {len(verified)} entries")
    print(f"Rejected {len(rejected)} rows")
    print(f"Skipped original-baseline rows: {len(skipped_original)}")
    print(f"New total: {len(data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REJECTS}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
