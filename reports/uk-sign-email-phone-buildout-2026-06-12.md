# UK Sign Directory Email/Phone Buildout - 2026-06-12

## Summary
- Added 17 additional sign-company entries from the high-confidence national seed CSV with real email, phone and address fields.
- No websites were guessed. Rows without a real website are stored with `website: null`.
- Emails were accepted only when present in the source row and not obvious placeholders.
- Non-generic email domains had to match the company name or sign/display wording.
- Broader regional CSV rows were reviewed by MiMo but left unmerged because several looked placeholder-like and need direct verification first.

## Counties Improved
- Berkshire: 1
- Bristol: 1
- Buckinghamshire: 1
- Cheshire: 1
- East Riding of Yorkshire: 1
- Greater London: 1
- Greater Manchester: 1
- Hampshire: 1
- Lanarkshire: 1
- Leicestershire: 1
- Merseyside: 1
- Norfolk: 1
- Suffolk: 1
- Swansea: 1
- Tyne and Wear: 1
- West Midlands: 1
- West Yorkshire: 1

## Source Files
- uk_sign_companies.csv: 17

## Added Companies
- Alpen Signs (Leicestershire) - info@alpensigns.co.uk | 0116 263 0550 | source: uk_sign_companies.csv
- Lavastar (Hampshire) - info@lavastar.co.uk | 0845 459 4525 | source: uk_sign_companies.csv
- Signs Express (HQ) (Norfolk) - info@signsexpress.co.uk | 01603 625925 | source: uk_sign_companies.csv
- Ward Signs (Bristol) - info@ward-signs.co.uk | 0117 937 2636 | source: uk_sign_companies.csv
- Goodwin & Goodwin (Greater London) - sales@goodwinandgoodwin.com | 020 8829 0599 | source: uk_sign_companies.csv
- Apex Signs & Graphics (West Midlands) - info@apexsigns.co.uk | 0121 359 5555 | source: uk_sign_companies.csv
- Designs Signage Solutions (East Riding of Yorkshire) - info@designs.uk.net | 01482 787713 | source: uk_sign_companies.csv
- Merson Group (Lanarkshire) - enquiries@mersongroup.com | 01355 243 021 | source: uk_sign_companies.csv
- Widd Signs (Merseyside) - info@widdsigns.co.uk | 0113 250 2662 | source: uk_sign_companies.csv
- Astley (Tyne and Wear) - info@astley-uk.com | 0191 414 4144 | source: uk_sign_companies.csv
- D&A Media (Berkshire) - info@damedia.co.uk | 0118 977 2222 | source: uk_sign_companies.csv
- Omega Signs (West Yorkshire) - info@omega-signs.co.uk | 0113 240 3000 | source: uk_sign_companies.csv
- isGroup Signs (Cheshire) - info@is-group.co.uk | 01244 371443 | source: uk_sign_companies.csv
- Signs Display (Suffolk) - info@signsdisplay.com | 01473 711100 | source: uk_sign_companies.csv
- Signum Sign Studio (Buckinghamshire) - info@signum-signs.com | 01296 489099 | source: uk_sign_companies.csv
- Signature Signs (Swansea) - info@signaturesigns.co.uk | 01792 581561 | source: uk_sign_companies.csv
- Signage Systems (Greater Manchester) - info@signagesystems.co.uk | 0161 336 2266 | source: uk_sign_companies.csv

## Validation
- JSON parse: passed on 2026-06-12.
- Duplicate gate: company name and email checked before append.
- Safety gate: no guessed websites and no GitHub push performed.
