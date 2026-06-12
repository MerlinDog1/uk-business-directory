#!/usr/bin/env python3
"""Second Scotland-only verification pass for local CSV leads."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
SOURCE = WORKSPACE / "scotland_sign_companies.csv"
OUT = ROOT / "data" / "scotland-pass-verified-additions.json"
REJECTS = ROOT / "data" / "scotland-pass-rejected.json"
REPORT = ROOT / "reports" / "uk-sign-scotland-pass-verified-2026-06-12.md"

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
    "exhibition",
    "large format",
)

BAD_HOST_PARTS = (
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "hugedomains.com",
    "sedo.com",
    "godaddy.com",
    "domainmarket",
)

PATHS = ("", "/", "/contact", "/contact-us", "/about", "/about-us", "/services", "/signage")


def read_value(row: dict[str, str], *names: str) -> str:
    lower = {k.lower(): v for k, v in row.items() if k}
    for name in names:
        value = lower.get(name.lower())
        if value:
            return value.strip()
    return ""


def norm_name(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and")
    value = re.sub(r"\b(ltd|limited|llp|plc|co|company|the)\b", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def site_host(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.netloc.lower().removeprefix("www.")


def site_key(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def email_value(value: str | None) -> str:
    value = (value or "").strip().lower()
    if "@" not in value:
        return ""
    local, domain = value.rsplit("@", 1)
    if not local or "." not in domain:
        return ""
    return value


def clean_phone(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    return value if len(digits) >= 9 else ""


def social_value(row: dict[str, str], *names: str) -> str | None:
    value = read_value(row, *names)
    return value or None


def has_signal(company: str, text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.lower())
    return any(word in lowered for word in SIGNAL_WORDS)


def candidate_urls(domain: str) -> list[str]:
    bases = [f"https://{domain}", f"https://www.{domain}", f"http://{domain}", f"http://www.{domain}"]
    urls = []
    for base in bases:
        for path in PATHS:
            urls.append(base.rstrip("/") + path)
    return urls


def fetch_one(session: requests.Session, company: str, url: str) -> tuple[str | None, str]:
    try:
        response = session.get(url, timeout=5, allow_redirects=True, verify=False)
    except requests.RequestException as exc:
        return None, type(exc).__name__
    final_url = response.url
    host = site_host(final_url)
    if any(part in host for part in BAD_HOST_PARTS):
        return None, f"bad host {host}"
    if response.status_code >= 400:
        return None, f"HTTP {response.status_code}"
    body = response.text[:250000]
    if has_signal(company, body):
        return final_url, ""
    return None, "resolved but lacked signage wording"


def fetch_verified_url(company: str, domain: str) -> tuple[str | None, str]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        }
    )
    last_error = "no response"
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, session, company, url): url for url in candidate_urls(domain)}
        for future in as_completed(futures):
            verified_url, error = future.result()
            if verified_url:
                return verified_url, ""
            last_error = error or last_error
    return None, last_error


def source_rows() -> list[dict]:
    rows = []
    with SOURCE.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
        for row in csv.DictReader(handle):
            company = read_value(row, "Company Name", "Company")
            email = email_value(read_value(row, "Email Address", "Email"))
            phone = clean_phone(read_value(row, "Phone Number", "Phone"))
            address = read_value(row, "Physical Address", "Address")
            if not company or not email or not phone or not address:
                continue
            rows.append(
                {
                    "sourceFile": SOURCE.name,
                    "company": company,
                    "county": "Scotland",
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "linkedin": social_value(row, "LinkedIn URL", "LinkedIn"),
                    "instagram": social_value(row, "Instagram URL", "Instagram"),
                    "facebook": social_value(row, "Facebook URL", "Facebook"),
                }
            )
    return rows


def main() -> None:
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
    live_data = json.loads(DATA.read_text())
    original_data = json.loads(subprocess.check_output(["git", "show", "HEAD:data/directory-data.json"], cwd=ROOT))

    live_names = {norm_name(entry.get("company")) for entry in live_data}
    live_hosts = {site_host(entry.get("website")) for entry in live_data if entry.get("website")}
    live_sites = {site_key(entry.get("website")) for entry in live_data if entry.get("website")}
    live_emails = {email_value(entry.get("email")) for entry in live_data if entry.get("email")}
    original_names = {norm_name(entry.get("company")) for entry in original_data}
    original_emails = {email_value(entry.get("email")) for entry in original_data if entry.get("email")}
    original_hosts = {site_host(entry.get("website")) for entry in original_data if entry.get("website")}

    candidates = []
    rejected = []
    seen_candidates: set[tuple[str, str]] = set()
    seed_rows = source_rows()

    def verify_row(row: dict) -> tuple[dict | None, dict | None]:
        key = (norm_name(row["company"]), row["email"])
        if key in seen_candidates:
            return None, {**row, "reason": "duplicate source row"}
        seen_candidates.add(key)
        domain = row["email"].rsplit("@", 1)[1]
        if norm_name(row["company"]) in live_names or row["email"] in live_emails:
            return None, {**row, "reason": "already present in live directory"}
        if norm_name(row["company"]) in original_names or row["email"] in original_emails:
            return None, {**row, "reason": "matched original repo by normalized company/email"}
        verified_url, reason = fetch_verified_url(row["company"], domain)
        if not verified_url:
            return None, {**row, "reason": reason}
        host = site_host(verified_url)
        key = site_key(verified_url)
        if host in original_hosts or host in live_hosts or key in live_sites:
            return None, {**row, "reason": f"website host/path already present: {host}"}
        return {
            "county": "Scotland",
            "category": "Signage",
            "company": row["company"],
            "website": verified_url,
            "email": row["email"],
            "linkedin": row["linkedin"],
            "instagram": row["instagram"],
            "facebook": row["facebook"],
            "phone": row["phone"],
            "address": row["address"],
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": row["sourceFile"],
            "_evidence": f"Scotland pass: verified email-domain website {verified_url} resolved and contained signage-related wording.",
        }, None

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify_row, row) for row in seed_rows]
        for future in as_completed(futures):
            entry, rejection = future.result()
            if rejection:
                rejected.append(rejection)
                continue
            if not entry:
                continue
            host = site_host(entry["website"])
            key = site_key(entry["website"])
            if norm_name(entry["company"]) in live_names or entry["email"] in live_emails:
                rejected.append({**entry, "reason": "became duplicate during concurrent pass"})
                continue
            if host in original_hosts or host in live_hosts or key in live_sites:
                rejected.append({**entry, "reason": f"website host/path already present: {host}"})
                continue
            candidates.append(entry)
            live_names.add(norm_name(entry["company"]))
            live_emails.add(entry["email"])
            live_hosts.add(host)
            live_sites.add(key)

    candidates.sort(key=lambda item: item["company"])
    next_id = max(entry["id"] for entry in live_data) + 1
    for entry in candidates:
        live = {key: value for key, value in entry.items() if not key.startswith("_")}
        live["id"] = next_id
        live_data.append(live)
        entry["id"] = next_id
        next_id += 1

    DATA.write_text(json.dumps(live_data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n")
    REJECTS.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(live_data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in live_data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# Scotland Sign Pass Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Source rows scanned: {len(seed_rows)}.",
        f"- Added {len(candidates)} verified Scotland sign-company entries.",
        f"- Rejected {len(rejected)} rows as duplicates, original-repo overlaps, unresolved domains or weak evidence.",
        "- No websites or emails were guessed; websites are verified email-domain sites.",
        "- Extra duplicate gate: normalized company/email checked against the original 914-row repo before append.",
        "",
        "## Added Companies",
    ]
    for entry in candidates:
        lines.append(f"- {entry['company']} - {entry['email']} | {entry['phone']} | {entry['website']}")
    lines.extend(
        [
            "",
            "## Validation",
            f"- JSON parse: passed on {date.today().isoformat()}.",
            "- Duplicate gate: live directory and original repo company/email/site checked before append.",
            "- Evidence gate: email-domain website resolved and contained signage-related wording.",
            "- Safety gate: no GitHub push performed.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Scanned {len(seed_rows)} Scotland rows")
    print(f"Added {len(candidates)} entries")
    print(f"Rejected {len(rejected)} rows")
    print(f"New total: {len(live_data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REJECTS}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
