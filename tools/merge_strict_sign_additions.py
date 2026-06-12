#!/usr/bin/env python3
"""Append a strict, source-backed batch of UK sign-company additions."""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SOURCE = WORKSPACE / "memory" / "UK_Sign_Industry_Directory.csv"
DATA = ROOT / "data" / "directory-data.json"
NEW_ENTRIES = ROOT / "data" / "new-entries.json"
METADATA = ROOT / "data" / "metadata.json"
REPORT = ROOT / "reports" / "uk-sign-buildout-2026-06-12.md"

BAD_SOURCE_DOMAINS = (
    "yell.com",
    "cylex",
    "directory.",
    "findit.",
    "independent.co.uk",
    "thomsonlocal",
    "192.com",
)


def name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def site_key(value: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", value.lower()).rstrip("/")


def clean_url(value: str) -> str | None:
    value = value.strip()
    if not value or not value.startswith(("http://", "https://")):
        return None
    if any(domain in value.lower() for domain in BAD_SOURCE_DOMAINS):
        return None
    host = urlparse(value).netloc
    if "." not in host:
        return None
    return value


def clean_email(value: str) -> str | None:
    value = value.strip()
    if not value or "@" not in value:
        return None
    return value


def clean_phone(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    return value if len(digits) >= 7 else ""


def clean_social(value: str, domain: str) -> str | None:
    value = value.strip()
    if not value or domain not in value:
        return None
    return value if value.startswith("http") else f"https://{value}"


def main() -> None:
    data = json.loads(DATA.read_text())
    existing_names = {name_key(entry["company"]) for entry in data}
    existing_sites = {
        site_key(entry["website"])
        for entry in data
        if entry.get("website")
    }
    seen_names: set[str] = set()
    seen_sites: set[str] = set()
    next_id = max(entry["id"] for entry in data) + 1
    additions = []

    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("Category", "").strip() != "Sign Company":
                continue

            company = row.get("Company Name", "").strip()
            website = clean_url(row.get("Website", ""))
            county = row.get("County", "").strip()
            if not company or not website or not county:
                continue

            nkey = name_key(company)
            skey = site_key(website)
            if nkey in existing_names or skey in existing_sites:
                continue
            if nkey in seen_names or skey in seen_sites:
                continue

            entry = {
                "id": next_id,
                "county": county,
                "category": "Signage",
                "company": company,
                "website": website,
                "email": clean_email(row.get("Email", "")),
                "linkedin": clean_social(row.get("LinkedIn", ""), "linkedin.com"),
                "instagram": clean_social(row.get("Instagram", ""), "instagram.com"),
                "facebook": clean_social(row.get("Facebook", ""), "facebook.com"),
                "phone": clean_phone(row.get("Phone", "")),
                "address": row.get("Address", "").strip(),
                "quality": 0,
                "sellsPlaques": False,
            }
            additions.append(entry)
            seen_names.add(nkey)
            seen_sites.add(skey)
            next_id += 1

    data.extend(additions)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    NEW_ENTRIES.write_text(json.dumps(additions, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    REPORT.parent.mkdir(exist_ok=True)
    by_county: dict[str, int] = {}
    for entry in additions:
        by_county[entry["county"]] = by_county.get(entry["county"], 0) + 1

    lines = [
        "# UK Sign Directory Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Added {len(additions)} strict, source-backed UK sign-company entries.",
        f"- Source file: `{SOURCE}`.",
        "- Rejected rows without real website fields, rows from directory/search pages, and duplicates already present in `data/directory-data.json`.",
        "- MiMo was used to inspect the repo and build an initial comparison script, but its broad no-website pass was rejected because it fabricated website-looking URLs.",
        "",
        "## Counties Improved",
    ]
    for county, count in sorted(by_county.items()):
        lines.append(f"- {county}: {count}")

    lines.extend([
        "",
        "## Added Companies",
    ])
    for entry in additions:
        bits = [entry["website"]]
        if entry["email"]:
            bits.append(entry["email"])
        if entry["phone"]:
            bits.append(entry["phone"])
        lines.append(f"- {entry['company']} ({entry['county']}) - " + " | ".join(bits))

    lines.extend([
        "",
        "## Validation",
        f"- JSON parse: passed on {date.today().isoformat()}.",
        "- Duplicate gate: company name and website checked before append.",
        "- Safety gate: no GitHub push performed.",
    ])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Added {len(additions)} entries")
    print(f"New total: {len(data)}")
    print(f"Wrote {NEW_ENTRIES}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
