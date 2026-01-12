# Confluence PDF Exporter

Python script to export Confluence pages as PDF using Playwright.

## How It Works

The script automates the PDF export process by:

1. **Clicking through Confluence's UI** - Uses Playwright to click:
   - "Weitere Aktionen" (More Actions) button
   - "Exportieren" (Export) option
   - "PDF Exportieren" link
2. **Waiting for PDF generation** - Navigates to FlyingPDF page and waits for "Download PDF" button to appear (up to 2 minutes)
3. **Downloading the PDF** - Clicks the "Download PDF" button and saves the file

This uses Confluence's native FlyingPDF export, which generates high-quality PDFs with proper formatting. If the automated clicking fails, it falls back to browser-based PDF generation.

## Features

- Works with any authentication method (Apple ID, Google, password, SSO, etc.)
- Cookie-based authentication (login once, export multiple times)
- Runs in headless mode after initial authentication
- Automatically hides trial expiration messages
- No screenshots - direct PDF export only

## Installation

```bash
pip install playwright
playwright install chromium
```

## Usage

### First time: Login and save cookies

```bash
python3 export.py --login
```

This will:
1. Open a browser window
2. Navigate to your Confluence site
3. Wait for you to log in manually (using any authentication method)
4. Automatically detect when you're logged in
5. Save authentication cookies to `auth_cookies.json`

### Export PDF

```bash
python3 export.py
```

This uses the saved cookies to export the configured page as PDF.

## Configuration

Edit the variables at the top of `export.py`:

- `PAGE_URL`: The Confluence page to export
- `OUTPUT_FILE`: Name of the output PDF file
- `COOKIES_FILE`: Name of the cookies file (default: `auth_cookies.json`)

## Notes

- Cookies expire after some time - if you get authentication errors, run `--login` again
- The script automatically hides trial/expiration banner messages
- PDF format is A4 with 20px margins and background graphics enabled
- The script only exports PDFs - no screenshots are taken during the process
