# SEMCL.ONE PyPI Stats Dashboard

A GitHub Pages dashboard that tracks download statistics for all SEMCL.ONE packages published on PyPI.

## Quick Start

### 1. Initial Setup

Run the fetch script to generate initial data:

```bash
python fetch_stats.py
```

This creates `docs/data/stats.json` with the latest statistics.

### 2. Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Settings > Pages**
3. Under **Source**, select **Deploy from a branch**
4. Choose the **main** branch and **/docs** folder
5. Click **Save**

Your dashboard will be available at: `https://[username].github.io/[repository-name]/`

### 3. Automated Updates

The GitHub Actions workflow (`.github/workflows/update-stats.yml`) automatically:
- Runs daily at midnight UTC
- Fetches latest stats from pypistats.org API
- Commits updated data if changes detected
- Can be manually triggered from the Actions tab

## Tracked Packages

The dashboard tracks these SEMCL.ONE packages:

- **purl2src** - Downloads source code from Package URLs
- **binarysniffer** - Identifies hidden OSS components in binaries
- **osslili** - High-performance license detection
- **purl2notices** - Generates legal notices with licenses
- **upmex** - Universal package metadata extractor
- **src2purl** - Identifies package coordinates from source code
- **vulnq** - Multi-source vulnerability query tool
- **ospac** - Open Source Policy as Code engine
- **mcp-semclone** - MCP server for OSS compliance analysis

## Manual Updates

To manually update the statistics:

```bash
# Run the fetch script
python fetch_stats.py

# Commit and push
git add docs/data/stats.json
git commit -m "Update PyPI stats"
git push
```

Or use the **Actions** tab on GitHub to trigger the workflow manually.

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── update-stats.yml    # GitHub Actions workflow
├── docs/                        # GitHub Pages content
│   ├── index.html              # Dashboard HTML
│   ├── css/
│   │   └── style.css           # Dashboard styles
│   ├── js/
│   │   └── dashboard.js        # Dashboard JavaScript
│   └── data/
│       └── stats.json          # PyPI statistics (auto-generated)
├── fetch_stats.py              # Stats fetching script
└── README.md
```

## Customization

### Adding/Removing Packages

Edit the `PACKAGES` list in `fetch_stats.py`:

```python
PACKAGES = [
    "purl2src",
    "your-new-package",
    # ...
]
```

### Changing Update Frequency

Edit the cron schedule in `.github/workflows/update-stats.yml`:

```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at midnight UTC
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * 0'  # Weekly on Sunday
```

### Styling

Modify `docs/css/style.css` to customize colors, fonts, and layout.

## Data Source

All data is fetched from [pypistats.org](https://pypistats.org/) API:
- No API key required
- Rate limiting applied
- Data updated daily
- Historical data retained for 180 days

## License

See [LICENSE](LICENSE) file for details.
