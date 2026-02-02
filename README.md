# UK Business Directory

A searchable, filterable directory of 1,200+ UK businesses across 48 counties. Find sign companies, architects, engravers, and trophy suppliers.

## Features

- 🔍 **Full-text search** - Search by company name, address, county, or keyword
- 📊 **Filter by category** - Sign Companies, Architects, Engravers, Trophy Suppliers
- 🗺️ **Filter by county** - All 48 UK counties covered
- ⭐ **Quality scores** - Businesses rated 1-10 based on data completeness
- 📱 **Responsive design** - Works on desktop, tablet, and mobile
- 🔗 **Direct links** - Website, email, LinkedIn, Instagram, and Facebook links
- 🌙 **Clean UI** - Modern, distraction-free interface

## Data Coverage

- **1,211 businesses** total
- **48 counties** across England, Wales, and Northern Ireland
- **4 categories** per county

## Categories

| Category | Description |
|----------|-------------|
| Sign Company | Sign makers, vehicle graphics, shop fascias, banners |
| Architect | Chartered architects, architectural design firms |
| Engraver | Industrial, commercial, and personal engraving services |
| Trophy Supplier | Trophies, medals, awards, and engraving |

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

Data compiled from web research across all UK counties. Each business entry includes:
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
2. Run the data export script to regenerate `data/directory-data.json`
3. Commit and push changes
