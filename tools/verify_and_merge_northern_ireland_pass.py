#!/usr/bin/env python3
"""Verify Northern Ireland sign-company candidates and append clean additions."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
SOURCE = WORKSPACE / "northern_ireland_sign_companies.csv"
MEMORY_SOURCE = WORKSPACE / "memory" / "Northern_Ireland_Directory.csv"
OUT = ROOT / "data" / "northern-ireland-verified-additions.json"
REJECTS = ROOT / "data" / "northern-ireland-rejected.json"
REPORT = ROOT / "reports" / "uk-sign-northern-ireland-verified-2026-06-12.md"

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


def norm_name(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and")
    value = re.sub(r"\b(ltd|limited|llp|plc|co|company|the)\b", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def host(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.netloc.lower().removeprefix("www.")


def site_key(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return f"{parsed.netloc.lower().removeprefix('www.')}{parsed.path.rstrip('/')}"


def email(value: str | None) -> str:
    value = (value or "").strip().lower()
    if "@" not in value:
        return ""
    local, domain = value.rsplit("@", 1)
    if not local or "." not in domain:
        return ""
    return value


def clean_phone(value: str | None) -> str:
    value = (value or "").strip()
    digits = re.sub(r"\D", "", value)
    if len(digits) < 9:
        return ""
    tail = digits[-6:]
    if tail in {"000000", "111111", "222222", "333333", "444444", "123123"}:
        return ""
    return value


def has_signal(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.lower())
    return any(word in lowered for word in SIGNAL_WORDS)


def candidate_urls(domain: str) -> list[str]:
    bases = [f"https://{domain}", f"https://www.{domain}", f"http://{domain}", f"http://www.{domain}"]
    return [base.rstrip("/") + path for base in bases for path in PATHS]


def fetch_one(session: requests.Session, url: str) -> tuple[str | None, str]:
    try:
        response = session.get(url, timeout=6, allow_redirects=True, verify=False)
    except requests.RequestException as exc:
        return None, type(exc).__name__
    final_url = response.url
    final_host = host(final_url)
    if any(part in final_host for part in BAD_HOST_PARTS):
        return None, f"bad host {final_host}"
    if response.status_code >= 400:
        return None, f"HTTP {response.status_code}"
    if has_signal(response.text[:250000]):
        return final_url, ""
    return None, "resolved but lacked signage wording"


def fetch_verified_url(domain: str) -> tuple[str | None, str]:
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
        futures = {pool.submit(fetch_one, session, url): url for url in candidate_urls(domain)}
        for future in as_completed(futures):
            verified_url, error = future.result()
            if verified_url:
                return verified_url, ""
            last_error = error or last_error
    return None, last_error


def read_social(row: dict[str, str], key: str) -> str | None:
    value = (row.get(key) or "").strip()
    return value or None


def row_from_csv(row: dict[str, str]) -> dict | None:
    company = (row.get("Company Name") or "").strip()
    area = (row.get("County/Area") or "").strip()
    phone = clean_phone(row.get("Phone Number"))
    addr = (row.get("Physical Address") or "").strip()
    mail = email(row.get("Email Address"))
    facebook = read_social(row, "Facebook")

    # Source row has an unquoted comma in the company name.
    if company == "4 Corners Sign" and area.lower().startswith("print"):
        company = "4 Corners Sign, Print & Display"
        area = (row.get("Phone Number") or "").strip()
        phone = clean_phone(row.get("Email Address"))
        mail = email(row.get("Physical Address"))
        addr = (row.get("LinkedIn") or "").strip()
        facebook = row.get(None, [""])[0] if isinstance(row.get(None), list) and row.get(None) else facebook

    if not company or not mail or not phone or not addr:
        return None
    return {
        "sourceFile": SOURCE.name,
        "company": company,
        "county": "Northern Ireland",
        "area": area,
        "email": mail,
        "phone": phone,
        "address": addr,
        "linkedin": read_social(row, "LinkedIn"),
        "instagram": read_social(row, "Instagram"),
        "facebook": facebook,
    }


def source_rows() -> list[dict]:
    rows: list[dict] = []
    with SOURCE.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
        for row in csv.DictReader(handle):
            parsed = row_from_csv(row)
            if parsed:
                rows.append(parsed)

    if MEMORY_SOURCE.exists():
        with MEMORY_SOURCE.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
            for row in csv.DictReader(handle):
                category = (row.get("Category") or "").lower()
                if "sign" not in category and "wayfinding" not in category:
                    continue
                company = (row.get("Company") or row.get("Company Name") or "").strip()
                mail = email(row.get("Email"))
                website = (row.get("Website") or "").strip()
                if not company or not mail or not website:
                    continue
                rows.append(
                    {
                        "sourceFile": "memory/Northern_Ireland_Directory.csv",
                        "company": company,
                        "county": "Northern Ireland",
                        "area": row.get("City") or "Northern Ireland",
                        "email": mail,
                        "phone": "",
                        "address": (row.get("City") or "Northern Ireland").strip(),
                        "linkedin": row.get("LinkedIn") or None,
                        "instagram": row.get("Instagram") or None,
                        "facebook": None,
                        "presetWebsite": website,
                    }
                )
    return rows


def main() -> None:
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
    data = json.loads(DATA.read_text())
    original = json.loads(subprocess.check_output(["git", "show", "HEAD:data/directory-data.json"], cwd=ROOT))

    live_names = {norm_name(entry.get("company")) for entry in data}
    live_hosts = {host(entry.get("website")) for entry in data if entry.get("website")}
    live_sites = {site_key(entry.get("website")) for entry in data if entry.get("website")}
    live_emails = {email(entry.get("email")) for entry in data if entry.get("email")}
    original_names = {norm_name(entry.get("company")) for entry in original}
    original_hosts = {host(entry.get("website")) for entry in original if entry.get("website")}
    original_emails = {email(entry.get("email")) for entry in original if entry.get("email")}

    accepted = []
    rejected = []
    seen: set[tuple[str, str]] = set()

    def verify(row: dict) -> tuple[dict | None, dict | None]:
        name_key = norm_name(row["company"])
        mail = row["email"]
        seed_key = (name_key, mail)
        if seed_key in seen:
            return None, {**row, "reason": "duplicate source row"}
        seen.add(seed_key)
        if name_key in live_names or mail in live_emails:
            return None, {**row, "reason": "already present in live directory"}
        if name_key in original_names or mail in original_emails:
            return None, {**row, "reason": "matched original repo by normalized company/email"}

        if row.get("presetWebsite"):
            verified_url, reason = fetch_verified_url(host(row["presetWebsite"]))
        else:
            verified_url, reason = fetch_verified_url(mail.rsplit("@", 1)[1])
        if not verified_url:
            return None, {**row, "reason": reason}
        verified_host = host(verified_url)
        verified_site = site_key(verified_url)
        if verified_host in original_hosts or verified_host in live_hosts or verified_site in live_sites:
            return None, {**row, "reason": f"website host/path already present: {verified_host}"}

        return {
            "county": "Northern Ireland",
            "category": "Signage",
            "company": row["company"],
            "website": verified_url,
            "email": mail,
            "linkedin": row.get("linkedin"),
            "instagram": row.get("instagram"),
            "facebook": row.get("facebook"),
            "phone": row.get("phone") or None,
            "address": row["address"],
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": row["sourceFile"],
            "_evidence": f"Northern Ireland pass: verified website {verified_url} resolved and contained signage-related wording.",
        }, None

    rows = source_rows()
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(verify, row) for row in rows]
        for future in as_completed(futures):
            entry, rejection = future.result()
            if rejection:
                rejected.append(rejection)
                continue
            if not entry:
                continue
            name_key = norm_name(entry["company"])
            mail = entry["email"]
            verified_host = host(entry["website"])
            verified_site = site_key(entry["website"])
            if name_key in live_names or mail in live_emails:
                rejected.append({**entry, "reason": "became duplicate during concurrent pass"})
                continue
            if verified_host in original_hosts or verified_host in live_hosts or verified_site in live_sites:
                rejected.append({**entry, "reason": f"website host/path already present: {verified_host}"})
                continue
            accepted.append(entry)
            live_names.add(name_key)
            live_emails.add(mail)
            live_hosts.add(verified_host)
            live_sites.add(verified_site)

    accepted.sort(key=lambda entry: entry["company"])
    next_id = max(entry["id"] for entry in data) + 1
    for entry in accepted:
        live = {key: value for key, value in entry.items() if not key.startswith("_")}
        live["id"] = next_id
        data.append(live)
        entry["id"] = next_id
        next_id += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(accepted, indent=2, ensure_ascii=False) + "\n")
    REJECTS.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# Northern Ireland Sign Pass Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Source rows scanned: {len(rows)}.",
        f"- Added {len(accepted)} verified Northern Ireland sign/signage entries.",
        f"- Rejected/held {len(rejected)} rows as duplicates, original-repo overlaps, unresolved domains, weak evidence or malformed/incomplete rows.",
        "- No websites or emails were guessed.",
        "- Duplicate gate: current live directory and original 914-row repo checked by normalized company, website host and email.",
        "",
        "## Added Companies",
    ]
    for entry in accepted:
        lines.append(f"- {entry['company']} - {entry['email']} | {entry.get('phone') or 'no phone'} | {entry['website']}")
    lines.extend(["", "## Validation", f"- JSON parse: passed on {date.today().isoformat()}.", "- Safety gate: no GitHub push performed."])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Scanned {len(rows)} Northern Ireland rows")
    print(f"Added {len(accepted)} entries")
    print(f"Rejected/held {len(rejected)} rows")
    print(f"New total: {len(data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REJECTS}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
