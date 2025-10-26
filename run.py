"""
Main automation runner that orchestrates the browser automation workflow.
Opens browser, navigates to URL, extracts DOM, processes with AI, and saves to database.
"""

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from event_response_from_ai import WebAutomationAgent
from model.database import create_events


class AutomationRunner:
    def __init__(self, api_key: str, db_path: str = "database.db"):
        """
        Initialize the automation runner.
        
        Args:
            api_key: Google Gemini API key for AI processing
            db_path: Path to SQLite database file
        """
        self.api_key = api_key
        self.db_path = db_path
        self.ai_agent = WebAutomationAgent(api_key)
        
    async def run_automation_workflow(self, target_url: str, prompt: str, dom_output_file: str = None):
        """
        Run the complete automation workflow:
        1. Open browser and navigate to URL
        2. Extract DOM content
        3. Process with AI to generate events
        4. Save events to database
        
        Args:
            target_url: URL to navigate to
            prompt: Hardcoded prompt for AI processing
            dom_output_file: File to save extracted DOM content (defaults to url_datetime.txt)
        """
        # Generate default filename if not provided
        if dom_output_file is None:
            # Extract domain from URL and clean it
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            dom_output_file = f"{domain}_{current_time}.txt"
        
        print("=" * 80)
        print("🚀 STARTING AUTOMATION WORKFLOW")
        print("=" * 80)
        print(f"Target URL: {target_url}")
        print(f"Prompt: {prompt}")
        print(f"DOM Output: {dom_output_file}")
        
        try:
            # Step 1: Open browser and navigate to URL
            print("\n📱 Step 1: Opening browser and navigating to URL...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
                page = await browser.new_page()
                
                print(f"Navigating to: {target_url}")
                await page.goto(target_url)
                
                # Wait for page to fully load
                await page.wait_for_load_state('networkidle')
                print("✅ Navigation completed successfully")
                
                # Step 2: Extract DOM content
                print("\n🔍 Step 2: Extracting DOM content...")
                html_content = await page.content()
                
                # Save to text file
                with open(dom_output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ DOM content saved to: {dom_output_file}")
                
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
                return False
                
            print(f"✅ AI generated {ai_result.get('noOfEvents', 0)} events")
            print(f"AI result: {ai_result}")
            
            # Step 4: Save events to database
            print("\n💾 Step 4: Saving events to database...")
            self._save_events_to_database(ai_result)
            print("✅ Events saved to database successfully")
            
            print("\n" + "=" * 80)
            print("🎉 AUTOMATION WORKFLOW COMPLETED SUCCESSFULLY")
            print("=" * 80)
            return True
            
        except Exception as e:
            print(f"\n❌ AUTOMATION WORKFLOW FAILED: {e}")
            return False
    
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


async def main():
    """
    Main function to run the automation workflow with hardcoded values.
    """
    # Configuration
    API_KEY = "AIzaSyA_jrCpHgsAY-J3pIeKJWPuZ76su3ug2DY"  # Replace with your API key
    TARGET_URL = "https://www.bishnoishaadi.com/login"
    HARDCODED_PROMPT = "Login with email = harshbshnoi@gmail.com and password = 123456"
    DATABASE_PATH = "database.db"
    
    # Initialize and run automation
    runner = AutomationRunner(API_KEY, DATABASE_PATH)
    
    success = await runner.run_automation_workflow(
        target_url=TARGET_URL,
        prompt=HARDCODED_PROMPT
    )
    
    if success:
        print("\n🎯 Workflow completed successfully!")
        print(f"Check the database at: {DATABASE_PATH}")
        print("DOM content saved with auto-generated filename")
    else:
        print("\n💥 Workflow failed. Check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
