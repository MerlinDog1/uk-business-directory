# Compare SUPATED customers

Export the current SUPATED customers as CSV or JSON and keep that export private. The export needs a `company` column; `postcode` and `phone_number` help identify possible matches. JSON may be an array or an object with a `customers` or `data` array. Run this from the repository root with Python 3:

```powershell
python tools/compare_supated_customers.py C:\private\supated-customers.csv --output C:\private\customer-overlay.json --review C:\private\customer-review.json
```

The overlay contains directory IDs, `confirmed` or `possible` labels, customer names and matching evidence. Import it using the directory's customer-status control. The optional review report also contains company names and match evidence, so keep both files private and do not commit or publish them. Create the output folder before running the command. Never put customer data into this public repository.

Unique company names that match after normalizing punctuation, case and legal suffixes are marked confirmed only if the postcode or phone also matches and there is no conflicting postcode. Name-only matches, duplicate names and similar names with a matching postcode or phone are marked possible for review. No algorithm can guarantee two records are the same customer; verify questionable matches. No match means **unknown**, not proof that the business is not a customer. Repeat the export and comparison to refresh the snapshot; it does not sync automatically. Overlays refer to directory IDs and should be regenerated if the directory data changes.

Run comparison tests with `python -m unittest discover -s tools -p test_compare_supated_customers.py`.
