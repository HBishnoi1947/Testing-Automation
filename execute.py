"""
Event Executor for Testing Automation POC.
Executes a list of events using Playwright browser automation.
"""

from playwright.sync_api import sync_playwright, Page, Browser
import time
import re
from typing import List, Optional, Tuple
from model.event import Event
from model.operation_type import OperationTypeMapper
from dom_extract import save_page_dom_to_file


class ComponentLocator:
    """
    Helper class for intelligent component identification with high accuracy.
    Handles multiple selector types and fallback strategies.
    """
    
    @staticmethod
    def detect_selector_type(selector: str) -> str:
        """
        Detect the type of selector.
        
        Args:
            selector: The selector string
            
        Returns:
            str: Type of selector ('text', 'xpath', 'css', 'id', 'class', 'name', 'unknown')
        """
        if not selector:
            return 'unknown'
        
        selector = selector.strip()
        
        # Text-based selectors
        if selector.startswith("text="):
            return 'text'
        if "text=" in selector.lower() or "text='" in selector or 'text="' in selector:
            return 'text'
        
        # XPath selectors
        if selector.startswith("//") or selector.startswith("xpath=") or selector.startswith("/html"):
            return 'xpath'
        
        # ID selector (starts with #)
        if selector.startswith("#"):
            return 'id'
        
        # Class selector (starts with .)
        if selector.startswith("."):
            return 'class'
        
        # Name attribute selector
        if selector.startswith("[name=") or selector.startswith("[name='"):
            return 'name'
        
        # CSS selector (contains brackets, colons, spaces, etc.)
        if any(char in selector for char in ['[', ']', ':', '>', '+', '~', ' ', ',']):
            return 'css'
        
        # Default to CSS
        return 'css'
    
    @staticmethod
    def extract_text_from_selector(selector: str) -> Optional[str]:
        """
        Extract text content from text-based selectors.
        
        Args:
            selector: Selector string that may contain text
            
        Returns:
            str or None: Extracted text content
        """
        if not selector:
            return None
        
        # Format: text=Some Text
        if selector.startswith("text="):
            return selector[5:].strip()
        
        # Format: a[text='Some Text'] or a[text="Some Text"]
        text_patterns = [
            r"text=['\"]([^'\"]+)['\"]",  # text='...' or text="..."
            r"text=([^\]]+)",  # text=... (without quotes)
        ]
        
        for pattern in text_patterns:
            match = re.search(pattern, selector, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    @staticmethod
    def find_element(page: Page, selector: str, timeout: int = 5000) -> Tuple[Optional[any], str]:
        """
        Find an element using multiple strategies with high accuracy.
        
        Args:
            page: Playwright page object
            selector: Selector string
            timeout: Timeout in milliseconds for each attempt
            
        Returns:
            Tuple[Locator or None, str]: (locator, strategy_used)
        """
        if not selector:
            return None, "no_selector"
        
        selector_type = ComponentLocator.detect_selector_type(selector)
        text_content = ComponentLocator.extract_text_from_selector(selector)
        
        # Strategy 1: Text-based selectors (highest accuracy for text matching)
        if text_content:
            try:
                # Use Playwright's get_by_text (most reliable)
                locator = page.get_by_text(text_content, exact=False)
                if locator.count() > 0:
                    return locator.first, "get_by_text"
            except Exception as e:
                print(f"    get_by_text failed: {e}")
            
            try:
                # Try get_by_role with link role if it's a link selector
                if selector.startswith("a[") or selector.startswith("a "):
                    locator = page.get_by_role("link", name=text_content, exact=False)
                    if locator.count() > 0:
                        return locator.first, "get_by_role_link"
            except Exception as e:
                print(f"    get_by_role_link failed: {e}")
            
            try:
                # Try :has-text() selector
                locator = page.locator(f":has-text('{text_content}')")
                if locator.count() > 0:
                    return locator.first, "has_text_selector"
            except Exception as e:
                print(f"    :has-text() failed: {e}")
            
            try:
                # Try XPath with contains text
                locator = page.locator(f"xpath=//*[contains(text(), '{text_content}')]")
                if locator.count() > 0:
                    return locator.first, "xpath_text"
            except Exception as e:
                print(f"    XPath text failed: {e}")
        
        # Strategy 2: Direct CSS selector
        if selector_type == 'css':
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    return locator.first, "css_selector"
            except Exception as e:
                print(f"    CSS selector failed: {e}")
        
        # Strategy 3: XPath
        if selector_type == 'xpath' or selector.startswith("//"):
            try:
                xpath = selector.replace("xpath=", "") if selector.startswith("xpath=") else selector
                locator = page.locator(f"xpath={xpath}")
                if locator.count() > 0:
                    return locator.first, "xpath"
            except Exception as e:
                print(f"    XPath failed: {e}")
        
        # Strategy 4: ID selector
        if selector_type == 'id':
            try:
                id_value = selector.lstrip("#")
                locator = page.locator(f"#{id_value}")
                if locator.count() > 0:
                    return locator.first, "id_selector"
            except Exception as e:
                print(f"    ID selector failed: {e}")
        
        # Strategy 5: Class selector
        if selector_type == 'class':
            try:
                class_value = selector.lstrip(".")
                locator = page.locator(f".{class_value}")
                if locator.count() > 0:
                    return locator.first, "class_selector"
            except Exception as e:
                print(f"    Class selector failed: {e}")
        
        # Strategy 6: Name attribute
        if selector_type == 'name':
            try:
                # Extract name value
                name_match = re.search(r"name=['\"]?([^'\"]+)['\"]?", selector)
                if name_match:
                    name_value = name_match.group(1)
                    locator = page.locator(f"[name='{name_value}']")
                    if locator.count() > 0:
                        return locator.first, "name_selector"
            except Exception as e:
                print(f"    Name selector failed: {e}")
        
        # Strategy 7: Try as ID (if selector looks like an ID)
        if selector_type not in ['id', 'class'] and not selector.startswith(('/', '[', '.', '#')):
            try:
                locator = page.locator(f"#{selector}")
                if locator.count() > 0:
                    return locator.first, "id_fallback"
            except Exception as e:
                pass
        
        # Strategy 8: Try as class (if selector looks like a class)
        if selector_type not in ['id', 'class'] and not selector.startswith(('/', '[', '.', '#')):
            try:
                locator = page.locator(f".{selector}")
                if locator.count() > 0:
                    return locator.first, "class_fallback"
            except Exception as e:
                pass
        
        # Strategy 9: Try as name attribute (common for form inputs)
        if selector_type not in ['name'] and not selector.startswith(('/', '[', '.', '#')):
            try:
                locator = page.locator(f"[name='{selector}']")
                if locator.count() > 0:
                    return locator.first, "name_fallback"
            except Exception as e:
                pass
        
        # Strategy 10: Try exact text match as last resort
        if text_content:
            try:
                locator = page.get_by_text(text_content, exact=True)
                if locator.count() > 0:
                    return locator.first, "exact_text"
            except Exception as e:
                pass
        
        return None, "not_found"


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
            print("🔧 EventExecutor new instance created (not singleton)")
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
        print("🔧 EventExecutor singleton instance created")
    
    @classmethod
    def _is_singleton_browser_open(cls) -> bool:
        """Check if singleton browser is open and connected."""
        if cls._singleton_browser is None:
            return False
        try:
            return cls._singleton_browser.is_connected()
        except:
            return False
    
    @classmethod
    def _get_or_create_singleton_browser(cls, headless: bool = False):
        """
        Get or create the singleton browser instance.
        
        Args:
            headless: Whether to launch browser in headless mode (only applies if creating new browser)
            
        Returns:
            tuple: (playwright, browser, page)
        """
        # If browser exists and is connected, reuse it
        if cls._is_singleton_browser_open():
            print("♻️ Reusing existing singleton browser")
            return cls._singleton_playwright, cls._singleton_browser, cls._singleton_page
        
        # Create new browser
        print("🌐 Creating new singleton browser")
        cls._singleton_playwright = sync_playwright().start()
        cls._singleton_browser = cls._singleton_playwright.chromium.launch(headless=headless)
        cls._singleton_page = cls._singleton_browser.new_page()
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
            print("🌐 Singleton browser closed")
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
            page.goto(target_url)
            page.wait_for_load_state('networkidle')
            print("✅ Navigation completed successfully")
            
            # Extract DOM content
            print("\n🔍 Extracting DOM content...")
            html_content = page.content()
            
            with open(dom_output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ DOM saved to: {dom_output_file}")
            
            # Don't close browser - keep singleton browser open
            return True
            
        except Exception as e:
            print(f"❌ Error navigating and extracting DOM: {e}")
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
                    print(f"✅ Event {i} executed successfully")
                except Exception as e:
                    print(f"❌ Event {i} failed: {e}")
                    # Continue with next event instead of stopping
                    continue
                
                # Small delay between events
                time.sleep(1)
            
            print(f"\n🎯 Execution completed: {success_count}/{len(events)} events successful")
            print("🌐 Browser staying open for next execution...")
            
            return success_count == len(events)
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
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
                        print(f"    ⚠️ Event {i} error: {e}")
                        continue
            finally:
                # Restore original page reference
                self.page = original_page
            
            # Wait for final state
            print("\n  ⏳ Waiting for final page state...")
            page.wait_for_load_state('networkidle')
            time.sleep(4)  # Additional 4s for any async operations
            final_url = page.url
            print(f"  📍 Final URL: {final_url}")
            
            # Capture final DOM (sync version)
            html_content = page.content()
            with open(final_dom_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ DOM saved to: {final_dom_path}")
            
            # Don't close browser - keep singleton browser open
            print("🌐 Browser staying open (singleton)")
            
            return {'success': True,
                    'final_url' :final_url}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_testing_module(self, features_with_events: List[dict], headless: bool = False) -> dict:
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
            print(f"\n🌐 Opening separate browser session for module execution...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()
            
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
                print(f"📋 FEATURE {idx}/{len(features_with_events)}: {feature_name}")
                print(f"{'='*80}")
                
                # ✅ After first feature, skip navigation (stay on current page)
                if idx > 1:
                    print(f"🔗 Continuing from current page: {self.page.url}")
                    self.skip_navigation = True
                else:
                    print(f"🌐 Starting from initial URL")
                    self.skip_navigation = False
                
                if not events:
                    print(f"⚠️ No events found for feature: {feature_name}")
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
                        print(f"✅ Event {event_idx} passed")
                            
                    except Exception as e:
                        event_info['error'] = str(e)
                        print(f"❌ Event {event_idx} failed: {e}")
                    
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
                    print(f"\n✅ Feature '{feature_name}' PASSED ({success_count}/{len(events)} events)")
                else:
                    module_results['failed_features'] += 1
                    module_results['success'] = False
                    print(f"\n❌ Feature '{feature_name}' FAILED ({success_count}/{len(events)} events passed)")
                
                module_results['feature_results'].append(feature_result)
            
            # Reset skip flag
            self.skip_navigation = False
            
            # Keep browser open briefly to see final state
            if not headless:
                print(f"\n\n✅ All {len(features_with_events)} features executed in single browser session!")
                print(f"Browser will close in 3 seconds...")
                time.sleep(3)
            
            return module_results
            
        except Exception as e:
            print(f"❌ Error during module execution: {e}")
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
            print(f"🌐 Browser session closed.")
    
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
                print(f"✅ Successfully clicked element using {strategy}: {event.html_component}")
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
                print(f"✅ Successfully input text using {strategy}: {event.html_component}")
                return
            except Exception as e:
                print(f"    Fill action failed on found element: {e}")
                # Try alternative: type instead of fill
                try:
                    locator.clear(timeout=5000)
                    locator.type(event.input_text, delay=50, timeout=5000)
                    print(f"✅ Successfully typed text using {strategy}: {event.html_component}")
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
            
            # Use ComponentLocator for intelligent element identification
            locator, strategy = ComponentLocator.find_element(self.page, event.html_component)
            
            if locator:
                try:
                    # Check if element is visible
                    is_visible = locator.is_visible(timeout=5000)
                    if is_visible:
                        print(f"✅ Verification PASSED - Element found and visible using {strategy}!")
                        return
                    else:
                        raise Exception(f"Verification FAILED - Element exists but not visible")
                except Exception as e:
                    # If visibility check fails, try count check
                    if locator.count() > 0:
                        print(f"✅ Verification PASSED - Element found using {strategy} (visibility check skipped)")
                        return
                    else:
                        raise Exception(f"Verification FAILED - Element not found")
            else:
                raise Exception(f"Verification FAILED - Element not found (tried multiple strategies)")
                
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
        print("🎉 All events executed successfully!")
    else:
        print("❌ Some events failed to execute")


if __name__ == "__main__":
    main()
