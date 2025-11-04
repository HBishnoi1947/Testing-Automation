from playwright.sync_api import sync_playwright
from playwright.async_api import Page
from typing import Optional
 
def extract_dom_to_file(url, output_file='dom_content.txt'):
    """
    Extract DOM content from a URL and save to file (synchronous version).
    
    Args:
        url: URL to extract DOM from
        output_file: Path to save the DOM content
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
       
        # Navigate to the URL
        page.goto(url)
       
        # Wait for the page to fully load
        page.wait_for_load_state('networkidle')
       
        # Extract the entire DOM content
        html_content = page.content()
       
        # Save to text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
       
        print(f"DOM content successfully saved to {output_file}")
       
        # Browser closes automatically with context manager
        browser.close()


async def save_page_dom_to_file(page: Page, output_file: str) -> None:
    """
    Extract DOM content from a Playwright Page object and save to file (async version).
    
    Args:
        page: Playwright async Page object to extract DOM from
        output_file: Path to save the DOM content
        
    Example:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://example.com')
            await save_page_dom_to_file(page, 'dom_content.txt')
    """
    # Extract the entire DOM content
    html_content = await page.content()
    
    # Save to text file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"DOM content successfully saved to {output_file}")
 
if __name__ == "__main__":
    url = "https://bishnoishaadi.com/login"
    extract_dom_to_file(url, 'bishnoishaadi_dom.txt')