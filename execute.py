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
            
            print(f"Executing {len(events)} events (including verification)...")
            
            # Execute each event
            success_count = 0
            verification_passed = None
            
            for i, event in enumerate(events, 1):
                operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
                
                print(f"\n--- Executing Event {i}/{len(events)} ---")
                print(f"Step: {event.step_number}")
                print(f"Operation: {operation_name}")
                print(f"URL: {event.url}")
                print(f"Component: {event.html_component}")
                if event.input_text:
                    print(f"Input: {event.input_text}")
                
                try:
                    self._execute_single_event(event)
                    success_count += 1
                    
                    # Track if this was verification event
                    if operation_name == "verify_element":
                        verification_passed = True
                        print(f"✅ Event {i} (VERIFICATION) passed!")
                    else:
                        print(f"✅ Event {i} executed successfully")
                        
                except Exception as e:
                    print(f"❌ Event {i} failed: {e}")
                    
                    # If verification fails, mark it
                    if operation_name == "verify_element":
                        verification_passed = False
                    
                    # Continue with next event
                    continue
                
                time.sleep(1)
            
            # Check results
            all_passed = success_count == len(events)
            
            print(f"\n{'='*80}")
            print(f"🎯 EXECUTION SUMMARY")
            print(f"{'='*80}")
            print(f"   Total Events: {len(events)}")
            print(f"   Successful: {success_count}")
            print(f"   Failed: {len(events) - success_count}")
            
            if verification_passed is not None:
                if verification_passed:
                    print(f"   ✅ VERIFICATION: PASSED")
                else:
                    print(f"   ❌ VERIFICATION: FAILED")
            
            if all_passed:
                print(f"\n✅ ALL EVENTS INCLUDING VERIFICATION PASSED!")
            else:
                print(f"\n⚠️ SOME EVENTS FAILED")
            print(f"{'='*80}")
            
            # Keep browser open briefly
            if not headless:
                wait_time = 5 if verification_passed else 3
                print(f"\nBrowser will close in {wait_time} seconds...")
                time.sleep(wait_time)
            
            return all_passed
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            return False
        finally:
            self._cleanup()


    
    def _execute_single_event(self, event: Event):
        """Execute a single event."""
        # Get operation name first
        operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
        print(f"Operation: {operation_name}")
        
        # Navigate to URL if specified (but NOT for verify_element)
        if event.url and operation_name != "verify_element":
            current_url = self.page.url
            if not self._is_same_url(current_url, event.url):
                print(f"Navigating to: {event.url}")
                self.page.goto(event.url)
                self.page.wait_for_load_state("networkidle")
            else:
                print(f"Already on {event.url}, skipping navigation")
        elif operation_name == "verify_element":
            print(f"Verification on current page: {self.page.url}")
        
        # Execute based on operation type
        if operation_name == "click":
            self._perform_click(event)
        elif operation_name == "input_text":
            self._perform_input_text(event)
        elif operation_name == "scroll":
            self._perform_scroll(event)
        elif operation_name == "verify_element":
            self._perform_verify_element(event)


    
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
    def _perform_verify_element(self, event: Event):
        """
        Perform element verification operation.
        Checks if specified element exists and is visible.
        """
        if not event.html_component:
            raise ValueError("HTML component is required for verify_element operation")
        
        verification_desc = event.input_text or "Verification element"
        print(f"Verifying element: {event.html_component}")
        print(f"Description: {verification_desc}")
        
        try:
            # Wait for page to stabilize
            self.page.wait_for_load_state('networkidle')
            time.sleep(1)
            
            # Try to locate the element
            locator = self.page.locator(event.html_component)
            
            # Check if element exists and is visible
            if locator.count() > 0:
                if locator.first.is_visible():
                    print(f"✅ Verification PASSED - Element found and visible!")
                    return
                else:
                    raise Exception(f"Verification FAILED - Element exists but not visible")
            else:
                raise Exception(f"Verification FAILED - Element not found")
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            raise Exception(f"Element verification failed: {e}")


    
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
    Convenience function to execute events.
    
    Returns:
        bool: True if all events (including verification) passed
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
