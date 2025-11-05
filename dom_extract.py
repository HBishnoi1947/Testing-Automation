from playwright.sync_api import sync_playwright, Page as SyncPage
from playwright.async_api import Page
from typing import Optional
 
def save_page_dom_to_file(page, output_file='dom_content.txt') -> None:
    """
    Extract DOM content from a Playwright Page object and save to file.
    Works with both sync and async Page objects.
    
    Args:
        page: Playwright Page object (sync or async) to extract DOM from
        output_file: Path to save the DOM content
    """
    # Extract the entire DOM content (works for both sync and async)
    html_content = page.content()
    
    # Save to text file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"DOM content successfully saved to {output_file}")
 
if __name__ == "__main__":
    url = "https://bishnoishaadi.com/login"
    extract_dom_to_file(url, 'bishnoishaadi_dom.txt')