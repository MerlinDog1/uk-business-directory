# MiMo Task: UK Sign Industry Directory Buildout

## Goal
Expand this static UK business directory with more companies that fit the sign-industry lead-generation brief, especially:

- UK sign makers and signage contractors
- architectural signage firms
- wayfinding/signage consultancies
- plaque/engraving/etched metal signage suppliers
- trophy/award suppliers only when signage/plaque/engraving work is clearly relevant

## Current repo
- Static site: `index.html`, `css/styles.css`, `js/app.js`
- Primary data: `data/directory-data.json`
- Related data snapshots: `data/directory-data-cleaned.json`, `data/directory-data-no-dead.json`, `data/directory-data-original.json`, `data/nordic-directory-data.json`
- Metadata: `data/metadata.json`

## Required approach
1. Inspect the existing JSON schema and UI filters before editing.
2. Use the local candidate backlog first. Compare candidates against `data/directory-data.json`, then add only non-duplicate companies that fit the sign-industry brief.
3. Add genuinely relevant companies only. Avoid generic builders, printers, architects, marketing agencies, or unrelated manufacturers unless they clearly sell signage/wayfinding/plaque/engraving services.
4. Prefer rows with real website, email, phone, address or social evidence already present in the local CSVs. Direct website checks are useful, but do not let broken association pages stall the batch.
5. Local candidate files to inspect:
   - `/home/clawd_bot/clawd/memory/UK_Sign_Industry_Directory.csv`
   - `/home/clawd_bot/clawd/uk_sign_companies.csv`
   - `/home/clawd_bot/clawd/north_west_sign_companies.csv`
   - `/home/clawd_bot/clawd/midlands_sign_companies.csv`
   - `/home/clawd_bot/clawd/south_west_sign_companies.csv`
   - `/home/clawd_bot/clawd/south_east_sign_companies.csv`
   - `/home/clawd_bot/clawd/east_anglia_sign_companies.csv`
   - `/home/clawd_bot/clawd/scotland_sign_companies.csv`
   - `/home/clawd_bot/clawd/wales_sign_companies.csv`
   - `/home/clawd_bot/clawd/yorkshire_north_east_sign_companies.csv`
6. Suggested first batch size: 25-60 verified, non-duplicate sign-industry entries. Quality beats volume.
7. Preserve JSON formatting and fields used by the app.
8. Add source/evidence notes in a separate review file rather than inventing unsupported data fields.
9. If an email is not visible in the source row or direct site evidence, leave it blank/null according to the existing schema. Do not guess emails.
10. Run validation after edits:
   - JSON parse validation
   - duplicate company/website check
   - a quick static-site sanity check if practical
11. Write a report with:
   - how many entries were added
   - which counties/categories improved
   - source CSVs and source URLs checked
   - validation results
   - any uncertain entries deliberately excluded

## High-value targets
   - architectural/wayfinding signage
   - trade signage contractors
   - metal, etched, engraved, brass, stainless or plaque specialists
   - UK firms with visible contact details

## Constraints
- Do not push to GitHub.
- Do not use the MiMo `task` subtool if it throws schema errors; continue with read/bash/edit/write tools instead.
- Do not delete existing data unless it is a clear duplicate or broken test entry, and document any removal.
- Keep changes scoped to directory data, metadata, validation/report files, and minimal app changes only if needed for new fields already present in the data.
- If you hit rate limits or search friction, stop with a partial verified batch rather than padding the dataset.

## Suggested output files
- `data/directory-data.json` with additions
- `reports/uk-sign-buildout-2026-06-12.md`
- optional `tools/validate-directory-data.*` if no suitable validator exists
