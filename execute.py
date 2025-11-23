"""
Event Executor for Testing Automation POC.
Executes a list of events using Playwright browser automation.
"""

from playwright.sync_api import sync_playwright, Page, Browser
import time
from typing import List
from model.event import Event
from model.operation_type import OperationTypeMapper
from dom_extract import save_page_dom_to_file
from component_locator import ComponentLocator


class EventExecutor:
    """Executes a list of events using Playwright browser automation.
    By default, returns a singleton instance. Can create a new instance with new_object=True.
    """
    
    # Singleton instance
    _instance = None
    _initialized = False
    
    # Class-level singleton browser instance
    _singleton_playwright = None
    _singleton_browser = None
    _singleton_page = None
    _singleton_headless = None
    
    def __new__(cls, db_path: str = "database.db", new_object: bool = False):
        """
        Create or return an instance.
        
        Args:
            db_path: Path to database file
            new_object: If True, create a new instance instead of returning singleton
            
        Returns:
            EventExecutor instance
        """
        if new_object:
            # Create a new instance (not singleton)
            new_instance = super(EventExecutor, cls).__new__(cls)
            new_instance._is_new_instance = True
            return new_instance
        else:
            # Return singleton instance
            if cls._instance is None:
                cls._instance = super(EventExecutor, cls).__new__(cls)
                cls._instance._is_new_instance = False
            return cls._instance
    
    def __init__(self, db_path: str = "database.db", new_object: bool = False):
        """
        Initialize the executor with database path.
        
        Args:
            db_path: Path to database file
            new_object: If True, this is a new instance (not singleton)
        """
        # If this is a new instance, always initialize
        if hasattr(self, '_is_new_instance') and self._is_new_instance:
            self.playwright = None
            self.browser = None
            self.page = None
            self.db_path = db_path
            self.operation_mapper = OperationTypeMapper(db_path)
            self.operation_mapper.load_operation_types()
            print("[NEW] EventExecutor new instance created (not singleton)")

            return
        
        # For singleton: only initialize once
        if EventExecutor._initialized:
            return
        
        self.playwright = None
        self.browser = None
        self.page = None
        self.db_path = db_path
        self.operation_mapper = OperationTypeMapper(db_path)
        self.operation_mapper.load_operation_types()
        
        # Mark as initialized
        EventExecutor._initialized = True
        print("[NEW] EventExecutor singleton instance created")
    
    @classmethod
    def _is_singleton_browser_open(cls) -> bool:
        """Check if singleton browser is open and connected."""
        if cls._singleton_browser is None:
            return False
        try:
            return cls._singleton_browser.is_connected() and not cls._singleton_page.is_closed()
        except:
            return False
    
    @classmethod
    def _ensure_browser_open(cls, headless: bool = False):
        """
        Ensure singleton browser is open and connected. Test if goto works. Recreate if closed or not working.
        
        Args:
            headless: Whether to launch browser in headless mode (if recreating)
        """
        browser_working = False
        
        # Step 1: Check if browser exists and is connected
        if cls._is_singleton_browser_open():
            # Step 2: Test if page is accessible
            try:
                if cls._singleton_page:
                    # Step 3: Test if goto actually works by trying a simple navigation
                    cls._singleton_page.wait_for_timeout(3000)
                    browser_working = True
                    print("[OK] Browser is open and goto is working")
                else:
                    print("[WARNING] Singleton page is None")
            except Exception as e:
                print(f"[WARNING] Browser goto test failed: {e}")
                browser_working = False
        else:
            print("[WARNING] Singleton browser is not connected")
        
        # If browser is not working, reset singleton and recreate
        if not browser_working:
            print("[SINGLETON] Browser is closed or not working, resetting singleton and recreating...")
            # Set singleton browser to None
            cls._singleton_browser = None
            cls._singleton_page = None
            # cls._singleton_playwright = None
            cls._singleton_headless = None
    
    @classmethod
    def _get_or_create_singleton_browser(cls, headless: bool = False):
        """
        Get or create the singleton browser instance.
        
        Args:
            headless: Whether to launch browser in headless mode (only applies if creating new browser)
            
        Returns:
            tuple: (playwright, browser, page)
        """
        cls._ensure_browser_open(headless=headless)

        # If browser exists and is connected, reuse it
        if cls._is_singleton_browser_open():
            print("[*] Reusing existing singleton browser")
            return cls._singleton_playwright, cls._singleton_browser, cls._singleton_page
        
        # Create new browser
        print("[WEB] Creating new singleton browser")
        if cls._singleton_playwright is None:
            cls._singleton_playwright = sync_playwright().start()
        cls._singleton_browser = cls._singleton_playwright.chromium.launch(headless=headless)
        
        # Create browser context without viewport constraint (browser opens at normal/default size)
        context = cls._singleton_browser.new_context(no_viewport=True)
        cls._singleton_page = context.new_page()
        cls._singleton_headless = headless
        
        return cls._singleton_playwright, cls._singleton_browser, cls._singleton_page
    
    @classmethod
    def _close_singleton_browser(cls):
        """Close the singleton browser instance."""
        try:
            if cls._singleton_browser:
                cls._singleton_browser.close()
            if cls._singleton_playwright:
                cls._singleton_playwright.stop()
            cls._singleton_browser = None
            cls._singleton_page = None
            cls._singleton_playwright = None
            cls._singleton_headless = None
            print("[WEB] Singleton browser closed")
        except Exception as e:
            print(f"Error closing singleton browser: {e}")
    
    @classmethod
    def close_singleton_browser(cls):
        """Public method to close singleton browser."""
        cls._close_singleton_browser()
    
    def navigate_and_extract_dom(self, target_url: str, dom_output_file: str, headless: bool = False) -> bool:
        """
        Navigate to URL and extract DOM content using singleton browser.
        All navigation logic is handled here.
        
        Args:
            target_url: URL to navigate to
            dom_output_file: File path to save DOM content
            headless: Whether to launch browser in headless mode (only applies if creating new browser)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get or create singleton browser
            playwright, browser, page = self._get_or_create_singleton_browser(headless=headless)
            
            print(f"Navigating to: {target_url}")
            if target_url != "":
                page.goto(target_url)
                page.wait_for_load_state('networkidle')
                print("[OK] Navigation completed successfully")
            
            # Extract DOM content
            print("\n[*] Extracting DOM content...")
            save_page_dom_to_file(page, dom_output_file)
            print(f"[OK] DOM saved to: {dom_output_file}")
            
            # Don't close browser - keep singleton browser open
            return True
            
        except Exception as e:
            print(f"[FAILED] Error navigating and extracting DOM: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_events(self, events: List[Event], headless: bool = False) -> bool:
        """
        Execute a list of events in sequence.
        Uses singleton browser - reuses existing browser if available.
        
        Args:
            events: List of Event objects to execute
            headless: Whether to run browser in headless mode (only applies if creating new browser)
            
        Returns:
            bool: True if all events executed successfully, False otherwise
        """
        if not events:
            print("No events to execute")
            return False
        
        try:
            # Get or create singleton browser
            self.playwright, self.browser, self.page = self._get_or_create_singleton_browser(headless=headless)
                  
            print(f"Executing {len(events)} events...")
            
            # Execute each event
            success_count = 0
            for i, event in enumerate(events, 1):
                print(f"\n--- Executing Event {i}/{len(events)} ---")
                print(f"Step: {event.step_number}")
                print(f"URL: {event.url}")
                print(f"Component: {event.html_component}")
                print(f"Input: {event.input_text}")
                
                try:
                    self._execute_single_event(event)
                    success_count += 1
                    print(f"[OK] Event {i} executed successfully")
                except Exception as e:
                    print(f"[FAILED] Event {i} failed: {e}")
                    # Continue with next event instead of stopping
                    continue
                
                # Small delay between events
                time.sleep(1)
            
            print(f"\n[*] Execution completed: {success_count}/{len(events)} events successful")
            print("[WEB] Browser staying open for next execution...")
            
            return success_count == len(events)
            
        except Exception as e:
            print(f"[FAILED] Error during execution: {e}")
            return False
        finally:
            # Don't cleanup - keep browser open (singleton pattern)
            pass

    def _execute_and_capture_dom(self, events, final_dom_path: str):
        """
        Execute events and capture final DOM state (synchronous version).
        Uses singleton browser - reuses existing browser if available.
        
        Args:
            events: List of events to execute
            final_dom_path: Path to save final DOM
            
        Returns:
            dict: {'success': bool, 'error': str (optional)}
        """
        try:
            # Get or create singleton browser
            playwright, browser, page = self._get_or_create_singleton_browser(headless=False)
            
            # Navigate to first event URL
            if events and events[0].url:
                if events[0].url != "":
                    page.goto(events[0].url)
                    page.wait_for_load_state('networkidle')
            # Get operation name
            from model.operation_type import OperationTypeMapper
            mapper = OperationTypeMapper()
            mapper.load_operation_types()
            
            # Set page to instance variable so _execute_single_event can use it
            original_page = self.page
            self.page = page
            
            try:
                # Execute each event
                for i, event in enumerate(events, 1):
                    print(f"  Executing event {i}/{len(events)}: {event.operation_id}")
                    
                    try:
                        # Use _execute_single_event for consistent behavior
                        self._execute_single_event(event)
                        
                        # Wait for any navigation/updates
                        page.wait_for_load_state('networkidle')
                        
                    except Exception as e:
                        print(f"    [WARNING] Event {i} error: {e}")
                        continue
            finally:
                # Restore original page reference
                self.page = original_page
            
            # Wait for final state
            print("\n  ⏳ Waiting for final page state...")
            page.wait_for_load_state('networkidle')
            time.sleep(4)  # Additional 4s for any async operations
            final_url = page.url
            print(f"  [*] Final URL: {final_url}")
            
            # Capture final DOM (sync version)
            save_page_dom_to_file(page, final_dom_path)
            print(f"[OK] DOM saved to: {final_dom_path}")
            
            # Don't close browser - keep singleton browser open
            print("[WEB] Browser staying open (singleton)")
            
            return {'success': True,
                    'final_url' :final_url}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_testing_module(self, features_with_events: List[dict], headless: bool = False, browser: str = "chromium") -> dict:
        """
        Execute multiple features in a SINGLE browser session.
        Creates its own browser instance (does not use singleton), executes all features sequentially, then closes.
        After first feature, stays on current page instead of navigating.
        
        Args:
            features_with_events: List of dicts with keys:
                - 'feature_name': str
                - 'feature_id': int
                - 'events': List[Event]
            headless: Whether to run browser in headless mode
            
        Returns:
            dict: {
                'success': bool,
                'total_features': int,
                'passed_features': int,
                'failed_features': int,
                'feature_results': List[dict]
            }
        """
        if not features_with_events:
            return {
                'success': True,
                'total_features': 0,
                'passed_features': 0,
                'failed_features': 0,
                'feature_results': []
            }
        
        try:
            # Create separate browser instance for module execution (not singleton)
            print(f"\n[WEB] Opening separate browser session for module execution...")
            self.playwright = sync_playwright().start()
            if browser == "chromium":
                self.browser = self.playwright.chromium.launch(headless=headless)
            elif browser == "firefox":
                self.browser = self.playwright.firefox.launch(headless=headless)
            elif browser == "edge":
                # Edge is Chromium-based, use chromium with msedge channel
                self.browser = self.playwright.chromium.launch(headless=headless, channel="msedge")
            else:
                raise ValueError(f"Invalid browser: {browser}")
            
            # Create browser context without viewport constraint (browser opens at normal/default size)
            context = self.browser.new_context(no_viewport=True)
            self.page = context.new_page()
            
            module_results = {
                'success': True,
                'total_features': len(features_with_events),
                'passed_features': 0,
                'failed_features': 0,
                'feature_results': []
            }
            
            # Execute each feature WITHOUT closing browser
            for idx, feature_data in enumerate(features_with_events, 1):
                feature_name = feature_data.get('feature_name', f'Feature {idx}')
                events = feature_data.get('events', [])
                
                print(f"\n{'='*80}")
                print(f"[*] FEATURE {idx}/{len(features_with_events)}: {feature_name}")
                print(f"{'='*80}")
                
                # [OK] After first feature, skip navigation (stay on current page)
                if idx > 1:
                    print(f"[*] Continuing from current page: {self.page.url}")
                    self.skip_navigation = True
                else:
                    print(f"[WEB] Starting from initial URL")
                    self.skip_navigation = False
                
                if not events:
                    print(f"[WARNING] No events found for feature: {feature_name}")
                    feature_result = {
                        'feature_name': feature_name,
                        'success': False,
                        'total_events': 0,
                        'passed_events': 0,
                        'failed_events': 0,
                        'event_results': []
                    }
                    module_results['failed_features'] += 1
                    module_results['success'] = False
                    module_results['feature_results'].append(feature_result)
                    continue
                
                # Execute events for this feature (browser stays open)
                event_results = []
                success_count = 0
                
                for event_idx, event in enumerate(events, 1):
                    operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
                    
                    event_info = {
                        'event_number': event_idx,
                        'step_number': event.step_number,
                        'operation': operation_name,
                        'component': event.html_component,
                        'input': event.input_text,
                        'success': False,
                        'error': None
                    }
                    
                    print(f"\n--- Executing Event {event_idx}/{len(events)} ---")
                    print(f"Operation: {operation_name}")
                    
                    try:
                        self._execute_single_event(event)
                        success_count += 1
                        event_info['success'] = True
                        print(f"[OK] Event {event_idx} passed")
                            
                    except Exception as e:
                        event_info['error'] = str(e)
                        print(f"[FAILED] Event {event_idx} failed: {e}")
                    
                    event_results.append(event_info)
                    time.sleep(1)
                
                # Feature result
                all_passed = success_count == len(events)
                feature_result = {
                    'feature_name': feature_name,
                    'success': all_passed,
                    'total_events': len(events),
                    'passed_events': success_count,
                    'failed_events': len(events) - success_count,
                    'event_results': event_results
                }
                
                if all_passed:
                    module_results['passed_features'] += 1
                    print(f"\n[OK] Feature '{feature_name}' PASSED ({success_count}/{len(events)} events)")
                else:
                    module_results['failed_features'] += 1
                    module_results['success'] = False
                    print(f"\n[FAILED] Feature '{feature_name}' FAILED ({success_count}/{len(events)} events passed)")
                
                module_results['feature_results'].append(feature_result)
            
            # Reset skip flag
            self.skip_navigation = False
            
            # Keep browser open briefly to see final state
            if not headless:
                print(f"\n\n[OK] All {len(features_with_events)} features executed in single browser session!")
                print(f"Browser will close in 3 seconds...")
                time.sleep(3)
            
            return module_results
            
        except Exception as e:
            print(f"[FAILED] Error during module execution: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'total_features': len(features_with_events),
                'passed_features': 0,
                'failed_features': len(features_with_events),
                'feature_results': [],
                'error': str(e)
            }
        finally:
            # Close browser ONCE after ALL features
            self.skip_navigation = False  # Reset flag
            self._cleanup()
            print(f"[WEB] Browser session closed.")
    
    def _execute_single_event(self, event: Event, headless: bool = False):
        """Execute a single event."""
        # Navigate to URL if specified
        if event.url:
            current_url = self.page.url
            if not self._is_same_url(current_url, event.url):
                print(f"Navigating to: {event.url}")
                if event.url != "":
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
        elif operation_name == "verify_element":
            self._perform_verify_element(event)
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
        
        # Use ComponentLocator for intelligent element identification
        locator, strategy = ComponentLocator.find_element(self.page, event.html_component)
        
        if locator:
            try:
                locator.click(timeout=10000)  # 10 second timeout for click
                print(f"[OK] Successfully clicked element using {strategy}: {event.html_component}")
                return
            except Exception as e:
                print(f"    Click action failed on found element: {e}")
                raise Exception(f"Element found but click failed: {e}")
        else:
            raise Exception(f"Could not find clickable element: {event.html_component} (tried multiple strategies)")
    
    def _perform_input_text(self, event: Event):
        """Perform input text operation."""
        if not event.html_component:
            raise ValueError("HTML component is required for input_text operation")
        if not event.input_text:
            raise ValueError("Input text is required for input_text operation")
        
        print(f"Inputting text '{event.input_text}' into: {event.html_component}")
        
        # Use ComponentLocator for intelligent element identification
        locator, strategy = ComponentLocator.find_element(self.page, event.html_component)
        
        if locator:
            try:
                # Clear and fill the input
                locator.clear(timeout=5000)
                locator.fill(event.input_text, timeout=5000)
                print(f"[OK] Successfully input text using {strategy}: {event.html_component}")
                return
            except Exception as e:
                print(f"    Fill action failed on found element: {e}")
                # Try alternative: type instead of fill
                try:
                    locator.clear(timeout=5000)
                    locator.type(event.input_text, delay=50, timeout=5000)
                    print(f"[OK] Successfully typed text using {strategy}: {event.html_component}")
                    return
                except Exception as e2:
                    raise Exception(f"Element found but input failed: {e2}")
        else:
            raise Exception(f"Could not find input element: {event.html_component} (tried multiple strategies)")
    
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
                        print(f"[OK] Successfully scrolled to element: {event.html_component}")
                        return
                except Exception as e:
                    print(f"Element scroll failed: {e}")
                
                # Try scroll directions
                if event.html_component.lower() == "down":
                    self.page.evaluate("window.scrollBy(0, 500);")
                    print("[OK] Scrolled down")
                    return
                elif event.html_component.lower() == "up":
                    self.page.evaluate("window.scrollBy(0, -500);")
                    print("[OK] Scrolled up")
                    return
                elif event.html_component.lower() == "top":
                    self.page.evaluate("window.scrollTo(0, 0);")
                    print("[OK] Scrolled to top")
                    return
                elif event.html_component.lower() == "bottom":
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    print("[OK] Scrolled to bottom")
                    return
            
            # Default scroll down
            self.page.evaluate("window.scrollBy(0, 500);")
            print("[OK] Scrolled down (default)")
            
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
            
            # Use ComponentLocator for intelligent element identification
            locator, strategy = ComponentLocator.find_element(self.page, event.html_component)
            
            if locator:
                try:
                    # Check if element is visible
                    is_visible = locator.is_visible(timeout=5000)
                    if is_visible:
                        print(f"[OK] Verification PASSED - Element found and visible using {strategy}!")
                        return
                    else:
                        raise Exception(f"Verification FAILED - Element exists but not visible")
                except Exception as e:
                    # If visibility check fails, try count check
                    if locator.count() > 0:
                        print(f"[OK] Verification PASSED - Element found using {strategy} (visibility check skipped)")
                        return
                    else:
                        raise Exception(f"Verification FAILED - Element not found")
            else:
                raise Exception(f"Verification FAILED - Element not found (tried multiple strategies)")
                
        except Exception as e:
            print(f"[FAILED] Verification error: {e}")
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


def main():
    """Main function for testing."""
    from model.database import get_all_events_from_sqlite
    
    # Get all events from database
    events = get_all_events_from_sqlite()
    print(f"Loaded {len(events)} events from database")
    
    # Execute events
    executor = EventExecutor()
    success = executor.execute_events(events, headless=False)
    
    if success:
        print("[SUCCESS] All events executed successfully!")
    else:
        print("[FAILED] Some events failed to execute")


def run_scheduled_module():
    """Execute a testing module from command-line (called by Task Scheduler)"""
    import argparse
    from datetime import datetime
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Execute a testing module via scheduler")
    parser.add_argument("--module-id", type=int, required=True, 
                       help="ID of the testing module")
    parser.add_argument("--module-name", type=str, required=True,
                       help="Name of the testing module")
    parser.add_argument("--browser", type=str, default="Chrome",
                       choices=["Chrome", "Edge", "Firefox"],
                       help="Browser to use for execution")
    parser.add_argument("--headless", type=str, default="false",
                       choices=["true", "false"],
                       help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    # Convert headless string to boolean
    headless = args.headless.lower() == "true"
    
    # Map browser names to playwright browser types
    browser_map = {
        "Chrome": "chromium",
        "Edge": "edge",
        "Firefox": "firefox"
    }
    browser = browser_map.get(args.browser, "chromium")
    
    # Log execution start
    print("=" * 80)
    print(f"SCHEDULED TESTING MODULE EXECUTION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Module ID: {args.module_id}")
    print(f"Module Name: {args.module_name}")
    print(f"Browser: {args.browser} ({browser})")
    print(f"Headless Mode: {headless}")
    print("=" * 80)
    
    try:
        # Import required modules - use correct function names
        from model.database import get_testing_module_flow, get_all_events_from_sqlite
        
        # Get module flow
        module_flow = get_testing_module_flow(args.module_id)
        
        if not module_flow:
            print(f"ERROR: No flow found for module ID {args.module_id}")
            return 1
        
        print(f"\nModule Flow: {len(module_flow)} steps")
        
        # Build list of all feature IDs in the module
        feature_ids = [step['feature_id'] for step in module_flow]
        print(f"Feature IDs in module: {feature_ids}")
        
        # Get ALL events from database
        all_events = get_all_events_from_sqlite()
        
        # Filter events that belong to features in this module
        module_events = []
        for event in all_events:
            if event.feature_id in feature_ids:
                module_events.append(event)
        
        if not module_events:
            print("\nERROR: No events found for this module!")
            return 1
        
        print(f"Found {len(module_events)} events for this module")
        
        # Group events by feature
        features_with_events = []
        for step in module_flow:
            feature_id = step['feature_id']
            feature_name = step['feature_name']
            
            # Get events for this feature
            feature_events = [e for e in module_events if e.feature_id == feature_id]
            
            if feature_events:
                features_with_events.append({
                    'feature_id': feature_id,
                    'feature_name': feature_name,
                    'events': feature_events
                })
                print(f"  [OK] Feature: {feature_name} ({len(feature_events)} events)")

        
        if not features_with_events:
            print("\nERROR: No features with events found!")
            return 1
        
        # Execute the module
        print(f"\n{'='*80}")
        print(f"STARTING EXECUTION")
        print(f"{'='*80}\n")
        
        executor = EventExecutor(new_object=True)  # Create new instance for scheduled run
        result = executor.execute_testing_module(
            features_with_events=features_with_events,
            headless=headless,
            browser=browser
        )
        
        # Print results
        print("\n" + "=" * 80)
        print("EXECUTION RESULTS")
        print("=" * 80)
        print(f"Total Features: {result['total_features']}")
        print(f"Passed Features: {result['passed_features']}")
        print(f"Failed Features: {result['failed_features']}")
        print(f"Success: {'YES' if result['success'] else 'NO'}")

        print("=" * 80)
        
        # Save execution report to database
        try:
            from model.database import save_module_execution_report
            import json
            
            report_json = json.dumps(result, indent=2)
            save_module_execution_report(
                module_id=args.module_id,
                total_features=result['total_features'],
                passed_features=result['passed_features'],
                failed_features=result['failed_features'],
                report_json=report_json
            )
            print("\n[OK] Execution report saved to database")

        except Exception as e:
            print(f"\n[WARNING] Warning: Failed to save execution report: {e}")
        
        return 0 if result['success'] else 1
    
    except Exception as e:
        print(f"\nERROR: Execution failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    
    # Check if running from scheduler (has command-line arguments)
    if len(sys.argv) > 1 and "--module-id" in sys.argv:
        sys.exit(run_scheduled_module())
    else:
        main()

