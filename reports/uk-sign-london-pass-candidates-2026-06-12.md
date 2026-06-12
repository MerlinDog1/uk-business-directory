# London Pass Candidates Report — 2026-06-12

## Summary

- **Candidates written**: 24
- **Source files scanned**:
  - `/home/clawd_bot/clawd/south_east_sign_companies.csv` (32 Greater London rows)
  - `/home/clawd_bot/clawd/memory/UK_Sign_Industry_Directory.csv` (16 Greater London rows)
- **Duplicates removed**: 18 (against directory-data.json, new-entries.json, second-pass-email-additions.json)
- **Weak/garbled rows excluded**: 4

## Coverage

| Field       | Count | %     |
|-------------|-------|-------|
| Email       | 24    | 100%  |
| Phone       | 24    | 100%  |
| Address     | 24    | 100%  |
| Website     | 0     | 0%    |
| LinkedIn    | 0     | 0%    |
| Instagram   | 1     | 4%    |
| Facebook    | 2     | 8%    |

No websites were available in the source CSV data. All candidates are CSV-sourced only — no direct website verification was performed.

## Unique Company Groups

1. **E U Signs Ltd** — Borehamwood, sign manufacturing
2. **Significant Signs** — SE24, signage
3. **Sign Architects** — IG11, signage with Instagram/Facebook
4. **Bellenden Signs Ltd** — SE15, signage
5. **Lumen Signs Ltd** — E14, signage
6. **Genesis Signs & Print** — SE5, signs and print
7. **Signtec Direct** — IG6, sign technology
8. **Links Signs** — weak London link (01424 Hastings phone, address "London/Hastings") — verify before inclusion
9. **Signs Now (16 branches)** — franchise network across Greater London: Ealing, Wembley, Enfield, Harrow, Hornsey, Finchley, Islington, Uxbridge, Camden Town, Willesden, Westminster, Hounslow, Barnet, Wimbledon, Hammersmith, Tottenham

## Excluded Rows

| Company            | Reason                                              |
|--------------------|-----------------------------------------------------|
| Promo Signs        | Duplicate of existing directory entry                |
| GLYPHICS LTD       | Duplicate of existing directory entry                |
| Goodwin & Goodwin  | Duplicate of existing directory entry                |
| xsign              | Duplicate of existing directory entry                |
| Morgans Consult    | Duplicate of existing directory entry                |
| Lavastar           | Duplicate of existing directory entry                |
| Glyphics           | Duplicate of existing directory entry (UK dir)       |
| Prestige Signs     | Duplicate of existing directory entry                |
| Efficient Signs    | Duplicate of existing directory entry                |
| Sign Company London| Duplicate of existing directory entry                |
| Significant Ltd    | Duplicate of existing directory entry                |
| Extension Architecture | Duplicate of existing directory entry             |
| Stiff + Trevillion | Duplicate of existing directory entry                |
| ACS Engraving      | Duplicate of existing directory entry                |
| Engravers Guild of London | Duplicate of existing directory entry          |
| Milne & Yardley Engravers | Duplicate of existing directory entry        |
| B&W Trophies       | Duplicate of existing directory entry                |
| Supreme Awards     | Duplicate of existing directory entry                |
| 1st Place 4 Trophies | Duplicate of existing directory entry             |
| London Trophy Company | Duplicate of existing directory entry            |
| N-signs            | Non-London postcode (RM15 South Ockendon, Thurrock)  |
| Masters Engravers  | Garbled CSV row — no email, phone/address fields swapped |

## Notes

- Signs Now is a franchise network with 16 separate London branches, each with unique email, phone, and address. All included as individual candidates.
- Links Signs has a Hastings (01424) phone number and "London/Hastings" address — flagged as weak London relevance.
- No website URLs were present in either source CSV for any Greater London row, so all `website` fields are `null`.
- All data is CSV-sourced. No direct website or email verification was performed per task rules (no guessing).

## Output File

`data/london-pass-candidates.json` — 24 candidates, JSON validated.
