from playwright.sync_api import sync_playwright, Page, Browser
import time
from model import get_all_actions_from_excel, ActionSpec, OperationType


class ActionExecutor:
    """Executes actions from Excel file using Playwright."""
    
    def __init__(self, browser=None, page=None):
        """Initialize the executor with optional Playwright browser and page instances."""
        self.playwright = None
        self.browser = browser
        self.page = page
    
    def execute_actions_from_excel(self, excel_file="actions.xlsx", sheet_name="Actions"):
        """Read actions from Excel and execute them in sequence."""
        try:
            # Initialize Playwright if not provided
            if not self.browser or not self.page:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=False)
                self.page = self.browser.new_page()
            
            # Get all actions from Excel
            actions = get_all_actions_from_excel(excel_file, sheet_name)
            print(f"Loaded {len(actions)} actions from Excel")
            
            # Execute each action
            for i, action in enumerate(actions, 1):
                print(f"\nExecuting action {i}/{len(actions)}: {action.operationType.value}")
                self.execute_action(action)
                time.sleep(4)  # Small delay between actions
                
        except Exception as e:
            print(f"Error executing actions: {e}")
        finally:
            # Keep browser open for a moment to see results
            input("Press Enter to close browser...")
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
    
    def execute_action(self, action: ActionSpec):
        """Execute a single action based on its operation type."""
        try:
            # Navigate to URL if specified and not already on that page
            if action.url:
                current_url = self.page.url
                if not self._is_same_url(current_url, action.url):
                    print(f"Navigating to: {action.url}")
                    self.page.goto(action.url)
                    self.page.wait_for_load_state("networkidle")
                else:
                    print(f"Already on {action.url}, skipping navigation")
            
            # Execute based on operation type
            if action.operationType == OperationType.CLICK:
                self._perform_click(action)
            elif action.operationType == OperationType.SCROLL:
                self._perform_scroll(action)
            elif action.operationType == OperationType.INPUT_TEXT:
                self._perform_input_text(action)
            else:
                print(f"Unknown operation type: {action.operationType}")
                
        except Exception as e:
            print(f"Error executing action {action.id}: {e}")
    
    def _is_same_url(self, current_url: str, target_url: str) -> bool:
        """Check if current URL matches target URL, ignoring protocol and trailing slashes."""
        try:
            # Remove protocol and normalize URLs
            current_normalized = current_url.replace('https://', '').replace('http://', '').rstrip('/')
            target_normalized = target_url.replace('https://', '').replace('http://', '').rstrip('/')
            
            # Check if URLs match
            return current_normalized == target_normalized
        except:
            return False
    
    def _perform_click(self, action: ActionSpec):
        """Perform click operation on the specified HTML component."""
        print(f"Clicking element: {action.htmlComponent}")
        
        try:
            # Try different locator strategies
            locator = None
            
            # Try as CSS selector first (most common)
            try:
                locator = self.page.locator(action.htmlComponent)
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as XPath
            try:
                locator = self.page.locator(f"xpath={action.htmlComponent}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as ID selector
            try:
                locator = self.page.locator(f"#{action.htmlComponent}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as class selector
            try:
                locator = self.page.locator(f".{action.htmlComponent}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.htmlComponent}")
                    return
            except:
                pass
            
            print(f"Could not find clickable element: {action.htmlComponent}")
            
        except Exception as e:
            print(f"Error clicking element {action.htmlComponent}: {e}")
    
    def _perform_scroll(self, action: ActionSpec):
        """Perform scroll operation."""
        print(f"Scrolling: {action.htmlComponent}")
        
        try:
            if action.htmlComponent.lower() == "down":
                self.page.evaluate("window.scrollBy(0, 500);")
            elif action.htmlComponent.lower() == "up":
                self.page.evaluate("window.scrollBy(0, -500);")
            elif action.htmlComponent.lower() == "top":
                self.page.evaluate("window.scrollTo(0, 0);")
            elif action.htmlComponent.lower() == "bottom":
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            else:
                # Try to scroll to specific element
                try:
                    locator = self.page.locator(action.htmlComponent)
                    if locator.count() > 0:
                        locator.scroll_into_view_if_needed()
                        print(f"Successfully scrolled to element: {action.htmlComponent}")
                    else:
                        print(f"Could not find element to scroll to: {action.htmlComponent}")
                except:
                    print(f"Could not scroll to element: {action.htmlComponent}")
        except Exception as e:
            print(f"Error scrolling: {e}")
    
    def _perform_input_text(self, action: ActionSpec):
        """Perform input text operation."""
        if not action.Input:
            print("No input text provided")
            return
            
        print(f"Inputting text '{action.Input}' into: {action.htmlComponent}")
        
        try:
            # Try different locator strategies
            locator = None
            
            # Try as CSS selector first (most common)
            try:
                locator = self.page.locator(action.htmlComponent)
                if locator.count() > 0:
                    locator.fill(action.Input)
                    print(f"Successfully input text into: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as XPath
            try:
                locator = self.page.locator(f"xpath={action.htmlComponent}")
                if locator.count() > 0:
                    locator.fill(action.Input)
                    print(f"Successfully input text into: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as ID selector
            try:
                locator = self.page.locator(f"#{action.htmlComponent}")
                if locator.count() > 0:
                    locator.fill(action.Input)
                    print(f"Successfully input text into: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as class selector
            try:
                locator = self.page.locator(f".{action.htmlComponent}")
                if locator.count() > 0:
                    locator.fill(action.Input)
                    print(f"Successfully input text into: {action.htmlComponent}")
                    return
            except:
                pass
            
            # Try as name attribute
            try:
                locator = self.page.locator(f"[name='{action.htmlComponent}']")
                if locator.count() > 0:
                    locator.fill(action.Input)
                    print(f"Successfully input text into: {action.htmlComponent}")
                    return
            except:
                pass
            
            print(f"Could not find input element: {action.htmlComponent}")
            
        except Exception as e:
            print(f"Error inputting text into {action.htmlComponent}: {e}")


def main():
    """Main function to execute actions from Excel file."""
    executor = ActionExecutor()
    executor.execute_actions_from_excel()


if __name__ == "__main__":
    main()
