"""
Main automation runner that orchestrates the browser automation workflow.
Opens browser, navigates to URL, extracts DOM, processes with AI, and saves to database.

Features:
1. run_automation_workflow: Creates new automation events
2. run_update_automation_workflow: Updates existing automation events using re_generate_events

Usage:
- python run.py                    # Run full workflow (create + update)
- python run.py test-update         # Run only update workflow test
"""

import os
from dotenv import load_dotenv
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from event_response_from_ai import WebAutomationAgent
from model.database import get_events_by_feature_id, update_events, create_events


class AutomationRunner:
    def __init__(self, db_path: str = "database.db"):
        """
        Initialize the automation runner.
        
        Args:
            db_path: Path to SQLite database file
        """
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Create a .env with GEMINI_API_KEY=<your_key>")
        self.db_path = db_path
        self.ai_agent = WebAutomationAgent(self.api_key)

    async def run_automation_workflow(self, target_url: str, prompt: str, dom_output_file: str = None):
        """
        Run the complete automation workflow:
        1. Open browser and navigate to URL
        2. Extract DOM content
        3. Process with AI to generate events
        4. Save events to database
        5. Execute events immediately
        6. Wait for page load and extract final DOM
        7. Validate execution with AI
        8. Return validation result
        
        Args:
            target_url: URL to navigate to
            prompt: Hardcoded prompt for AI processing
            dom_output_file: File to save extracted DOM content
            
        Returns:
            dict: {'success': bool, 'feature_name': str, 'validation': dict}
        """
        # Generate default filename if not provided
        if dom_output_file is None:
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            dom_output_file = f"{domain}_{current_time}.txt"
        
        print("=" * 80)
        print("🚀 STARTING AUTOMATION WORKFLOW WITH VALIDATION")
        print("=" * 80)
        print(f"Target URL: {target_url}")
        print(f"Prompt: {prompt}")
        print(f"DOM Output: {dom_output_file}")
        
        try:
            # Step 1: Open browser and navigate to URL
            print("\n📱 Step 1: Opening browser and navigating to URL...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                print(f"Navigating to: {target_url}")
                await page.goto(target_url)
                await page.wait_for_load_state('networkidle')
                print("✅ Navigation completed successfully")
                
                # Step 2: Extract initial DOM content
                print("\n🔍 Step 2: Extracting initial DOM content...")
                html_content = await page.content()
                
                with open(dom_output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ Initial DOM saved to: {dom_output_file}")
                
                await browser.close()
            
            # Step 3: Process with AI to generate automation events
            print("\n🤖 Step 3: Processing with AI to generate automation events...")
            ai_result = self.ai_agent.generate_events(
                html_file_path=dom_output_file,
                url=target_url,
                prompt=prompt
            )
            
            if "error" in ai_result:
                print(f"❌ AI processing failed: {ai_result['error']}")
                return {'success': False, 'error': ai_result['error']}
                
            print(f"✅ AI generated {ai_result.get('noOfEvents', 0)} events")
            
            # Step 4: Save events to database
            print("\n💾 Step 4: Saving events to database...")
            self._save_events_to_database(ai_result)
            feature_name = ai_result.get("feature", "AI Generated Feature")
            print(f"✅ Events saved for feature: {feature_name}")
            
            # Step 5: Execute events immediately
            print("\n🎬 Step 5: Executing generated events...")
            from model.database import get_events_by_feature_id, connect_to_sqlite_database
            from execute import EventExecutor
            
            # Get feature_id
            conn = connect_to_sqlite_database(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT id FROM features WHERE feature = ? ORDER BY id DESC LIMIT 1",
                    (feature_name,)
                )
                row = cursor.fetchone()
                feature_id = row['id'] if row else None
            finally:
                conn.close()
            
            if not feature_id:
                print("❌ Could not find feature_id")
                return {'success': False, 'error': 'Feature not found in database'}
            
            # Get events
            events = get_events_by_feature_id(feature_id, self.db_path)
            print(f"Loaded {len(events)} events for execution")
            
            # Execute with page object to capture final state
            executor = EventExecutor(self.db_path)
            
            # Execute and get final DOM
            print("\n⚡ Executing events...")
            final_dom_path = dom_output_file.replace('.txt', '_final.txt')
            
            execution_result = await self._execute_and_capture_dom(
                events, 
                final_dom_path
            )
            
            if not execution_result['success']:
                print(f"❌ Execution failed: {execution_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'feature_name': feature_name,
                    'error': execution_result.get('error', 'Execution failed')
                }
            
            print(f"✅ Events executed, final DOM saved to: {final_dom_path}")
            
            # Step 6: Validate execution with AI
            # Step 6: Validate execution with AI
            # Step 6: Validate execution with AI
            print("\n🔍 Step 6: Validating execution with AI...")
            validation_result = self.ai_agent.validate_execution_success(
                initial_html_path=dom_output_file,
                final_html_path=final_dom_path,
                feature_name=feature_name
            )

            print(f"\n📊 VALIDATION RESULTS:")
            print(f"   Success: {validation_result['success']}")
            print(f"   Reason: {validation_result['reason']}")

            # Create verification event
            # Create verification event for existing feature
            if validation_result['success'] and validation_result.get('verification_selector'):
                from model.database import add_single_event_to_feature
                verification_selector = validation_result['verification_selector']
                verification_desc = validation_result.get('verification_description', 'Verification element')
                
                print(f"\n💾 Creating verification event: {verification_selector}")
                print(f"   Description: {verification_desc}")
                
                # Get the step number for verification event (last step + 1)
                last_step = len(ai_result['events'])
                
                # Create verification event dict
                verification_event = {
                "operation_name": "verify_element",
                "step_number": last_step + 1,
                "url": None,  
                "html_component": verification_selector,
                "input_text": verification_desc
            }

                
          
                try:
                    event_id = add_single_event_to_feature(feature_id, verification_event, self.db_path)
                    print(f"✅ Verification event created with ID: {event_id} (step {last_step + 1})")
                except Exception as e:
                    print(f"⚠️ Failed to create verification event: {e}")


            # Determine final success (removed confidence check)
            final_success = validation_result['success']

            if final_success:
                print("\n✅ VALIDATION PASSED")
            else:
                print(f"\n⚠️ VALIDATION FAILED")
                print(f"   Suggestions: {validation_result.get('suggestions', 'None')}")

            print("\n" + "=" * 80)
            print("🎉 AUTOMATION WORKFLOW COMPLETED")
            print("=" * 80)

            # Return result dict for UI
            return {
                'success': final_success,
                'feature_name': feature_name,
                'validation': validation_result
            }


            
        except Exception as e:
            print(f"\n❌ AUTOMATION WORKFLOW FAILED: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


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
                        
                        # Navigate if URL changed
                        current_url = page.url
                        if event.url and event.url != current_url:
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



        
    # async def run_automation_workflow(self, target_url: str, prompt: str, dom_output_file: str = None):
    #     """
    #     Run the complete automation workflow:
    #     1. Open browser and navigate to URL
    #     2. Extract DOM content
    #     3. Process with AI to generate events
    #     4. Save events to database
        
    #     Args:
    #         target_url: URL to navigate to
    #         prompt: Hardcoded prompt for AI processing
    #         dom_output_file: File to save extracted DOM content (defaults to url_datetime.txt)
    #     """
    #     # Generate default filename if not provided
    #     if dom_output_file is None:
    #         # Extract domain from URL and clean it
    #         from urllib.parse import urlparse
    #         parsed_url = urlparse(target_url)
    #         domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
    #         current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         dom_output_file = f"{domain}_{current_time}.txt"
        
    #     print("=" * 80)
    #     print("🚀 STARTING AUTOMATION WORKFLOW")
    #     print("=" * 80)
    #     print(f"Target URL: {target_url}")
    #     print(f"Prompt: {prompt}")
    #     print(f"DOM Output: {dom_output_file}")
        
    #     try:
    #         # Step 1: Open browser and navigate to URL
    #         print("\n📱 Step 1: Opening browser and navigating to URL...")
    #         async with async_playwright() as p:
    #             browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
    #             page = await browser.new_page()
                
    #             print(f"Navigating to: {target_url}")
    #             await page.goto(target_url)
                
    #             # Wait for page to fully load
    #             await page.wait_for_load_state('networkidle')
    #             print("✅ Navigation completed successfully")
                
    #             # Step 2: Extract DOM content
    #             print("\n🔍 Step 2: Extracting DOM content...")
    #             html_content = await page.content()
                
    #             # Save to text file
    #             with open(dom_output_file, 'w', encoding='utf-8') as f:
    #                 f.write(html_content)
                
    #             print(f"✅ DOM content saved to: {dom_output_file}")
                
    #             await browser.close()
            
    #         # Step 3: Process with AI to generate automation events
    #         print("\n🤖 Step 3: Processing with AI to generate automation events...")
    #         ai_result = self.ai_agent.generate_events(
    #             html_file_path=dom_output_file,
    #             url=target_url,
    #             prompt=prompt
    #         )
            
    #         if "error" in ai_result:
    #             print(f"❌ AI processing failed: {ai_result['error']}")
    #             return False
                
    #         print(f"✅ AI generated {ai_result.get('noOfEvents', 0)} events")
    #         print(f"AI result: {ai_result}")
            
    #         # Step 4: Save events to database
    #         print("\n💾 Step 4: Saving events to database...")
    #         self._save_events_to_database(ai_result)
    #         print("✅ Events saved to database successfully")
            
    #         print("\n" + "=" * 80)
    #         print("🎉 AUTOMATION WORKFLOW COMPLETED SUCCESSFULLY")
    #         print("=" * 80)
    #         return True
            
        
    
    async def run_update_automation_workflow(self, target_url: str, prompt: str, feature_id: int, feature_name: str, dom_output_file: str = None):
        """
        Run the update automation workflow WITH VALIDATION:
        1. Open browser and navigate to URL
        2. Extract DOM content
        3. Load existing events from database
        4. Process with AI to re-generate events using existing events as context
        5. Update events in database
        6. Execute regenerated events immediately
        7. Validate execution with AI
        8. Update verification event (ALWAYS, even on validation failure)
        
        Args:
            target_url: URL to navigate to
            prompt: User instruction for updating events
            feature_id: ID of the feature to update
            feature_name: Name of the feature
            dom_output_file: File to save extracted DOM content
            
        Returns:
            dict: {'success': bool, 'feature_name': str, 'validation': dict}
        """
        # Generate default filename if not provided
        if dom_output_file is None:
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            dom_output_file = f"{domain}_update_{current_time}.txt"
        
        print("=" * 80)
        print("🔄 STARTING UPDATE AUTOMATION WORKFLOW WITH VALIDATION")
        print("=" * 80)
        print(f"Target URL: {target_url}")
        print(f"Prompt: {prompt}")
        print(f"Feature ID: {feature_id}")
        print(f"Feature Name: {feature_name}")
        print(f"DOM Output: {dom_output_file}")
        
        try:
            # Step 1: Open browser and navigate to URL
            print("\n📱 Step 1: Opening browser and navigating to URL...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                print(f"Navigating to: {target_url}")
                await page.goto(target_url)
                await page.wait_for_load_state('networkidle')
                print("✅ Navigation completed successfully")
                
                # Step 2: Extract initial DOM content
                print("\n🔍 Step 2: Extracting initial DOM content...")
                html_content = await page.content()
                
                with open(dom_output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ Initial DOM saved to: {dom_output_file}")
                
                await browser.close()
            
            # Step 3: Load existing events from database for context
            print("\n📚 Step 3: Loading existing events from database...")
            from model.database import get_events_by_feature_id
            existing_events = get_events_by_feature_id(feature_id, self.db_path)
            
            if not existing_events:
                print(f"⚠️ No existing events found for feature_id {feature_id}")
                return {
                    'success': False,
                    'error': f'No existing events found for feature_id {feature_id}. Cannot update non-existent feature.'
                }
            
            print(f"✅ Loaded {len(existing_events)} existing events for regeneration context")
            
            # Step 4: Process with AI to re-generate automation events
            print("\n🤖 Step 4: Processing with AI to re-generate automation events...")
            ai_result = self.ai_agent.re_generate_events(
                html_file_path=dom_output_file,
                url=target_url,
                prompt=prompt,
                feature_id=feature_id,
                feature_name=feature_name,
                existing_events=existing_events,
                db_path=self.db_path
            )
            
            if "error" in ai_result:
                print(f"❌ AI processing failed: {ai_result['error']}")
                return {'success': False, 'error': ai_result['error']}
            
            print(f"✅ AI re-generated {ai_result.get('noOfEvents', 0)} events")
            
            # Step 5: Update events in database
            print("\n💾 Step 5: Updating events in database...")
            event_ids = update_events(feature_id, ai_result['events'], self.db_path)
            print(f"✅ Updated {len(event_ids)} events for feature_id {feature_id}")
            
            # Step 6: Execute regenerated events immediately
            print("\n🎬 Step 6: Executing regenerated events...")
            events = get_events_by_feature_id(feature_id, self.db_path)
            print(f"Loaded {len(events)} events for execution")
            
            # Execute and capture final DOM
            final_dom_path = dom_output_file.replace('.txt', '_final.txt')
            execution_result = await self._execute_and_capture_dom(
                events,
                final_dom_path
            )
            
            if not execution_result['success']:
                print(f"❌ Execution failed: {execution_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'feature_name': feature_name,
                    'error': execution_result.get('error', 'Execution failed')
                }
            
            print(f"✅ Events executed, final DOM saved to: {final_dom_path}")
            
            # Step 7: Validate execution with AI
            print("\n🔍 Step 7: Validating execution with AI...")
            validation_result = self.ai_agent.validate_execution_success(
                initial_html_path=dom_output_file,
                final_html_path=final_dom_path,
                feature_name=feature_name
            )
            
            print(f"\n📊 VALIDATION RESULTS:")
            print(f"  Success: {validation_result['success']}")
            print(f"  Reason: {validation_result['reason']}")
            
            # Step 8: Update/create verification event (ALWAYS, even on failure)
            print("\n💾 Step 8: Updating verification event...")
            from model.database import delete_verification_event, add_single_event_to_feature
            
            # Determine verification selector with fallback logic
            verification_selector = None
            verification_desc = None
            
            # Priority 1: Use AI-provided verification selector (if validation succeeded and selector exists)
            if validation_result.get('verification_selector'):
                verification_selector = validation_result['verification_selector']
                verification_desc = validation_result.get('verification_description', 'AI-identified verification element')
                print(f"  ✓ Using AI-identified verification selector: {verification_selector}")
            
            # Priority 2: If validation failed or no selector, use last event's target as fallback
            elif ai_result.get('events'):
                last_event = ai_result['events'][-1]
                verification_selector = last_event.get('html_component', 'body')
                verification_desc = f"Fallback verification: Last action target ({last_event.get('operation_name', 'unknown')} operation)"
                print(f"  ⚠️ No AI selector provided, using fallback: {verification_selector}")
            
            # Priority 3: Ultimate fallback
            else:
                verification_selector = 'body'
                verification_desc = 'Default verification: Page body'
                print(f"  ⚠️ Using default verification selector: body")
            
            # Always create/update verification event
            if verification_selector:
                # Delete old verification event if exists
                delete_verification_event(feature_id, self.db_path)
                
                # Get the step number for verification event (last step + 1)
                last_step = len(ai_result['events'])
                
                # Create new verification event
                verification_event = {
                    "operation_name": "verify_element",
                    "step_number": last_step + 1,
                    "url": None,
                    "html_component": verification_selector,
                    "input_text": verification_desc
                }
                
                try:
                    event_id = add_single_event_to_feature(feature_id, verification_event, self.db_path)
                    print(f"  ✅ Verification event updated with ID: {event_id} (step {last_step + 1})")
                    print(f"     Selector: {verification_selector}")
                    print(f"     Description: {verification_desc}")
                except Exception as e:
                    print(f"  ❌ Failed to update verification event: {e}")
            
            # Determine final success
            final_success = validation_result['success']
            
            if final_success:
                print("\n✅ VALIDATION PASSED")
            else:
                print(f"\n⚠️ VALIDATION FAILED")
                print(f"  Suggestions: {validation_result.get('suggestions', 'None')}")
                print(f"  Note: Verification event created with fallback selector")
            
            print("\n" + "=" * 80)
            print("🎉 UPDATE AUTOMATION WORKFLOW COMPLETED WITH VALIDATION")
            print("=" * 80)
            
            # Return result dict (matching generate_events return format)
            return {
                'success': final_success,
                'feature_name': feature_name,
                'validation': validation_result
            }
            
        except Exception as e:
            print(f"\n❌ UPDATE AUTOMATION WORKFLOW FAILED: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}



    def _save_events_to_database(self, ai_result: dict):
        """
        Save AI-generated events to the database using create_events for efficiency.
        
        Args:
            ai_result: Dictionary containing AI-generated events
        """
        if "events" not in ai_result or not ai_result["events"]:
            print("⚠️ No events to save")
            return
            
        feature_name = ai_result.get("feature", "AI Generated Feature")
        events = ai_result["events"]
        
        print(f"Saving {len(events)} events for feature: {feature_name}")
        
        try:
            # Convert AI events to the format expected by create_events
            formatted_events = []
            for event in events:
                formatted_event = {
                    "operation_name": event.get("operation_name"),
                    "step_number": event.get("step_number", 1),
                    "url": event.get("url"),
                    "html_component": event.get("html_component"),
                    "input_text": event.get("input_text")
                }
                formatted_events.append(formatted_event)
            
            # Create all events at once using create_events
            event_ids = create_events(feature_name, formatted_events, self.db_path)
            print(f"✅ Successfully created {len(event_ids)} events for feature '{feature_name}'")
            
        except Exception as e:
            print(f"❌ Failed to save events: {e}")

if __name__ == "__main__":
    import sys
    
