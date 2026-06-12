#!/usr/bin/env python3
"""Append verified Isle of Man sign/signage entries."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "directory-data.json"
METADATA = ROOT / "data" / "metadata.json"
OUT = ROOT / "data" / "isle-of-man-verified-additions.json"
REJECTS = ROOT / "data" / "isle-of-man-rejected.json"
REPORT = ROOT / "reports" / "uk-sign-isle-of-man-verified-2026-06-12.md"


def norm_name(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and")
    value = re.sub(r"\b(ltd|limited|llp|plc|co|company|the)\b", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def host(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.netloc.lower().removeprefix("www.")


def email(value: str | None) -> str:
    return (value or "").strip().lower()


def main() -> None:
    data = json.loads(DATA.read_text())
    original = json.loads(subprocess.check_output(["git", "show", "HEAD:data/directory-data.json"], cwd=ROOT))

    existing_names = {norm_name(entry.get("company")) for entry in data}
    existing_hosts = {host(entry.get("website")) for entry in data if entry.get("website")}
    existing_emails = {email(entry.get("email")) for entry in data if entry.get("email")}
    original_names = {norm_name(entry.get("company")) for entry in original}
    original_hosts = {host(entry.get("website")) for entry in original if entry.get("website")}
    original_emails = {email(entry.get("email")) for entry in original if entry.get("email")}

    candidates = [
        {
            "county": "Isle of Man",
            "category": "Signage",
            "company": "Signrite Isle of Man Ltd",
            "website": "https://www.signrite-iom.com/contact.html",
            "email": "sales@signrite-iom.com",
            "linkedin": None,
            "instagram": None,
            "facebook": None,
            "phone": "+44 (0) 1624 612244",
            "address": "Unit 2, Isle of Man Business Park, Cooil Road, Braddan, Isle of Man, IM2 2QY",
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": "web:signrite-iom.com/contact.html",
            "_evidence": "Direct contact page lists exterior signage, interior signage, window graphics, address, phone and sales@signrite-iom.com.",
        },
        {
            "county": "Isle of Man",
            "category": "Signage",
            "company": "The Copyshop",
            "website": "https://www.thecopyshop.im/signage-displays/",
            "email": "enquiries@thecopyshop.im",
            "linkedin": None,
            "instagram": None,
            "facebook": None,
            "phone": "01624 622697",
            "address": "Unit B1, Eden Business Park, Braddan, Isle of Man, IM4 2AY",
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": "web:thecopyshop.im/signage-displays/",
            "_evidence": "Direct signage/displays page lists shop signage, vehicle graphics, displays, address, phone and enquiries@thecopyshop.im.",
        },
        {
            "county": "Isle of Man",
            "category": "Signage",
            "company": "Gellings Isle of Man",
            "website": "https://www.gellings.im/prod_cat/C_signs--display-_303.asp",
            "email": "info@gellings.im",
            "linkedin": None,
            "instagram": None,
            "facebook": None,
            "phone": "01624 671200",
            "address": "Unit 4 Kirby Farm Industrial Estate, Vicarage Road, Braddan, Isle of Man, IM4 4LA",
            "quality": 0,
            "sellsPlaques": False,
            "_sourceFile": "web:gellings.im/prod_cat/C_signs--display-_303.asp",
            "_evidence": "Direct signs/display page lists signs and display products, address, phone and info@gellings.im.",
        },
    ]

    weak = [
        {
            "company": "Edwin Dennis Signs",
            "reason": "Direct site returned 502 and no email was found; kept out pending stronger evidence.",
            "website": "https://www.edwindennis.com/",
        },
        {
            "company": "Isle of Wraps",
            "reason": "Site connection failed and no direct email was found; kept out pending stronger evidence.",
            "website": "https://isleofwraps.co.uk/",
        },
        {
            "company": "Sign Sense Ltd",
            "reason": "Third-party listing only; no direct website/email evidence found.",
            "website": None,
        },
        {
            "company": "Ballasalla Signs",
            "reason": "Third-party listing only; no direct website/email evidence found.",
            "website": None,
        },
    ]

    accepted = []
    rejected = []
    for entry in candidates:
        checks = []
        name_key = norm_name(entry["company"])
        host_key = host(entry["website"])
        email_key = email(entry["email"])
        if name_key in existing_names or name_key in original_names:
            checks.append("company duplicate")
        if host_key in existing_hosts or host_key in original_hosts:
            checks.append("website duplicate")
        if email_key in existing_emails or email_key in original_emails:
            checks.append("email duplicate")
        if checks:
            rejected.append({**entry, "reason": ", ".join(checks)})
            continue
        accepted.append(entry)
        existing_names.add(name_key)
        existing_hosts.add(host_key)
        existing_emails.add(email_key)

    next_id = max(entry["id"] for entry in data) + 1
    for entry in accepted:
        live = {key: value for key, value in entry.items() if not key.startswith("_")}
        live["id"] = next_id
        data.append(live)
        entry["id"] = next_id
        next_id += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    OUT.write_text(json.dumps(accepted, indent=2, ensure_ascii=False) + "\n")
    REJECTS.write_text(json.dumps(rejected + weak, indent=2, ensure_ascii=False) + "\n")

    metadata = json.loads(METADATA.read_text())
    metadata["count"] = len(data)
    metadata["counties"] = sorted({entry.get("county", "") for entry in data if entry.get("county")})
    METADATA.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")

    REPORT.parent.mkdir(exist_ok=True)
    lines = [
        "# Isle of Man Sign Pass Verified Buildout - 2026-06-12",
        "",
        "## Summary",
        f"- Added {len(accepted)} verified Isle of Man sign/signage entries.",
        f"- Rejected/held {len(rejected) + len(weak)} weak or duplicate candidates.",
        "- No websites or emails were guessed.",
        "- Duplicate gate: current live directory and original 914-row repo checked by normalized company, website host and email.",
        "",
        "## Added Companies",
    ]
    for entry in accepted:
        lines.append(f"- {entry['company']} - {entry['email']} | {entry['phone']} | {entry['website']}")
    lines.extend(["", "## Held Back"])
    for entry in rejected + weak:
        lines.append(f"- {entry['company']} - {entry['reason']}")
    lines.extend(
        [
            "",
            "## Validation",
            f"- JSON parse: passed on {date.today().isoformat()}.",
            "- Safety gate: no GitHub push performed.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")

    print(f"Added {len(accepted)} entries")
    print(f"Rejected/held {len(rejected) + len(weak)} rows")
    print(f"New total: {len(data)}")
    print(f"Wrote {OUT}")
    print(f"Wrote {REJECTS}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
