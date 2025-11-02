"""
Event Executor for Testing Automation POC.
Executes a list of events using Playwright browser automation.
"""

from playwright.sync_api import sync_playwright, Page, Browser
import time
from typing import List, Optional
from model.event import Event
from model.operation_type import OperationTypeMapper
from playwright.sync_api import sync_playwright







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
        self.skip_navigation = False
    
    # def execute_events(self, events: List[Event], headless: bool = False) -> bool:
    #     """
    #     Execute a list of events in sequence.
        
    #     Args:
    #         events: List of Event objects to execute
    #         headless: Whether to run browser in headless mode
            
    #     Returns:
    #         bool: True if all events executed successfully, False otherwise
    #     """
    #     if not events:
    #         print("No events to execute")
    #         return False
        
    #     try:
    #         # Initialize Playwright
    #         self.playwright = sync_playwright().start()
    #         self.browser = self.playwright.chromium.launch(headless=headless)
    #         self.page = self.browser.new_page()
            
    #         print(f"Executing {len(events)} events (including verification)...")
            
    #         # Execute each event
    #         success_count = 0
    #         verification_passed = None
            
    #         for i, event in enumerate(events, 1):
    #             operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
                
    #             print(f"\n--- Executing Event {i}/{len(events)} ---")
    #             print(f"Step: {event.step_number}")
    #             print(f"Operation: {operation_name}")
    #             print(f"URL: {event.url}")
    #             print(f"Component: {event.html_component}")
    #             if event.input_text:
    #                 print(f"Input: {event.input_text}")
                
    #             try:
    #                 self._execute_single_event(event)
    #                 success_count += 1
                    
    #                 # Track if this was verification event
    #                 if operation_name == "verify_element":
    #                     verification_passed = True
    #                     print(f"✅ Event {i} (VERIFICATION) passed!")
    #                 else:
    #                     print(f"✅ Event {i} executed successfully")
                        
    #             except Exception as e:
    #                 print(f"❌ Event {i} failed: {e}")
                    
    #                 # If verification fails, mark it
    #                 if operation_name == "verify_element":
    #                     verification_passed = False
                    
    #                 # Continue with next event
    #                 continue
                
    #             time.sleep(1)
            
    #         # Check results
    #         all_passed = success_count == len(events)
            
    #         print(f"\n{'='*80}")
    #         print(f"🎯 EXECUTION SUMMARY")
    #         print(f"{'='*80}")
    #         print(f"   Total Events: {len(events)}")
    #         print(f"   Successful: {success_count}")
    #         print(f"   Failed: {len(events) - success_count}")
            
    #         if verification_passed is not None:
    #             if verification_passed:
    #                 print(f"   ✅ VERIFICATION: PASSED")
    #             else:
    #                 print(f"   ❌ VERIFICATION: FAILED")
            
    #         if all_passed:
    #             print(f"\n✅ ALL EVENTS INCLUDING VERIFICATION PASSED!")
    #         else:
    #             print(f"\n⚠️ SOME EVENTS FAILED")
    #         print(f"{'='*80}")
            
    #         # Keep browser open briefly
    #         if not headless:
    #             wait_time = 5 if verification_passed else 3
    #             print(f"\nBrowser will close in {wait_time} seconds...")
    #             time.sleep(wait_time)
            
    #         return all_passed
            
    #     except Exception as e:
    #         print(f"❌ Error during execution: {e}")
    #         return False
    #     finally:
    #         self._cleanup()
    
    def execute_events(self, events: List[Event], headless: bool = False) -> dict:
        """
        Execute a list of events in sequence with detailed results.
        
        Returns:
            dict: {
                'success': bool,
                'total_events': int,
                'passed_events': int,
                'failed_events': int,
                'event_results': List[dict]  # Detailed per-event results
            }
        """
        if not events:
            return {
                'success': False,
                'total_events': 0,
                'passed_events': 0,
                'failed_events': 0,
                'event_results': []
            }
        
        try:
            # Initialize Playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()
            
            print(f"Executing {len(events)} events...")
            
            # Track detailed results
            event_results = []
            success_count = 0
            
            for i, event in enumerate(events, 1):
                operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
                
                event_info = {
                    'event_number': i,
                    'step_number': event.step_number,
                    'operation': operation_name,
                    'component': event.html_component,
                    'input': event.input_text,
                    'success': False,
                    'error': None
                }
                
                print(f"\n--- Executing Event {i}/{len(events)} ---")
                print(f"Operation: {operation_name}")
                
                try:
                    self._execute_single_event(event)
                    success_count += 1
                    event_info['success'] = True
                    print(f"✅ Event {i} passed")
                        
                except Exception as e:
                    event_info['error'] = str(e)
                    print(f"❌ Event {i} failed: {e}")
                
                event_results.append(event_info)
                time.sleep(1)
            
            all_passed = success_count == len(events)
            
            # Keep browser open briefly if not headless
            if not headless:
                time.sleep(2)
            
            return {
                'success': all_passed,
                'total_events': len(events),
                'passed_events': success_count,
                'failed_events': len(events) - success_count,
                'event_results': event_results
            }
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            return {
                'success': False,
                'total_events': len(events),
                'passed_events': 0,
                'failed_events': len(events),
                'event_results': [],
                'error': str(e)
            }
        finally:
            self._cleanup()
    
    def execute_module_features(self, features_with_events: List[dict], headless: bool = False) -> dict:
        """
        Execute multiple features in a SINGLE browser session.
        Browser opens once, executes all features sequentially, then closes.
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
            # Initialize Playwright ONCE for ALL features
            print(f"\n🌐 Opening browser session for module execution...")
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
        # Get operation name first
        operation_name = self.operation_mapper.get_operation_name_by_id(event.operation_id)
        print(f"Operation: {operation_name}")
        
        # ✅ Navigate to URL only if not skipping AND not verify_element
        if event.url and operation_name != "verify_element" and not self.skip_navigation:
            current_url = self.page.url
            if not self._is_same_url(current_url, event.url):
                print(f"Navigating to: {event.url}")
                self.page.goto(event.url)
                self.page.wait_for_load_state("networkidle")
            else:
                print(f"Already on {event.url}, skipping navigation")
        elif operation_name == "verify_element":
            print(f"Verification on current page: {self.page.url}")
        elif self.skip_navigation:
            print(f"Staying on current page: {self.page.url}")  # ✅ NEW LOG
        
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
            raise ValueError(f"Unknown operation: {operation_name}")


    async def _execute_and_capture_dom(self, events, final_dom_path: str):
        """
        Execute events and capture final DOM state.
        
        Args:
            events: List of events to execute
            final_dom_path: Path to save final DOM
            
        Returns:
            dict: {'success': bool, 'error': str (optional)}
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # Navigate to first event URL
                if events and events[0].url:
                    await page.goto(events[0].url)
                    await page.wait_for_load_state('networkidle')
                
                # Execute each event
                for i, event in enumerate(events, 1):
                    print(f"  Executing event {i}/{len(events)}: {event.operation_id}")
                    
                    try:
                        # Get operation name
                        from model.operation_type import OperationTypeMapper
                        mapper = OperationTypeMapper(self.db_path)
                        mapper.load_operation_types()
                        operation_name = mapper.get_operation_name_by_id(event.operation_id)
                        print("current url", event.url)
                        print("page url", page.url)
                        # Navigate if URL changed
                        current_url = page.url
                        print("calling func same url")
                        if self._is_same_url(current_url, event.url)== False:
                            print("url not same")

                            await page.goto(event.url)
                            await page.wait_for_load_state('networkidle')
                        
                        # Execute based on operation type
                        if operation_name == "click":
                            locator = page.locator(event.html_component)
                            await locator.click()
                            print(f"    ✓ Clicked: {event.html_component}")
                            
                        elif operation_name == "input_text":
                            locator = page.locator(event.html_component)
                            await locator.fill(event.input_text)
                            print(f"    ✓ Input text: {event.input_text}")
                        
                        # Wait for any navigation/updates
                        await page.wait_for_load_state('networkidle')
                        
                    except Exception as e:
                        print(f"    ⚠️ Event {i} error: {e}")
                        continue
                
                # Wait for final state
                print("\n  ⏳ Waiting for final page state...")
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)  # Additional 2s for any async operations
                
                # Capture final DOM
                final_html = await page.content()
                with open(final_dom_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                await browser.close()
                
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    def _is_same_url(self, current_url: str, target_url: str) -> bool:
        """Check if current URL matches target URL, ignoring protocol and trailing slashes."""
        try:
            # Remove protocol and normalize URLs
            current_normalized = current_url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            target_normalized = target_url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            
            # Check if URLs match
            print("current_normalized",current_normalized)

            print("target_normalized",target_normalized)
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
