from playwright.sync_api import sync_playwright, Page, Browser
import time
from model import get_all_events_from_sqlite, Event
from model.operation_type import OperationTypeMapper


class ActionExecutor:
    """Executes events from Excel file using Playwright."""
    
    def __init__(self, browser=None, page=None, db_path="database.db"):
        """Initialize the executor with optional Playwright browser and page instances."""
        self.playwright = None
        self.browser = browser
        self.page = page
        self.db_path = db_path
        self.operation_mapper = OperationTypeMapper(db_path)
    
    def execute_events_from_excel(self, excel_file="events.xlsx", sheet_name="events"):
        """Read events from Excel and execute them in sequence."""
        try:
            # Initialize Playwright if not provided
            if not self.browser or not self.page:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=False)
                self.page = self.browser.new_page()
            
            # Get all events from Excel
            # events = get_all_events_from_excel(excel_file, sheet_name)

            events = get_all_events_from_sqlite()
            print(f"Loaded {len(events)} events from database")
            
            # Load operation types once for optimization
            self.operation_mapper.load_operation_types()
            print("Operation types loaded for optimized execution")
            
            # Execute each action
            for i, action in enumerate(events, 1):
                # Get operation name from mapper
                operation_name = self.operation_mapper.get_operation_name_by_id(action.operation_id)
                print(f"\nExecuting action {i}/{len(events)}: {operation_name}")
                self.execute_action(action)
                time.sleep(4)  # Small delay between events
                
        except Exception as e:
            print(f"Error executing events: {e}")
        finally:
            # Keep browser open for a moment to see results
            input("Press Enter to close browser...")
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
    
    def execute_action(self, action: Event):
        """Execute a single action based on its operation type."""
        try:
            # Navigate to URL if specified and not already on that page
            if action.url:
                current_url = self.page.url
                print(f"Current URL: {current_url}")
                print(f"Action URL: {action.url}")
                print(f"Is same URL: {self._is_same_url(current_url, action.url)}")
                if not self._is_same_url(current_url, action.url):
                    print(f"Navigating to: {action.url}")
                    self.page.goto(action.url)
                    self.page.wait_for_load_state("networkidle")
                else:
                    print(f"Already on {action.url}, skipping navigation")
            
            # Get operation name from mapper
            operation_name = self.operation_mapper.get_operation_name_by_id(action.operation_id)
            
            # Execute based on operation type
            if operation_name == "click":
                self._perform_click(action)
            elif operation_name == "scroll":
                self._perform_scroll(action)
            elif operation_name == "input_text":
                self._perform_input_text(action)
            else:
                print(f"Unknown operation type: {operation_name}")
                
        except Exception as e:
            print(f"Error executing action {action.id}: {e}")
    
    def _is_same_url(self, current_url: str, target_url: str) -> bool:
        """Check if current URL matches target URL, ignoring protocol and trailing slashes."""
        try:
            # Remove protocol and normalize URLs
            current_normalized = current_url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            target_normalized = target_url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            
            # Check if URLs match
            return current_normalized == target_normalized
        except:
            return False
    
    def _perform_click(self, action: Event):
        """Perform click operation on the specified HTML component."""
        print(f"Clicking element: {action.html_component}")
        
        try:
            # Try different locator strategies
            locator = None
            
            # Try as CSS selector first (most common)
            try:
                locator = self.page.locator(action.html_component)
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.html_component}")
                    return
            except:
                pass
            
            # Try as XPath
            try:
                locator = self.page.locator(f"xpath={action.html_component}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.html_component}")
                    return
            except:
                pass
            
            # Try as ID selector
            try:
                locator = self.page.locator(f"#{action.html_component}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.html_component}")
                    return
            except:
                pass
            
            # Try as class selector
            try:
                locator = self.page.locator(f".{action.html_component}")
                if locator.count() > 0:
                    locator.click()
                    print(f"Successfully clicked element: {action.html_component}")
                    return
            except:
                pass
            
            print(f"Could not find clickable element: {action.html_component}")
            
        except Exception as e:
            print(f"Error clicking element {action.html_component}: {e}")
    
    def _perform_scroll(self, action: Event):
        """Perform scroll operation."""
        print(f"Scrolling: {action.html_component}")
        
        try:
            if action.html_component.lower() == "down":
                self.page.evaluate("window.scrollBy(0, 500);")
            elif action.html_component.lower() == "up":
                self.page.evaluate("window.scrollBy(0, -500);")
            elif action.html_component.lower() == "top":
                self.page.evaluate("window.scrollTo(0, 0);")
            elif action.html_component.lower() == "bottom":
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            else:
                # Try to scroll to specific element
                try:
                    locator = self.page.locator(action.html_component)
                    if locator.count() > 0:
                        locator.scroll_into_view_if_needed()
                        print(f"Successfully scrolled to element: {action.html_component}")
                    else:
                        print(f"Could not find element to scroll to: {action.html_component}")
                except:
                    print(f"Could not scroll to element: {action.html_component}")
        except Exception as e:
            print(f"Error scrolling: {e}")
    
    def _perform_input_text(self, action: Event):
        """Perform input text operation."""
        if not action.input_text:
            print("No input text provided")
            return
            
        print(f"Inputting text '{action.input_text}' into: {action.html_component}")
        
        try:
            # Try different locator strategies
            locator = None
            
            # Try as CSS selector first (most common)
            try:
                locator = self.page.locator(action.html_component)
                if locator.count() > 0:
                    locator.fill(action.input_text)
                    print(f"Successfully input text into: {action.html_component}")
                    return
            except:
                pass
            
            # Try as XPath
            try:
                locator = self.page.locator(f"xpath={action.html_component}")
                if locator.count() > 0:
                    locator.fill(action.input_text)
                    print(f"Successfully input text into: {action.html_component}")
                    return
            except:
                pass
            
            # Try as ID selector
            try:
                locator = self.page.locator(f"#{action.html_component}")
                if locator.count() > 0:
                    locator.fill(action.input_text)
                    print(f"Successfully input text into: {action.html_component}")
                    return
            except:
                pass
            
            # Try as class selector
            try:
                locator = self.page.locator(f".{action.html_component}")
                if locator.count() > 0:
                    locator.fill(action.input_text)
                    print(f"Successfully input text into: {action.html_component}")
                    return
            except:
                pass
            
            # Try as name attribute
            try:
                locator = self.page.locator(f"[name='{action.html_component}']")
                if locator.count() > 0:
                    locator.fill(action.input_text)
                    print(f"Successfully input text into: {action.html_component}")
                    return
            except:
                pass
            
            print(f"Could not find input element: {action.html_component}")
            
        except Exception as e:
            print(f"Error inputting text into {action.html_component}: {e}")


def main():
    """Main function to execute events from Excel file."""
    executor = ActionExecutor()
    executor.execute_events_from_excel()


if __name__ == "__main__":
    main()
