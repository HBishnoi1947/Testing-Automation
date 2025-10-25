from playwright.sync_api import sync_playwright
 
def extract_dom_to_file(url, output_file='dom_content.txt'):
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
 
if __name__ == "__main__":
    url = "https://bishnoishaadi.com/login"
    extract_dom_to_file(url, 'bishnoishaadi_dom.txt')