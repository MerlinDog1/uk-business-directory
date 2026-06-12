# UK Sign Directory

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

- **985 businesses** total after splitting architects into their own repository
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

Simply open `index.html` in a web browser, or serve with any static server:

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
