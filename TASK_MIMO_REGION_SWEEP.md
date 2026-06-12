# MiMo Task: Full UK Regional Sign Directory Sweep

## Goal
Work through the remaining regional CSV backlog and produce verified sign-company candidates county/region by county/region.

## Hard Rules
- Candidate-only first. Do not edit `data/directory-data.json` or `data/metadata.json`.
- Do not guess websites from company names.
- You may test an email domain as a possible company website only if the row has a real email, e.g. `sales@example.co.uk` -> check `https://example.co.uk`.
- Do not guess emails.
- Avoid duplicate companies/emails/websites already in:
  - `data/directory-data.json`
  - `data/new-entries.json`
  - `data/second-pass-email-additions.json`
  - `data/london-verified-additions.json`
- Treat regional generated CSVs skeptically. Reject placeholder-looking rows, repeated fake phone patterns, and email domains that do not match the company/signage context.
- If MiMo `task` or `actor` tools throw schema errors, continue with read/bash/write/edit tools only.

## Primary Sources
Sweep these:

- `/home/clawd_bot/clawd/north_west_sign_companies.csv`
- `/home/clawd_bot/clawd/midlands_sign_companies.csv`
- `/home/clawd_bot/clawd/south_west_sign_companies.csv`
- `/home/clawd_bot/clawd/south_east_sign_companies.csv`
- `/home/clawd_bot/clawd/east_anglia_sign_companies.csv`
- `/home/clawd_bot/clawd/scotland_sign_companies.csv`
- `/home/clawd_bot/clawd/wales_sign_companies.csv`
- `/home/clawd_bot/clawd/yorkshire_north_east_sign_companies.csv`

## Verification Standard
A candidate is strong if:

- company name clearly fits signs/signage/display/graphics/wayfinding/shopfront/engraving/plaque context;
- row has email + phone + address;
- email is not placeholder/generic junk;
- email domain either matches the company name/signage context or is a generic mailbox;
- if a direct website is not present, checking the email domain returns HTTP 200 and the page contains sign/signage/display/graphics/shopfront/wayfinding/engraving/plaque wording.

## Output Only
Write:

- `data/region-sweep-candidates.json`
- `reports/uk-sign-region-sweep-candidates-2026-06-12.md`

Candidate shape:

```json
{
  "county": "County/region",
  "category": "Signage",
  "company": "Company name",
  "website": "verified email-domain website or null",
  "email": "visible source email",
  "phone": "source phone",
  "address": "source address",
  "linkedin": "url or null",
  "instagram": "url or null",
  "facebook": "url or null",
  "sellsPlaques": false,
  "evidence": {
    "source": "local csv / email-domain website",
    "sourceFile": "source csv",
    "checkedUrl": "url checked or null",
    "notes": "brief verification note"
  }
}
```

## Target
Work region by region. Aim for as many verified candidates as survive the standard, but do not pad.

