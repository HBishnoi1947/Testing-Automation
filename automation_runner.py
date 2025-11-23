"""
Main automation runner that orchestrates the browser automation workflow.
Opens browser, navigates to URL, extracts DOM, processes with AI, and saves to database.

Features:
1. run_automation_workflow: Creates new automation events
2. run_update_automation_workflow: Updates existing automation events using re_generate_events

Usage:
- python automation_runner.py                    # Run full workflow (create + update)
- python automation_runner.py test-update         # Run only update workflow test
"""

import os
from dotenv import load_dotenv
import json
import asyncio
from datetime import datetime
from ai import WebAutomationAgent
from model.database import get_events_by_feature_id, update_events, create_events
from execute import EventExecutor 


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
        self.event_executor = EventExecutor()
    
    @staticmethod
    def _get_dom_output_path(target_url: str, dom_output_file: str = None, suffix: str = "") -> str:
        """
        Generate or process DOM output file path, ensuring it's saved in the dom folder.
        
        Args:
            target_url: URL to extract domain from (used if dom_output_file is None)
            dom_output_file: Optional file path. If None, generates filename from target_url
            suffix: Optional suffix to add to generated filename (e.g., "_update")
            
        Returns:
            str: Full path to DOM output file in dom folder
        """
        # Generate default filename if not provided
        if dom_output_file is None:
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            dom_output_file = f"{domain}{suffix}_{current_time}.txt"
        
        # Ensure dom folder exists and update path
        dom_folder = "dom"
        os.makedirs(dom_folder, exist_ok=True)
        # Only add dom folder if not already in the path
        if not dom_output_file.startswith(dom_folder + os.sep) and not dom_output_file.startswith(dom_folder + "/"):
            dom_output_file = os.path.join(dom_folder, os.path.basename(dom_output_file))
        
        return dom_output_file

    def run_automation_workflow(self, target_url: str, prompt: str, project_id: int, dom_output_file: str = None):
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
        # Get DOM output file path in dom folder
        dom_output_file = self._get_dom_output_path(target_url, dom_output_file)
        
        print("=" * 80)
        print("🚀 STARTING AUTOMATION WORKFLOW WITH VALIDATION")
        print("=" * 80)
        print(f"Target URL: {target_url}")
        print(f"Prompt: {prompt}")
        print(f"DOM Output: {dom_output_file}")
        
        try:
            # Step 1: Open browser, navigate to URL, and extract DOM
            print("\n📱 Step 1: Opening browser and navigating to URL...")
            success = self.event_executor.navigate_and_extract_dom(
                target_url=target_url,
                dom_output_file=dom_output_file,
                headless=False
            )
            
            if not success:
                return {'success': False, 'error': 'Failed to navigate and extract DOM'}
            
            # Step 2: Process with AI to generate automation events
            print("\n🤖 Step 2: Processing with AI to generate automation events...")
            ai_result = self.ai_agent.generate_events(
                html_file_path=dom_output_file,
                url=target_url,
                prompt=prompt
            )
            
            if "error" in ai_result:
                print(f"❌ AI processing failed: {ai_result['error']}")
                return {'success': False, 'error': ai_result['error']}
                
            print(f"✅ AI generated {ai_result.get('noOfEvents', 0)} events")
            
            # Step 3: Save events to database
            print("\n💾 Step 3: Saving events to database...")
            self._save_events_to_database(ai_result, project_id)
            feature_name = ai_result.get("feature", "AI Generated Feature")
            print(f"✅ Events saved for feature: {feature_name}")
            
            # Step 4: Execute events immediately
            print("\n🎬 Step 4: Executing generated events...")
            from model.database import get_events_by_feature_id, connect_to_sqlite_database
            
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
            
            # Execute and get final DOM
            print("\n⚡ Executing events...")
            final_dom_path = dom_output_file.replace('.txt', '_final.txt')
            
            execution_result = self.event_executor._execute_and_capture_dom(
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
            
            final_url = execution_result.get('final_url', target_url)
            print(f"✅ Events executed, final DOM saved to: {final_dom_path}")
            print(f"✅ Final URL: {final_url}")
            
            # Step 5: Validate execution with AI
            print("\n🔍 Step 5: Validating execution with AI...")
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
                "url": "",  
                "html_component": verification_selector,
                "input_text": None,
            }

                
          
                try:
                    event_id = add_single_event_to_feature(feature_id, verification_event)
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
    
    def run_update_automation_workflow(self, target_url: str, prompt: str, feature_id: int, feature_name: str, dom_output_file: str = None):
        """
        Run the update automation workflow WITH VALIDATION:
        1. Open browser and navigate to URL if not empty string
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
        # Get DOM output file path in dom folder
        dom_output_file = self._get_dom_output_path(target_url, dom_output_file, suffix="_update")
        
        print("=" * 80)
        print("🔄 STARTING UPDATE AUTOMATION WORKFLOW WITH VALIDATION")
        print("=" * 80)
        print(f"Target URL: {target_url}")
        print(f"Prompt: {prompt}")
        print(f"Feature ID: {feature_id}")
        print(f"Feature Name: {feature_name}")
        print(f"DOM Output: {dom_output_file}")
        
        try:
            # Step 1: Open browser, navigate to URL, and extract DOM
            print("\n📱 Step 1: Opening browser and navigating to URL...")
            success = self.event_executor.navigate_and_extract_dom(
                target_url=target_url,
                dom_output_file=dom_output_file,
                headless=False
            )
            
            if not success:
                return {'success': False, 'error': 'Failed to navigate and extract DOM'}
            
            # Step 2: Load existing events from database for context
            print("\n📚 Step 2: Loading existing events from database...")
            from model.database import get_events_by_feature_id
            existing_events = get_events_by_feature_id(feature_id)
            
            if not existing_events:
                print(f"⚠️ No existing events found for feature_id {feature_id}")
                return {
                    'success': False,
                    'error': f'No existing events found for feature_id {feature_id}. Cannot update non-existent feature.'
                }
            
            print(f"✅ Loaded {len(existing_events)} existing events for regeneration context")
            
            # Step 3: Process with AI to re-generate automation events
            print("\n🤖 Step 3: Processing with AI to re-generate automation events...")
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
            
            # Step 4: Update events in database
            print("\n💾 Step 4: Updating events in database...")
            event_ids = update_events(feature_id, ai_result['events'], self.db_path)
            print(f"✅ Updated {len(event_ids)} events for feature_id {feature_id}")
            
            # Step 5: Execute regenerated events immediately
            print("\n🎬 Step 5: Executing regenerated events...")
            events = get_events_by_feature_id(feature_id, self.db_path)
            print(f"Loaded {len(events)} events for execution")
            
            # Execute and capture final DOM
            final_dom_path = dom_output_file.replace('.txt', '_final.txt')
            execution_result = self.event_executor._execute_and_capture_dom(
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
            
            final_url = execution_result.get('final_url', target_url)
            print(f"✅ Events executed, final DOM saved to: {final_dom_path}")
            print(f"✅ Final URL: {final_url}")
            
            # Step 6: Validate execution with AI
            print("\n🔍 Step 6: Validating execution with AI...")
            validation_result = self.ai_agent.validate_execution_success(
                initial_html_path=dom_output_file,
                final_html_path=final_dom_path,
                feature_name=feature_name
            )
            
            print(f"\n📊 VALIDATION RESULTS:")
            print(f"  Success: {validation_result['success']}")
            print(f"  Reason: {validation_result['reason']}")
            
            # Step 7: Update/create verification event (ALWAYS, even on failure)
            print("\n💾 Step 7: Updating verification event...")
            from model.database import delete_verification_event, add_single_event_to_feature
            
            # Delete old verification event if exists
            delete_verification_event(feature_id, self.db_path)
            
            # Determine verification selector with fallback logic
            verification_selector = None
            verification_desc = None
            
            if validation_result.get('verification_selector'):
                verification_selector = validation_result['verification_selector']
                verification_desc = validation_result.get('verification_description', 'AI-identified verification element')
                print(f"  ✓ Using AI-identified verification selector: {verification_selector}")
            
            else:
                raise Exception("No verification selector provided")
            
            # Always create/update verification event
            if verification_selector:
                
                # Get the step number for verification event (last step + 1)
                last_step = len(ai_result['events'])
                
                # Create new verification event
                verification_event = {
                    "operation_name": "verify_element",
                    "step_number": last_step + 1,
                    "url": "",
                    "html_component": verification_selector,
                    "input_text": None
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



    def _save_events_to_database(self, ai_result: dict, project_id: int):
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
            event_ids = create_events(feature_name, project_id, formatted_events, self.db_path)
            print(f"✅ Successfully created {len(event_ids)} events for feature '{feature_name}'")
            
        except Exception as e:
            print(f"❌ Failed to save events: {e}")

if __name__ == "__main__":
    import sys

