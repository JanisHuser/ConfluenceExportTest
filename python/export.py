import asyncio
from playwright.async_api import async_playwright
import os
import json

# Configuration
PAGE_URL = "https://janishuser.atlassian.net/wiki/spaces/~70121f63681e6d9614e7185f1d55159cde9f5/pages/294914/Testseite"
OUTPUT_FILE = "Testseite.pdf"
COOKIES_FILE = "auth_cookies.json"

async def interactive_login_and_save_cookies():
    """
    Opens a browser for the user to manually log in, then saves the cookies.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("A browser window has opened.")
        print("Please log in to Confluence using your Apple ID or other method.")
        print("Waiting for you to complete login...")
        print("The script will automatically detect when you're logged in.")
        print("="*60 + "\n")

        await page.goto("https://janishuser.atlassian.net/wiki")

        # Wait for successful login
        print("Waiting for login to complete (checking every 2 seconds)...")
        max_wait = 300
        elapsed = 0
        while elapsed < max_wait:
            await asyncio.sleep(2)
            elapsed += 2

            current_url = page.url
            if "atlassian.net/wiki" in current_url and "login" not in current_url.lower():
                print(f"Login detected! Current URL: {current_url}")
                break

            if elapsed % 10 == 0:
                print(f"Still waiting... ({elapsed}s elapsed)")

        if elapsed >= max_wait:
            print("Timeout waiting for login. Please try again.")
            await browser.close()
            return

        await asyncio.sleep(3)

        # Save cookies
        cookies = await context.cookies()
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"\nCookies saved to {COOKIES_FILE}")
        print("You can now close the browser window.")

        await asyncio.sleep(5)
        await browser.close()

async def export_pdf_with_playwright():
    """
    Uses Playwright to load the page with cookies and export to PDF.
    No screenshots are taken - only PDF export.
    """
    if not os.path.exists(COOKIES_FILE):
        print(f"Error: {COOKIES_FILE} not found!")
        print("Please run this script with --login first to save cookies.")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Load cookies
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()

        print(f"Loading page: {PAGE_URL}")
        await page.goto(PAGE_URL, wait_until="networkidle")

        # Check if we're logged in
        if "login" in page.url.lower():
            print("\nError: Cookies expired or invalid!")
            print("Please run with --login to re-authenticate.")
            await browser.close()
            return False

        print("Page loaded successfully!")

        # Wait for content to fully render
        await asyncio.sleep(2)

        # Click on the "Weitere Aktionen" (More actions) button at top right
        print("Clicking 'Weitere Aktionen' menu...")
        try:
            # Look for "Weitere Aktionen" button (German for "More actions")
            # There might be multiple, find the one in the top right that's actually visible
            more_buttons = page.locator('button:has-text("Weitere Aktionen")')
            count = await more_buttons.count()
            print(f"Found {count} 'Weitere Aktionen' buttons")

            # Try each one until we find a visible one
            clicked = False
            for i in range(count):
                try:
                    button = more_buttons.nth(i)
                    # Check if it's in the top right area (not sidebar)
                    box = await button.bounding_box()
                    if box and box['x'] > 400:  # Right side of page
                        await button.click(force=True)  # Force click even if obscured
                        clicked = True
                        print(f"Clicked button {i+1}")
                        break
                except:
                    continue

            if not clicked:
                # Fallback: just try the last one
                await more_buttons.last.click(force=True)

            await asyncio.sleep(1)
            print("Menu opened!")

            # Now click on "Exportieren" (Export)
            print("Looking for Exportieren option...")

            export_option = page.locator('text="Exportieren"').first
            await export_option.wait_for(state="visible", timeout=5000)
            await export_option.click()
            await asyncio.sleep(1)
            print("Clicked Exportieren!")

            # Now a submenu should appear with export format options
            print("Looking for PDF Exportieren option in submenu...")

            # Try to find PDF export option with multiple selectors
            pdf_export_option = None
            pdf_selectors = [
                'button:has-text("PDF Exportieren")',
                'a:has-text("PDF Exportieren")',
                'text="PDF Exportieren"',
                '[role="menuitem"]:has-text("PDF")',
                'a[href*="flyingpdf"]',
            ]

            for selector in pdf_selectors:
                try:
                    option = page.locator(selector).first
                    await option.wait_for(state="visible", timeout=3000)
                    pdf_export_option = option
                    print(f"Found PDF export option with: {selector}")
                    break
                except:
                    continue

            if not pdf_export_option:
                raise Exception("Could not find PDF Exportieren option in submenu")

            # Click it - this will open a new page
            print("Clicking 'PDF Exportieren'...")
            await pdf_export_option.click()

            # Wait for navigation to the PDF generation page
            await page.wait_for_load_state("load")
            await asyncio.sleep(2)
            print(f"Navigated to: {page.url}")

            # Wait for the "Download PDF" button to appear (Confluence is generating the PDF)
            print("Waiting for 'Download PDF' button to appear...")
            download_button = page.locator('text="Download PDF"')
            await download_button.wait_for(state="visible", timeout=120000)  # Wait up to 2 minutes
            print("'Download PDF' button is now visible!")

            # Click the Download PDF button and wait for the download
            print("Clicking 'Download PDF' button...")
            async with page.expect_download(timeout=60000) as download_info:
                await download_button.click()
                print("Clicked! Waiting for download to start...")

            download = await download_info.value
            print(f"Download started: {download.suggested_filename}")

            # Save the downloaded file
            await download.save_as(OUTPUT_FILE)
            file_size = os.path.getsize(OUTPUT_FILE) / 1024
            print(f"PDF downloaded successfully from Confluence ({file_size:.1f} KB)")

        except Exception as e:
            print(f"Error during automated export: {e}")
            print("Falling back to browser PDF generation...")

            # Fallback: use browser's PDF generation
            await page.pdf(
                path=OUTPUT_FILE,
                format="A4",
                print_background=True,
                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
            )
            file_size = os.path.getsize(OUTPUT_FILE) / 1024
            print(f"PDF generated using browser print ({file_size:.1f} KB)")

        file_size = os.path.getsize(OUTPUT_FILE) / 1024
        print(f"PDF exported successfully ({file_size:.1f} KB)")

        await browser.close()
        return True

async def main():
    import sys

    if "--login" in sys.argv:
        await interactive_login_and_save_cookies()
    else:
        success = await export_pdf_with_playwright()
        if not success:
            print("\nTip: Run 'python3 python/export.py --login' to authenticate first.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
