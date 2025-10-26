"""
Event Executor for Testing Automation POC.
Executes a list of events using Playwright browser automation.
"""

from playwright.sync_api import sync_playwright, Page, Browser
import time
from typing import List, Optional
from model.event import Event
from model.operation_type import OperationTypeMapper


class EventExecutor:
    """Executes a list of events using Playwright browser automation."""
    
    def __init__(self, db_path: str = "database.db"):
        """Initialize the executor with database path."""
        self.playwright = None
        self.browser = None
        self.page = None
        self.db_path = db_path
        self.operation_mapper = OperationTypeMapper(db_path)
        self.operation_mapper.load_operation_types()
    
    def execute_events(self, events: List[Event], headless: bool = False) -> bool:
        """
        Execute a list of events in sequence.
        
        Args:
            events: List of Event objects to execute
            headless: Whether to run browser in headless mode
            
        Returns:
            bool: True if all events executed successfully, False otherwise
        """
        if not events:
            print("No events to execute")
            return False
        
        try:
            # Initialize Playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()
            
            # Sort events by step number
            sorted_events = sorted(events, key=lambda x: x.step_number)
            
            print(f"Executing {len(sorted_events)} events...")
            
            # Execute each event
            success_count = 0
            for i, event in enumerate(sorted_events, 1):
                print(f"\n--- Executing Event {i}/{len(sorted_events)} ---")
                print(f"Step: {event.step_number}")
                print(f"URL: {event.url}")
                print(f"Component: {event.html_component}")
                print(f"Input: {event.input_text}")
                
                try:
                    self._execute_single_event(event)
                    success_count += 1
                    print(f"✅ Event {i} executed successfully")
                except Exception as e:
                    print(f"❌ Event {i} failed: {e}")
                    # Continue with next event instead of stopping
                    continue
                
                # Small delay between events
                time.sleep(1)
            
            print(f"\n🎯 Execution completed: {success_count}/{len(sorted_events)} events successful")
            
            # Keep browser open for a moment to see results
            if not headless:
                print("Browser will close in 3 seconds...")
                time.sleep(3)
            
            return success_count == len(sorted_events)
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            return False
        finally:
            self._cleanup()
    
    def _execute_single_event(self, event: Event):
        """Execute a single event."""
        # Navigate to URL if specified
        if event.url:
            current_url = self.page.url
            if not self._is_same_url(current_url, event.url):
                print(f"Navigating to: {event.url}")
                self.page.goto(event.url)
                self.page.wait_for_load_state("networkidle")
            else:
                print(f"Already on {event.url}, skipping navigation")
        
        # Get operation name
        operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
        print(f"Operation: {operation_name}")
        
        # Execute based on operation type
        if operation_name == "click":
            self._perform_click(event)
        elif operation_name == "input_text":
            self._perform_input_text(event)
        elif operation_name == "scroll":
            self._perform_scroll(event)
        else:
            print(f"Unknown operation type: {operation_name}")
            raise ValueError(f"Unknown operation type: {operation_name}")
    
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
    
    def _perform_click(self, event: Event):
        """Perform click operation on the specified HTML component."""
        if not event.html_component:
            raise ValueError("HTML component is required for click operation")
        
        print(f"Clicking element: {event.html_component}")
        
        # Try different locator strategies
        locator = None
        
        # Try as CSS selector first (most common)
        try:
            locator = self.page.locator(event.html_component)
            if locator.count() > 0:
                locator.click()
                print(f"✅ Successfully clicked element: {event.html_component}")
                return
        except Exception as e:
            print(f"CSS selector failed: {e}")
        
        # Try as XPath
        try:
            locator = self.page.locator(f"xpath={event.html_component}")
            if locator.count() > 0:
                locator.click()
                print(f"✅ Successfully clicked element: {event.html_component}")
                return
        except Exception as e:
            print(f"XPath failed: {e}")
        
        # Try as ID selector
        try:
            locator = self.page.locator(f"#{event.html_component}")
            if locator.count() > 0:
                locator.click()
                print(f"✅ Successfully clicked element: {event.html_component}")
                return
        except Exception as e:
            print(f"ID selector failed: {e}")
        
        # Try as class selector
        try:
            locator = self.page.locator(f".{event.html_component}")
            if locator.count() > 0:
                locator.click()
                print(f"✅ Successfully clicked element: {event.html_component}")
                return
        except Exception as e:
            print(f"Class selector failed: {e}")
        
        raise Exception(f"Could not find clickable element: {event.html_component}")
    
    def _perform_input_text(self, event: Event):
        """Perform input text operation."""
        if not event.html_component:
            raise ValueError("HTML component is required for input_text operation")
        if not event.input_text:
            raise ValueError("Input text is required for input_text operation")
        
        print(f"Inputting text '{event.input_text}' into: {event.html_component}")
        
        # Try different locator strategies
        locator = None
        
        # Try as CSS selector first (most common)
        try:
            locator = self.page.locator(event.html_component)
            if locator.count() > 0:
                locator.fill(event.input_text)
                print(f"✅ Successfully input text into: {event.html_component}")
                return
        except Exception as e:
            print(f"CSS selector failed: {e}")
        
        # Try as XPath
        try:
            locator = self.page.locator(f"xpath={event.html_component}")
            if locator.count() > 0:
                locator.fill(event.input_text)
                print(f"✅ Successfully input text into: {event.html_component}")
                return
        except Exception as e:
            print(f"XPath failed: {e}")
        
        # Try as ID selector
        try:
            locator = self.page.locator(f"#{event.html_component}")
            if locator.count() > 0:
                locator.fill(event.input_text)
                print(f"✅ Successfully input text into: {event.html_component}")
                return
        except Exception as e:
            print(f"ID selector failed: {e}")
        
        # Try as class selector
        try:
            locator = self.page.locator(f".{event.html_component}")
            if locator.count() > 0:
                locator.fill(event.input_text)
                print(f"✅ Successfully input text into: {event.html_component}")
                return
        except Exception as e:
            print(f"Class selector failed: {e}")
        
        # Try as name attribute
        try:
            locator = self.page.locator(f"[name='{event.html_component}']")
            if locator.count() > 0:
                locator.fill(event.input_text)
                print(f"✅ Successfully input text into: {event.html_component}")
                return
        except Exception as e:
            print(f"Name selector failed: {e}")
        
        raise Exception(f"Could not find input element: {event.html_component}")
    
    def _perform_scroll(self, event: Event):
        """Perform scroll operation."""
        print(f"Scrolling: {event.html_component}")
        
        try:
            if event.html_component:
                # Try to scroll to specific element
                try:
                    locator = self.page.locator(event.html_component)
                    if locator.count() > 0:
                        locator.scroll_into_view_if_needed()
                        print(f"✅ Successfully scrolled to element: {event.html_component}")
                        return
                except Exception as e:
                    print(f"Element scroll failed: {e}")
                
                # Try scroll directions
                if event.html_component.lower() == "down":
                    self.page.evaluate("window.scrollBy(0, 500);")
                    print("✅ Scrolled down")
                    return
                elif event.html_component.lower() == "up":
                    self.page.evaluate("window.scrollBy(0, -500);")
                    print("✅ Scrolled up")
                    return
                elif event.html_component.lower() == "top":
                    self.page.evaluate("window.scrollTo(0, 0);")
                    print("✅ Scrolled to top")
                    return
                elif event.html_component.lower() == "bottom":
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    print("✅ Scrolled to bottom")
                    return
            
            # Default scroll down
            self.page.evaluate("window.scrollBy(0, 500);")
            print("✅ Scrolled down (default)")
            
        except Exception as e:
            raise Exception(f"Error scrolling: {e}")
    
    def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")


def execute_events(events: List[Event], headless: bool = False) -> bool:
    """
    Convenience function to execute a list of events.
    
    Args:
        events: List of Event objects to execute
        headless: Whether to run browser in headless mode
        
    Returns:
        bool: True if all events executed successfully, False otherwise
    """
    executor = EventExecutor()
    return executor.execute_events(events, headless)


def main():
    """Main function for testing."""
    from model.database import get_all_events_from_sqlite
    
    # Get all events from database
    events = get_all_events_from_sqlite()
    print(f"Loaded {len(events)} events from database")
    
    # Execute events
    success = execute_events(events, headless=False)
    
    if success:
        print("🎉 All events executed successfully!")
    else:
        print("❌ Some events failed to execute")


if __name__ == "__main__":
    main()
