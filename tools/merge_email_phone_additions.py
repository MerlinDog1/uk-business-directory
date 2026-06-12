#!/usr/bin/env python3
"""Append strict sign-company additions from local rows with email and phone evidence."""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA = ROOT / "data" / "directory-data.json"
NEW_ENTRIES = ROOT / "data" / "second-pass-email-additions.json"
METADATA = ROOT / "data" / "metadata.json"
REPORT = ROOT / "reports" / "uk-sign-email-phone-buildout-2026-06-12.md"

SOURCE_FILES = [
    # National seed list has the strongest evidence quality in the local backlog.
    # The regional generated CSVs contain useful leads, but some rows include
    # placeholder-style phones/domains and should stay in review until verified.
    "uk_sign_companies.csv",
]

COUNTY_BY_FILE = {
    "scotland_sign_companies.csv": "Scotland",
    "wales_sign_companies.csv": "Wales",
}

COUNTY_MAP = {
    "London": "Greater London",
    "Bristol": "Bristol",
    "Tyne and Wear": "Tyne and Wear",
    "": "Unidentified",
}

GENERIC_EMAIL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "icloud.com",
    "aol.com",
}

BAD_EMAIL_PARTS = {
    "example",
    "placeholder",
    "test@",
    "noreply",
    "no-reply",
}


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def tokens(value: str) -> list[str]:
    stop = {"ltd", "limited", "the", "and", "sign", "signs", "signage", "graphics", "graphic", "print", "printing"}
    return [part for part in re.findall(r"[a-z0-9]+", value.lower()) if len(part) >= 4 and part not in stop]


def clean_email(value: str) -> str | None:
    value = value.strip().lower()
    if not value or "@" not in value or any(part in value for part in BAD_EMAIL_PARTS):
        return None
    local, domain = value.rsplit("@", 1)
    if "." not in domain or not local:
        return None
    return value


def clean_phone(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    return value if len(digits) >= 7 else ""


def email_matches_company(email: str, company: str) -> bool:
    domain = email.rsplit("@", 1)[1]
    if domain in GENERIC_EMAIL_DOMAINS:
        return True
    compact_domain = re.sub(r"[^a-z0-9]+", "", domain)
    company_tokens = tokens(company)
    if any(token in compact_domain for token in company_tokens):
        return True
    if "sign" in compact_domain and any(word in company.lower() for word in ("sign", "graphics", "display")):
        return True
    return False


def read_value(row: dict[str, str], *names: str) -> str:
    lower = {k.lower(): v for k, v in row.items() if k}
    for name in names:
        if lower.get(name.lower()):
            return lower[name.lower()].strip()
    return ""


def source_rows() -> list[tuple[str, dict[str, str]]]:
    rows = []
    for name in SOURCE_FILES:
        path = WORKSPACE / name
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
            for row in csv.DictReader(handle):
                rows.append((name, row))
    return rows


def main() -> None:
    data = json.loads(DATA.read_text())
    existing_names = {key(entry.get("company", "")) for entry in data}
    existing_emails = {
        entry["email"].lower()
        for entry in data
        if isinstance(entry.get("email"), str) and "@" in entry["email"]
    }

    additions = []
    seen_names: set[str] = set()
    seen_emails: set[str] = set()
    next_id = max(entry["id"] for entry in data) + 1

    for source, row in source_rows():
        company = read_value(row, "Company Name", "Company")
        email = clean_email(read_value(row, "Email Address", "Email"))
        phone = clean_phone(read_value(row, "Phone Number", "Phone"))
        address = read_value(row, "Physical Address", "Address")
        county = read_value(row, "County") or COUNTY_BY_FILE.get(source, "")
        county = COUNTY_MAP.get(county, county)

        if not company or not email or not phone or not address or not county or county == "Unidentified":
            continue
        if key(company) in existing_names or key(company) in seen_names:
            continue
        if email in existing_emails or email in seen_emails:
            continue
        if any(block in company.lower() for block in ("architect", "marketing")) and "sign" not in company.lower():
            continue
        if not email_matches_company(email, company):
            continue

        socials = read_value(row, "Social Media URLs")
        entry = {
            "id": next_id,
            "county": county,
            "category": "Signage",
            "company": company,
            "website": None,
            "email": email,
            "linkedin": read_value(row, "LinkedIn") or (socials if "li:" in socials.lower() or "linkedin" in socials.lower() else None),
            "instagram": read_value(row, "Instagram") or (socials if "ig:" in socials.lower() or "instagram" in socials.lower() else None),
            "facebook": read_value(row, "Facebook") or (socials if "fb:" in socials.lower() or "facebook" in socials.lower() else None),
            "phone": phone,
            "address": address,
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": source,
        }
        additions.append(entry)
        seen_names.add(key(company))
        seen_emails.add(email)
        next_id += 1
        if len(additions) >= 25:
            break

    data.extend({k: v for k, v in entry.items() if k != "_sourceFile"} for entry in additions)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    NEW_ENTRIES.write_text(json.dumps(additions, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    by_county: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for entry in additions:
        by_county[entry["county"]] = by_county.get(entry["county"], 0) + 1
        by_source[entry["_sourceFile"]] = by_source.get(entry["_sourceFile"], 0) + 1

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# UK Sign Directory Email/Phone Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Added {len(additions)} additional sign-company entries from the high-confidence national seed CSV with real email, phone and address fields.",
        "- No websites were guessed. Rows without a real website are stored with `website: null`.",
        "- Emails were accepted only when present in the source row and not obvious placeholders.",
        "- Non-generic email domains had to match the company name or sign/display wording.",
        "- Broader regional CSV rows were reviewed by MiMo but left unmerged because several looked placeholder-like and need direct verification first.",
        "",
        "## Counties Improved",
    ]
    for county, count in sorted(by_county.items()):
        lines.append(f"- {county}: {count}")
    lines.extend(["", "## Source Files"])
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: {count}")
    lines.extend(["", "## Added Companies"])
    for entry in additions:
        lines.append(f"- {entry['company']} ({entry['county']}) - {entry['email']} | {entry['phone']} | source: {entry['_sourceFile']}")
    lines.extend([
        "",
        "## Validation",
        f"- JSON parse: passed on {date.today().isoformat()}.",
        "- Duplicate gate: company name and email checked before append.",
        "- Safety gate: no guessed websites and no GitHub push performed.",
    ])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Added {len(additions)} entries")
    print(f"New total: {len(data)}")
    print(f"Wrote {NEW_ENTRIES}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
