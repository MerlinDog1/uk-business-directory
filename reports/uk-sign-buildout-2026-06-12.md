# UK Sign Directory Buildout - 2026-06-12

## Summary
- Added 21 strict, source-backed UK sign-company entries.
- Source file: `/home/clawd_bot/clawd/memory/UK_Sign_Industry_Directory.csv`.
- Rejected rows without real website fields, rows from directory/search pages, and duplicates already present in `data/directory-data.json`.
- MiMo was used to inspect the repo and build an initial comparison script, but its broad no-website pass was rejected because it fabricated website-looking URLs.

## Counties Improved
- Bedfordshire: 1
- Berkshire: 1
- Cambridgeshire: 2
- Cornwall: 1
- Devon: 1
- Durham: 1
- East Sussex: 1
- Greater London: 2
- Greater Manchester: 3
- Kent: 2
- Lincolnshire: 3
- North Yorkshire: 1
- Northumberland: 2

## Added Companies
- The Sign Shop Dunstable (Bedfordshire) - https://thesignshop-dunstable.co.uk | 01582 500 600
- Simplex Ltd (Berkshire) - https://www.simplexltd.com | info@simplexltd.com
- Motive Graphics (Cambridgeshire) - https://motivegraphics.co.uk | 01234 812922
- The Sign Team (Cambridgeshire) - https://www.thesignteam.com
- RH Signs and Graphics (Cornwall) - https://www.rh-signscornwall.co.uk | richard289@hotmail.co.uk | 0790 35 35 817
- AS Signs and Graphics (Devon) - https://assignsandgraphics.co.uk | alex@assignsandgraphics.co.uk | 01884 840906
- Skipbridge Signs (Durham) - https://www.skipbridgesigns.co.uk | info@skipbridgesigns.co.uk | 01325 749 399
- The Sign Shop (Hailsham) (East Sussex) - http://www.thesignshopsussex.co.uk | nic@thesignshopsussex.co.uk | 01323 846080
- Prestige Signs (Greater London) - https://www.prestigesigns.net | sales@prestigesigns.net
- Significant Ltd (Greater London) - https://www.significantsigns.co.uk | info@significantsigns.co.uk | 020 7924 9343
- Signs2Signs (Greater Manchester) - https://signs2signs.co.uk
- Manchester Signs (Greater Manchester) - https://manchester-signs.com
- Sign UK (Greater Manchester) - https://www.sign-uk.com | 0161 747 3333
- Sign Right UK (Kent) - https://signrightuk.com
- Sign Wizard (Kent) - https://www.sign-wizard.co.uk
- Lincs Signs (Lincolnshire) - https://lincs-signs.co.uk | enquiries@lincs-signs.co.uk
- Elite Signs Ltd (Lincolnshire) - https://elite4signs.co.uk | sales@elite4signs.co.uk
- Grimsby Signs Ltd (Lincolnshire) - https://grimsbysigns.com | grimsbysigns@outlook.com | 01472 268868
- Design Display (North Yorkshire) - https://www.designdisplay.co.uk/ | info@designdisplay.co.uk
- Ark Signs Ltd (Northumberland) - https://www.arksigns.co.uk
- Ellis Signs (Northumberland) - https://ellissigns.co.uk

## Validation
- JSON parse: passed on 2026-06-12.
- Duplicate gate: company name and website checked before append.
- Safety gate: no GitHub push performed.
