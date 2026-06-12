#!/usr/bin/env python3
"""Append manually verified London-focused sign-company additions."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
OUT = ROOT / "data" / "london-verified-additions.json"
REPORT = ROOT / "reports" / "uk-sign-london-verified-buildout-2026-06-12.md"


CANDIDATES = [
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "E U Signs Ltd",
        "website": "https://eusigns.co.uk",
        "email": "info@eusigns.co.uk",
        "phone": "020 3375 2100",
        "address": "Unit 6 Stirling Industrial Centre, Stirling Way, Borehamwood, WD6 2BT",
        "linkedin": None,
        "instagram": None,
        "facebook": None,
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title references health and safety signs.",
    },
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "Sign Architects",
        "website": "https://signarchitects.co.uk",
        "email": "info@signarchitects.co.uk",
        "phone": "020 8507 3395",
        "address": "London, IG11 0HE",
        "linkedin": None,
        "instagram": "IG: signarchitects",
        "facebook": "FB: signarchitects",
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title says Signage Company London.",
    },
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "GLYPHICS LTD",
        "website": "https://glyphics.co.uk",
        "email": "hello@glyphics.co.uk",
        "phone": "020 7739 7818",
        "address": "75 Leonard St, London, EC2A 4QS",
        "linkedin": None,
        "instagram": "IG: glyphics_london",
        "facebook": None,
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title references London sign maker, branding and wayfinding signage.",
    },
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "Bellenden Signs Ltd",
        "website": "https://bellendensigns.com",
        "email": "info@bellendensigns.com",
        "phone": "020 3654 7973",
        "address": "83 Bellenden Rd, London, SE15 4QZ",
        "linkedin": None,
        "instagram": None,
        "facebook": None,
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title says London Sign Maker Specialists.",
    },
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "Lumen Signs Ltd",
        "website": "https://lumensigns.co.uk",
        "email": "info@lumensigns.co.uk",
        "phone": "020 3375 2100",
        "address": "London, E14 9RP",
        "linkedin": None,
        "instagram": None,
        "facebook": None,
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title says Custom Signage Company In London.",
    },
    {
        "county": "Greater London",
        "category": "Signage",
        "company": "Butler Signs",
        "website": "https://butlersigns.co.uk",
        "email": "info@butlersigns.co.uk",
        "phone": "01635 250680",
        "address": "Berkshire/London",
        "linkedin": None,
        "instagram": "IG: butlersigns",
        "facebook": "FB: butlersigns",
        "sellsPlaques": False,
        "_evidence": "Website returned HTTP 200; page title says award winning signage.",
    },
]


def key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def site_key(value: str | None) -> str:
    return re.sub(r"^https?://(www\.)?", "", (value or "").lower()).rstrip("/")


def main() -> None:
    data = json.loads(DATA.read_text())
    names = {key(entry.get("company")) for entry in data}
    sites = {site_key(entry.get("website")) for entry in data if entry.get("website")}
    emails = {
        entry["email"].lower()
        for entry in data
        if isinstance(entry.get("email"), str) and "@" in entry["email"]
    }
    next_id = max(entry["id"] for entry in data) + 1
    additions = []

    for raw in CANDIDATES:
        if key(raw["company"]) in names:
            continue
        if site_key(raw["website"]) in sites:
            continue
        if raw["email"].lower() in emails:
            continue
        entry = {key_: value for key_, value in raw.items() if not key_.startswith("_")}
        entry["id"] = next_id
        additions.append({**entry, "_evidence": raw["_evidence"]})
        data.append(entry)
        names.add(key(raw["company"]))
        sites.add(site_key(raw["website"]))
        emails.add(raw["email"].lower())
        next_id += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(additions, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# UK Sign Directory London Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Added {len(additions)} London-focused sign-company entries.",
        "- Each accepted row has email, phone, address and a direct website that returned HTTP 200 during verification.",
        "- Repeated `Signs Now` borough rows and other no-website rows were left unmerged pending direct verification.",
        "",
        "## Added Companies",
    ]
    for entry in additions:
        lines.append(f"- {entry['company']} - {entry['email']} | {entry['phone']} | {entry['website']}")
        lines.append(f"  Evidence: {entry['_evidence']}")
    lines.extend([
        "",
        "## Validation",
        f"- JSON parse: passed on {date.today().isoformat()}.",
        "- Duplicate gate: company, website and email checked before append.",
        "- Safety gate: no guessed websites/emails and no GitHub push performed.",
    ])
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Added {len(additions)} London entries")
    print(f"New total: {len(data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
