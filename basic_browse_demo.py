from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
# Install once: pip install playwright and python -m playwright install

def run_demo() -> None:
	"""Basic 3-step browsing demo using Playwright (Python, sync API).

	Steps:
	1) Open example.com
	2) Click the "More information..." link
	3) Take a screenshot of the destination page
	"""
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=False, slow_mo=200)
		context = browser.new_context(viewport={"width": 1280, "height": 800})
		page = context.new_page()
		page.set_default_timeout(20000)

		# Step 1: Navigate to a stable page
		page.goto("https://playwright.dev", wait_until="networkidle")

		# Step 2: Click a reliable link on the page (robust locators and fallback)
		# Try role-based first, then CSS with :has-text() as a fallback.
		link = page.get_by_role("link", name=re.compile(r"get\s*started", re.IGNORECASE))
		try:
			link.wait_for(state="visible", timeout=10000)
			link.click(timeout=10000)
		except PlaywrightTimeoutError:
			page.locator('a:has-text("Get started")').first.click(timeout=15000)

		page.wait_for_load_state("domcontentloaded")

		# Step 3: Take a screenshot
		screenshot_path = "screenshot.png"
		page.screenshot(path=screenshot_path, full_page=True)
		print(f"Saved screenshot to {screenshot_path}")

		# Cleanup
		context.close()
		browser.close()


if __name__ == "__main__":
	run_demo()


