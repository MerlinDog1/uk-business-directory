# MiMo Task: UK Sign Directory Second Pass

## Goal
Find another batch of UK sign-industry companies for this repo, with better coverage and email recovery than the first strict pass.

## Hard Rules
- Do not edit `data/directory-data.json` or `data/metadata.json`.
- Do not invent websites from company names.
- Do not guess emails.
- Do not use emails unless they are visible in source data or on the company's own website/contact page.
- Avoid directory/search-result pages as primary websites: Yell, Cylex, 192, Thomson Local, Independent directory, local newspaper directory pages, etc.
- Avoid duplicates already in `data/directory-data.json`.
- Avoid companies already in `data/new-entries.json`.
- If MiMo `task` or `actor` subtools throw schema errors, continue with read/bash/write/edit tools only.

## What To Produce
Write candidates only to:

- `data/second-pass-candidates.json`
- `reports/uk-sign-second-pass-candidates-2026-06-12.md`

Each candidate must use this shape:

```json
{
  "county": "County or region",
  "category": "Signage",
  "company": "Company name",
  "website": "https://real-company-website.example",
  "email": "visible-email@example.com or null",
  "phone": "visible phone or empty string",
  "address": "visible address or empty string",
  "linkedin": "url or null",
  "instagram": "url or null",
  "facebook": "url or null",
  "sellsPlaques": false,
  "evidence": {
    "source": "local csv / direct website / web search",
    "sourceFile": "path if local csv",
    "checkedUrl": "url actually checked",
    "notes": "brief reason this fits the brief"
  }
}
```

## Search Direction
Use local CSV backlog first, then web discovery if useful:

- `/home/clawd_bot/clawd/uk_sign_companies.csv`
- `/home/clawd_bot/clawd/north_west_sign_companies.csv`
- `/home/clawd_bot/clawd/midlands_sign_companies.csv`
- `/home/clawd_bot/clawd/south_west_sign_companies.csv`
- `/home/clawd_bot/clawd/south_east_sign_companies.csv`
- `/home/clawd_bot/clawd/east_anglia_sign_companies.csv`
- `/home/clawd_bot/clawd/scotland_sign_companies.csv`
- `/home/clawd_bot/clawd/wales_sign_companies.csv`
- `/home/clawd_bot/clawd/yorkshire_north_east_sign_companies.csv`
- `/home/clawd_bot/clawd/memory/UK_Sign_Industry_Directory.csv`

Prioritise companies with:

- real website URLs from source data or directly verified by website/contact page,
- visible email addresses,
- architectural signage, trade signs, wayfinding, metal signs, plaques, etching or engraving relevance,
- counties underrepresented in the current dataset.

## Target Batch
Aim for 25-50 candidates. Stop lower if only a smaller verified batch is defensible.

## Validation To Run
Before finishing:

- JSON parse `data/second-pass-candidates.json`.
- Check duplicate company/site against `data/directory-data.json` and `data/new-entries.json`.
- Check every candidate has a real `http` website.
- Check emails contain `@` and are not placeholders.
- Write validation results to the report.

