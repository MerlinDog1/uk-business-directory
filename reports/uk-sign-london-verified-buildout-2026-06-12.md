# UK Sign Directory London Verified Buildout - 2026-06-12

## Summary
- Added 5 London-focused sign-company entries.
- Each accepted row has email, phone, address and a direct website that returned HTTP 200 during verification.
- Repeated `Signs Now` borough rows and other no-website rows were left unmerged pending direct verification.

## Added Companies
- E U Signs Ltd - info@eusigns.co.uk | 020 3375 2100 | https://eusigns.co.uk
  Evidence: Website returned HTTP 200; page title references health and safety signs.
- Sign Architects - info@signarchitects.co.uk | 020 8507 3395 | https://signarchitects.co.uk
  Evidence: Website returned HTTP 200; page title says Signage Company London.
- Bellenden Signs Ltd - info@bellendensigns.com | 020 3654 7973 | https://bellendensigns.com
  Evidence: Website returned HTTP 200; page title says London Sign Maker Specialists.
- Lumen Signs Ltd - info@lumensigns.co.uk | 020 3375 2100 | https://lumensigns.co.uk
  Evidence: Website returned HTTP 200; page title says Custom Signage Company In London.
- Butler Signs - info@butlersigns.co.uk | 01635 250680 | https://butlersigns.co.uk
  Evidence: Website returned HTTP 200; page title says award winning signage.

## Validation
- JSON parse: passed on 2026-06-12.
- Duplicate gate: company, website and email checked before append.
- Safety gate: no guessed websites/emails and no GitHub push performed.
