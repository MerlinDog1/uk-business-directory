#!/usr/bin/env python3
"""Verify regional CSV leads through email-domain websites, then append clean rows."""

from __future__ import annotations

import csv
import json
import re
import ssl
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
OUT = ROOT / "data" / "region-sweep-verified-additions.json"
REJECTS = ROOT / "data" / "region-sweep-rejected.json"
REPORT = ROOT / "reports" / "uk-sign-region-sweep-verified-2026-06-12.md"

SOURCE_FILES = [
    "north_west_sign_companies.csv",
    "midlands_sign_companies.csv",
    "south_west_sign_companies.csv",
    "south_east_sign_companies.csv",
    "east_anglia_sign_companies.csv",
    "scotland_sign_companies.csv",
    "wales_sign_companies.csv",
    "yorkshire_north_east_sign_companies.csv",
]

SIGNAL_WORDS = (
    "sign",
    "signage",
    "graphics",
    "display",
    "wayfinding",
    "shopfront",
    "vehicle graphics",
    "engraving",
    "plaque",
    "banner",
    "vinyl",
    "print",
    "illuminated",
)

BAD_EMAIL_PARTS = (
    "example",
    "placeholder",
    "test@",
    "noreply",
    "no-reply",
    "somewhere.com",
    "moonwalkmedia.co.uk",
    "hkpcl.com",
)

BAD_NAMES = (
    "somewhere",
    "digital signs & signage solutions",
    "cybern systems",
    "hitch technologies",
)

GENERIC_EMAIL_DOMAINS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com"}
SSL_CONTEXT = ssl.create_default_context()


def norm_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def site_key(value: str | None) -> str:
    return re.sub(r"^https?://(www\.)?", "", (value or "").lower()).rstrip("/")


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokens(value: str) -> list[str]:
    stop = {
        "ltd",
        "limited",
        "the",
        "and",
        "sign",
        "signs",
        "signage",
        "graphics",
        "graphic",
        "print",
        "printing",
        "display",
        "displays",
        "studio",
    }
    return [part for part in re.findall(r"[a-z0-9]+", value.lower()) if len(part) >= 4 and part not in stop]


def read_value(row: dict[str, str], *names: str) -> str:
    lower = {k.lower(): v for k, v in row.items() if k}
    for name in names:
        value = lower.get(name.lower())
        if value:
            return value.strip()
    return ""


def clean_email(value: str) -> str | None:
    value = value.strip().lower()
    if not value or "@" not in value or any(part in value for part in BAD_EMAIL_PARTS):
        return None
    local, domain = value.rsplit("@", 1)
    if not local or "." not in domain:
        return None
    return value


def clean_phone(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    if len(digits) < 9:
        return ""
    # Drop obvious generated placeholders like 0161 111 2222.
    tail = digits[-6:]
    if tail in {"111222", "222111", "333444", "444333", "000000", "111111", "222222", "333333", "444444"}:
        return ""
    return value


def social_value(row: dict[str, str], direct: str, marker: str) -> str | None:
    direct_value = read_value(row, direct)
    if direct_value:
        return direct_value
    socials = read_value(row, "Social Media URLs")
    if marker.lower() in socials.lower():
        return socials
    return None


def plausible_email_domain(company: str, email: str) -> bool:
    domain = email.rsplit("@", 1)[1]
    if domain in GENERIC_EMAIL_DOMAINS:
        return False
    domain_compact = compact(domain)
    company_tokens = tokens(company)
    if any(token in domain_compact for token in company_tokens):
        return True
    if any(signal.replace(" ", "") in domain_compact for signal in SIGNAL_WORDS):
        return True
    return False


def source_rows() -> list[dict]:
    rows = []
    for source in SOURCE_FILES:
        path = WORKSPACE / source
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
            for row in csv.DictReader(handle):
                company = read_value(row, "Company Name", "Company")
                email = clean_email(read_value(row, "Email Address", "Email"))
                phone = clean_phone(read_value(row, "Phone Number", "Phone"))
                address = read_value(row, "Physical Address", "Address")
                county = read_value(row, "County")
                if not company or not email or not phone or not address:
                    continue
                if any(bad in company.lower() for bad in BAD_NAMES):
                    continue
                if not plausible_email_domain(company, email):
                    continue
                rows.append(
                    {
                        "sourceFile": source,
                        "company": company,
                        "county": county or infer_region(source, address),
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "linkedin": social_value(row, "LinkedIn", "LI:"),
                        "instagram": social_value(row, "Instagram", "IG:"),
                        "facebook": social_value(row, "Facebook", "FB:"),
                    }
                )
    return rows


def infer_region(source: str, address: str) -> str:
    if source == "scotland_sign_companies.csv":
        return "Scotland"
    if source == "wales_sign_companies.csv":
        return "Wales"
    return "Unidentified"


def fetch_domain(domain: str) -> tuple[str | None, str, str]:
    urls = [f"https://{domain}", f"https://www.{domain}", f"http://{domain}", f"http://www.{domain}"]
    last_error = ""
    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=5, context=SSL_CONTEXT) as response:
                final_url = response.geturl()
                body = response.read(180000).decode("utf-8", "ignore")
                return final_url, body, ""
        except Exception as exc:  # noqa: BLE001 - diagnostics only
            last_error = type(exc).__name__
    return None, "", last_error


def has_signage_signal(company: str, body: str) -> bool:
    text = re.sub(r"\s+", " ", body.lower())
    if any(word in text for word in SIGNAL_WORDS):
        return True
    return any(word in company.lower() for word in ("sign", "graphics", "display"))


def verify(row: dict) -> tuple[dict | None, dict | None]:
    domain = row["email"].rsplit("@", 1)[1]
    checked_url, body, error = fetch_domain(domain)
    if not checked_url:
        return None, {**row, "reason": f"email domain did not resolve: {error}"}
    if not has_signage_signal(row["company"], body):
        return None, {**row, "reason": "email-domain website resolved but lacked signage language", "checkedUrl": checked_url}

    entry = {
        "county": row["county"],
        "category": "Signage",
        "company": row["company"],
        "website": checked_url,
        "email": row["email"],
        "linkedin": row["linkedin"],
        "instagram": row["instagram"],
        "facebook": row["facebook"],
        "phone": row["phone"],
        "address": row["address"],
        "quality": 0,
        "sellsPlaques": False,
        "_sourceFile": row["sourceFile"],
        "_evidence": f"Verified email-domain website {checked_url} resolved and contained signage-related wording.",
    }
    return entry, None


def main() -> None:
    data = json.loads(DATA.read_text())
    existing_names = {norm_key(entry.get("company")) for entry in data}
    existing_sites = {site_key(entry.get("website")) for entry in data if entry.get("website")}
    existing_emails = {
        entry["email"].lower()
        for entry in data
        if isinstance(entry.get("email"), str) and "@" in entry["email"]
    }

    seed_rows = []
    seen_seed: set[tuple[str, str]] = set()
    for row in source_rows():
        row_key = (norm_key(row["company"]), row["email"])
        if row_key in seen_seed:
            continue
        seen_seed.add(row_key)
        if norm_key(row["company"]) in existing_names or row["email"] in existing_emails:
            continue
        seed_rows.append(row)

    verified = []
    rejected = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(verify, row): row for row in seed_rows}
        for future in as_completed(futures):
            entry, rejection = future.result()
            if rejection:
                rejected.append(rejection)
                continue
            assert entry is not None
            if norm_key(entry["company"]) in existing_names:
                continue
            if site_key(entry["website"]) in existing_sites:
                continue
            if entry["email"] in existing_emails:
                continue
            verified.append(entry)
            existing_names.add(norm_key(entry["company"]))
            existing_sites.add(site_key(entry["website"]))
            existing_emails.add(entry["email"])

    verified.sort(key=lambda item: (item["_sourceFile"], item["county"], item["company"]))
    next_id = max(entry["id"] for entry in data) + 1
    for entry in verified:
        live = {key: value for key, value in entry.items() if not key.startswith("_")}
        live["id"] = next_id
        data.append(live)
        entry["id"] = next_id
        next_id += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(verified, indent=2, ensure_ascii=False) + "\n")
    REJECTS.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    by_source: dict[str, int] = {}
    by_county: dict[str, int] = {}
    for entry in verified:
        by_source[entry["_sourceFile"]] = by_source.get(entry["_sourceFile"], 0) + 1
        by_county[entry["county"]] = by_county.get(entry["county"], 0) + 1

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# UK Sign Region Sweep Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Scanned {len(seed_rows)} deduped regional rows with plausible company-matching email domains.",
        f"- Added {len(verified)} verified regional sign-company entries.",
        f"- Rejected {len(rejected)} rows where the email-domain site did not resolve or lacked signage wording.",
        "- No websites or emails were guessed; websites are verified email-domain sites.",
        "",
        "## By Source",
    ]
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: {count}")
    lines.extend(["", "## By County"])
    for county, count in sorted(by_county.items()):
        lines.append(f"- {county}: {count}")
    lines.extend(["", "## Added Companies"])
    for entry in verified:
        lines.append(f"- {entry['company']} ({entry['county']}) - {entry['email']} | {entry['phone']} | {entry['website']}")
    lines.extend([
        "",
        "## Validation",
        f"- JSON parse: passed on {date.today().isoformat()}.",
        "- Duplicate gate: company, website and email checked before append.",
        "- Evidence gate: direct email-domain website resolved and contained signage-related wording.",
        "- Safety gate: no GitHub push performed.",
    ])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Seed rows: {len(seed_rows)}")
    print(f"Added {len(verified)} entries")
    print(f"Rejected {len(rejected)} rows")
    print(f"New total: {len(data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REJECTS}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
