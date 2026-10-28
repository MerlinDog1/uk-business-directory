# Sign Index

This local site combines three separate lists behind the directory switch:

- **UK signs:** `data/directory-data.json`.
- **UK wayfinding:** `data/wayfinding-directory-data.json`, a snapshot of [`MerlinDog1/uk-wayfinding-directory`](https://github.com/MerlinDog1/uk-wayfinding-directory).
- **Global wayfinding:** `data/global-wayfinding-directory-data.json`, a snapshot of [`MerlinDog1/global-wayfinding-directory`](https://github.com/MerlinDog1/global-wayfinding-directory), plus `data/global-wayfinding-contacts.json` and `data/global-wayfinding-outreach.json`.

Each list has separate filters, selections and customer reviews while the tab is open. Export applies only to the selected list. Refreshing the page resets in-tab selections and unsaved reviews. The wayfinding files are local snapshots and do not sync automatically.

Global contacts, suggested outreach routes, source confidence and notes are historical research: verify them before use. Global country labels are source data and may not reflect every office; the global map is unavailable because locations are not reliable enough to plot. Some mismatched contact records are withheld, and four audited contacts are remapped to their matching companies.

To refresh a snapshot, obtain the latest source repository separately, compare its data with the existing local files and any local corrections, then copy the intended files into the names above. The UK source is `data/directory-data.json`; the global sources are `data/directory-data.json`, `data/company-contacts.json` and `data/outreach-shortlist.json`. Re-check company IDs, contact-name joins and remaps before replacing data. Customer comparisons use list-specific IDs: back up existing reviewed comparisons and regenerate/review them if source IDs change. Do not publish customer comparisons with the public repository.

## Private customer comparison

Each directory can load its own local JSON comparison using **Load comparison**. The file is read in the browser tab only; it is not uploaded or stored. The local helper can also load the appropriate private comparison automatically when the site runs at `http://127.0.0.1:8767`. Do not commit comparison files: this repository and its GitHub Pages site are public.

The comparison format is `{"dataset":"signs","matches":[{"id":123,"status":"confirmed"},{"id":456,"status":"possible","customer":"Customer name","reason":"Why this may match"}]}`. The dataset must be `signs`, `wayfinding` or `global-wayfinding`; older untagged comparisons are accepted only for UK signs. IDs refer to entries in the selected list and can overlap across lists. Each ID must be unique and present in that list. The valid statuses are `confirmed`, `possible` and `rejected`. `customer` and `reason` are optional text shown for review. An imported comparison labels other entries **No match found**, which is not proof that they are new customers. Without a comparison, all entries are **Unchecked**. Possible matches need review. You can confirm, reject or return a match to review. Use **Save review** to download your decisions before reloading, then load that file next time. Keep the downloaded file private.

Filter by customer status to review entries. **Recently added** finds researched additions with a recorded date; each card and CSV shows the date. **Latest sweep** isolates the most recent research batch in each directory. **Select matches** and **Deselect matches** affect both strong and possible matches across the active directory, including hidden entries, without changing other selections. The CSV includes customer status. **Select shown** applies to the current filter; **Clear selection** clears the active list's selections.

A searchable, filterable directory of UK signage, engraving, plaque, print, and trophy suppliers.

## Features

- 🔍 **Full-text search** - Search by company name, address, county, or keyword
- 📊 **Filter by category** - Signage, engraving, print, trophies, and plaque-related suppliers
- 🗺️ **Filter by county** - All 48 UK counties covered
- ⭐ **Quality scores** - Businesses rated 1-10 based on data completeness
- 📱 **Responsive design** - Works on desktop, tablet, and mobile
- 🔗 **Direct links** - Website, email, LinkedIn, Instagram, and Facebook links
- 🌙 **Clean UI** - Modern, distraction-free interface

## Data Coverage

- **1,067 UK sign businesses** after splitting architects into their own repository and adding researched leads
- **60 UK wayfinding** and **193 global wayfinding** entries, including researched additions to the imported snapshots
- Coverage across England, Wales, Scotland, Northern Ireland, and the Isle of Man
- Signage, engraving, trophy, plaque, and print-related categories

## Categories

| Category | Description |
|----------|-------------|
| Signage | Sign makers, vehicle graphics, shop fascias, banners, display and graphics firms |
| Engraving | Industrial, commercial, memorial, plaque and personal engraving services |
| Trophies | Trophies, medals, awards and related engraving |
| Printers | Print suppliers that overlap with signage or display work |

## Running Locally

Serve the directory with a static server. To enable automatic private comparisons on this computer, use the exact loopback origin shown below and run the local helper in a second terminal:

```powershell
python -m http.server 8767 --bind 127.0.0.1
node tools/supated-export-server.cjs
```

Open `http://127.0.0.1:8767/`. The helper serves the selected list's private comparison only to that origin. If the helper is unavailable, a comparison can still be loaded manually. The existing export instructions are in `docs/customer-comparison.md` and `docs/supated-export.md`.

Other static servers can serve the site, although automatic private-comparison loading is restricted to the origin above:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (with http-server)
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000`

## Data Source

Data compiled from web research across UK regions. Each business entry includes:
- Company name and category
- Website and contact information
- Social media links (where available)
- Address and phone number
- Quality score (1-10)

## License

MIT License - Feel free to use and modify.

## Contributing

To update the directory:
1. Update CSV files in `/home/clawd_bot/clawd/memory/`
2. Run the relevant merge/export script to regenerate `data/directory-data.json`
3. Commit and push changes
