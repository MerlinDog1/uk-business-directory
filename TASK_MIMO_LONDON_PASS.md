# MiMo Task: London-Focused Sign Directory Pass

## Goal
Find additional Greater London / London sign-industry companies for the UK business directory.

## Hard Rules
- Candidate-only first. Do not edit `data/directory-data.json` or `data/metadata.json`.
- Do not guess websites.
- Do not guess emails.
- Avoid duplicates already in:
  - `data/directory-data.json`
  - `data/new-entries.json`
  - `data/second-pass-email-additions.json`
- Treat generated-looking regional CSV rows skeptically. Prefer rows with email + phone + address and direct London relevance.
- If website is not present in source data, keep `website: null`.
- If using the web, use direct company websites/contact pages only; no Yell/Cylex/192/directory pages.
- If MiMo `task` or `actor` tools throw schema errors, continue with read/bash/write/edit tools only.

## Primary Sources
Focus on:

- `/home/clawd_bot/clawd/south_east_sign_companies.csv`
- `/home/clawd_bot/clawd/memory/UK_Sign_Industry_Directory.csv`

Search criteria:

- `County == Greater London` or address contains London borough/postcode.
- Company name or source context clearly fits sign, signage, display, graphics, engraving, plaques, wayfinding, architectural signs, shopfront signs.
- Must have at least email + phone + address, or a real direct website with visible contact info.

## Output Only
Write:

- `data/london-pass-candidates.json`
- `reports/uk-sign-london-pass-candidates-2026-06-12.md`

Each candidate shape:

```json
{
  "county": "Greater London",
  "category": "Signage",
  "company": "Company name",
  "website": null,
  "email": "visible email or null",
  "phone": "visible phone or empty string",
  "address": "visible address or empty string",
  "linkedin": "url or null",
  "instagram": "url or null",
  "facebook": "url or null",
  "sellsPlaques": false,
  "evidence": {
    "source": "local csv / direct website",
    "sourceFile": "source file path",
    "checkedUrl": "url if checked, otherwise null",
    "notes": "why it fits and any uncertainty"
  }
}
```

## Validation
- JSON parse the candidate file.
- Check candidate company/email duplicates against existing data and previous additions.
- Count candidates with email, phone, address, website.
- Call out any rows excluded as too weak or placeholder-like.

