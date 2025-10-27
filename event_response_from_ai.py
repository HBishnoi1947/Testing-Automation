import google.generativeai as genai
import json
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import os
from model.database import get_events_by_feature_id, clear_all_events_from_sqlite
from model.operation_type import OperationTypeMapper


class WebAutomationAgent:
    def __init__(self, api_key: str):
        """
        Initialize the Web Automation AI Agent
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def load_html(self, html_file_path: str) -> str:
        """
        Load HTML content from file
        """
        if not os.path.exists(html_file_path):
            raise FileNotFoundError(f"File not found: {html_file_path}")
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def extract_interactive_elements(self, html_content: str) -> str:
        """
        Extract interactive elements from HTML for context
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        interactive_elements = []
        interactive_tags = ['input', 'button', 'a', 'select', 'textarea', 'form']

        for tag_name in interactive_tags:
            elements = soup.find_all(tag_name)
            for elem in elements:
                element_info = {
                    'tag': tag_name,
                    'id': elem.get('id', ''),
                    'class': ' '.join(elem.get('class', [])),
                    'type': elem.get('type', ''),
                    'name': elem.get('name', ''),
                    'placeholder': elem.get('placeholder', ''),
                    'value': elem.get('value', ''),
                    'text': elem.get_text(strip=True),
                    'html': str(elem)[:500]  # Limit HTML length
                }
                interactive_elements.append(element_info)

        # Also include important structural elements
        structural_elements = []
        structural_tags = ['div', 'section', 'article', 'main', 'nav', 'header', 'footer']
        
        for tag_name in structural_tags:
            elements = soup.find_all(tag_name, limit=10)  # Limit to avoid too much data
            for elem in elements:
                if elem.get('id') or elem.get('class'):
                    element_info = {
                        'tag': tag_name,
                        'id': elem.get('id', ''),
                        'class': ' '.join(elem.get('class', [])),
                        'text': elem.get_text(strip=True)[:100],
                        'html': str(elem)[:300]
                    }
                    structural_elements.append(element_info)

        return {
            'interactive': interactive_elements,
            'structural': structural_elements
        }

    def format_elements_for_prompt(self, elements: Dict) -> str:
        """
        Format extracted elements for the AI prompt
        """
        interactive_text = "INTERACTIVE ELEMENTS (inputs, buttons, links, forms):\n"
        for i, elem in enumerate(elements['interactive'], 1):
            interactive_text += f"{i}. <{elem['tag']}"
            if elem['id']:
                interactive_text += f" id='{elem['id']}'"
            if elem['class']:
                interactive_text += f" class='{elem['class']}'"
            if elem['type']:
                interactive_text += f" type='{elem['type']}'"
            if elem['name']:
                interactive_text += f" name='{elem['name']}'"
            if elem['placeholder']:
                interactive_text += f" placeholder='{elem['placeholder']}'"
            if elem['text']:
                interactive_text += f"> {elem['text']}"
            interactive_text += "\n"

        structural_text = "\nSTRUCTURAL ELEMENTS (containers, sections):\n"
        for i, elem in enumerate(elements['structural'], 1):
            structural_text += f"{i}. <{elem['tag']}"
            if elem['id']:
                structural_text += f" id='{elem['id']}'"
            if elem['class']:
                structural_text += f" class='{elem['class']}'"
            structural_text += f"> {elem['text']}\n"

        return interactive_text + structural_text

    def events_to_json_context(self, events: List, operation_mapper: OperationTypeMapper) -> str:
        """
        Convert events to JSON format for AI context
        """
        events_data = []
        for event in events:
            operation_name = operation_mapper.get_operation_name_by_id(event.operation_id)
            event_data = {
                "id": event.id,
                "step_number": event.step_number,
                "url": event.url,
                "html_component": event.html_component,
                "operation_name": operation_name,
                "input_text": event.input_text
            }
            events_data.append(event_data)
        
        return json.dumps(events_data, indent=2)

    def generate_events(self, html_file_path: str, url: str, prompt: str) -> Dict:
        """
        Generate automation events using the full HTML context
        """
        try:
            html_content = self.load_html(html_file_path)
            print(f"[✓] Loaded HTML file: {len(html_content)} characters")

            elements = self.extract_interactive_elements(html_content)
            print(f"[✓] Extracted {len(elements['interactive'])} interactive elements")
            print(f"[✓] Extracted {len(elements['structural'])} structural elements")

            formatted_elements = self.format_elements_for_prompt(elements)

            system_prompt = f"""
You are a web automation expert. Analyze the given webpage elements and user instruction to generate a sequence of automation events.

URL: {url}

WEBPAGE ELEMENTS:
{formatted_elements}

User Instruction: {prompt}

Based on the webpage elements and instruction, generate automation events in this EXACT JSON format:
{{
  "noOfEvents": <number>,
  "feature": "<feature name>",
  "events": [
    {{
      "url": "{url}",
      "html_component": "<the exact HTML element to target>",
      "operation_name": "<click|scroll|input_text>",
      "input_text": "<text to input or null>",
      "step_number": <number>
    }}
  ]
}}

IMPORTANT RULES:
1. Use ONLY the HTML elements shown in the webpage elements above.
2. operationType must be one of: "click", "scroll", or "input".
3. For "input" operations, provide the text to input as a string.
4. For "click" and "scroll" operations, set input to null.
5. Provide clear eventDescription for each step.
6. Return ONLY valid JSON, no explanation.
7. The htmlComponent should identify the element clearly (using id, class, text, or combination) so that playwright can locate the element using <page.locator(html_component)> locator strategy. Example: button[type='submit'] or input[name='email'] or div[class='login-button'] or span[text='Login']
8. Use the most specific element possible.
9. Order events logically to achieve the goal.
10. Focus on interactive elements that match the user's instruction.
"""

            response = self.model.generate_content(system_prompt)
            response_text = response.text.strip()

            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            if "noOfEvents" not in result or "events" not in result:
                raise ValueError("Invalid response structure")

            return result

        except FileNotFoundError:
            return {"noOfEvents": 0, "events": [], "error": f"File not found: {html_file_path}"}
        except json.JSONDecodeError as e:
            print(f"[!] JSON Parse Error: {e}")
            print("Response text:", response_text)
            return {"noOfEvents": 0, "events": [], "error": "Failed to parse AI response"}
        except Exception as e:
            print(f"[!] Error generating events: {e}")
            return {"noOfEvents": 0, "events": [], "error": str(e)}

    def re_generate_events(self, html_file_path: str, url: str, prompt: str, feature_id: int, feature_name: str, existing_events: List, db_path: str = "database.db") -> Dict:
        """
        Re-generate automation events using existing events as context
        
        Args:
            html_file_path: Path to HTML file
            url: Target URL
            prompt: User instruction prompt
            feature_id: ID of the feature to update
            existing_events: List of existing Event objects for context
            db_path: Path to database file
        """
        try:
            # Load HTML content
            html_content = self.load_html(html_file_path)
            print(f"[✓] Loaded HTML file: {len(html_content)} characters")

            # Extract interactive elements
            elements = self.extract_interactive_elements(html_content)
            print(f"[✓] Extracted {len(elements['interactive'])} interactive elements")
            print(f"[✓] Extracted {len(elements['structural'])} structural elements")

            formatted_elements = self.format_elements_for_prompt(elements)

            # Use existing events passed as parameter
            print(f"[✓] Using {len(existing_events)} existing events for context")

            # Convert events to JSON context
            operation_mapper = OperationTypeMapper(db_path)
            operation_mapper.load_operation_types()
            existing_events_json = self.events_to_json_context(existing_events, operation_mapper)

            # Use feature_name passed as parameter
            print(f"[✓] Using feature name: {feature_name}")

            system_prompt = f"""
You are a web automation expert. Analyze the given webpage elements, user instruction, and existing events to generate an updated sequence of automation events.

URL: {url}
FEATURE: {feature_name}

WEBPAGE ELEMENTS:
{formatted_elements}

EXISTING EVENTS (for context):
{existing_events_json}

User Instruction: {prompt}

Based on the webpage elements, existing events, and instruction, generate updated automation events in this EXACT JSON format:
{{
  "noOfEvents": <number>,
  "feature": "{feature_name}",
  "feature_id": {feature_id},
  "events": [
    {{
      "url": "{url}",
      "html_component": "<the exact HTML element to target>",
      "operation_name": "<click|scroll|input_text>",
      "input_text": "<text to input or null>",
      "step_number": <number>
    }}
  ]
}}

IMPORTANT RULES:
1. Use ONLY the HTML elements shown in the webpage elements above.
2. operation_name must be one of: "click", "scroll", or "input_text".
3. For "input_text" operations, provide the text to input as a string.
4. For "click" and "scroll" operations, set input_text to null.
5. The html_component should identify the element clearly (using id, class, text, or combination) so that playwright can locate the element using <page.locator(html_component)> locator strategy. Example: button[type='submit'] or input[name='email'] or div[class='login-button'] or span[text='Login']
6. Use the most specific element possible.
7. Order events logically to achieve the goal.
8. Focus on interactive elements that match the user's instruction.
9. Consider the existing events as context but generate fresh events based on the current webpage elements and instruction.
10. Return ONLY valid JSON, no explanation.
"""

            response = self.model.generate_content(system_prompt)
            response_text = response.text.strip()

            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            if "noOfEvents" not in result or "events" not in result:
                raise ValueError("Invalid response structure")

            # Add metadata to result
            result['feature_id'] = feature_id
            result['feature_name'] = feature_name
            
            print(f"[✓] AI processing completed successfully")
            return result

        except FileNotFoundError:
            return {"noOfEvents": 0, "events": [], "error": f"File not found: {html_file_path}"}
        except json.JSONDecodeError as e:
            print(f"[!] JSON Parse Error: {e}")
            print("Response text:", response_text)
            return {"noOfEvents": 0, "events": [], "error": "Failed to parse AI response"}
        except Exception as e:
            print(f"[!] Error re-generating events: {e}")
            return {"noOfEvents": 0, "events": [], "error": str(e)}

# --------------------------- TEST SECTION ---------------------------
if __name__ == "__main__":
    API_KEY = "AIzaSyA_jrCpHgsAY-J3pIeKJWPuZ76su3ug2DY"  # replace with your key
    agent = WebAutomationAgent(API_KEY)

    html_path = r"E:\Testing Automation\POC modules\bishnoishaadi_dom.txt"
    test_url = "https://www.bishnoishaadi.com"
    test_prompt = "Signup with email and password"
    test_feature_id = 1  # Example feature ID for testing

    print("=" * 80)
    print(f"Testing DOM: {html_path}")
    print("=" * 80)

    # Test generate_events
    print("\n🔄 Testing generate_events...")
    result = agent.generate_events(html_file_path=html_path, url=test_url, prompt=test_prompt)
    print("\n" + "=" * 80)
    print("✅ GENERATE EVENTS RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test re_generate_events
    print("\n🔄 Testing re_generate_events...")
    # Get existing events for testing
    from model.database import get_events_by_feature_id, connect_to_sqlite_database
    existing_events = get_events_by_feature_id(test_feature_id)
    print(f"Found {len(existing_events)} existing events for testing")
    
    # Get feature name for testing
    conn = connect_to_sqlite_database("database.db")
    try:
        cursor = conn.execute("SELECT feature FROM features WHERE id = ?", (test_feature_id,))
        row = cursor.fetchone()
        test_feature_name = row['feature'] if row else f"Feature {test_feature_id}"
    finally:
        conn.close()
    
    re_result = agent.re_generate_events(
        html_file_path=html_path, 
        url=test_url, 
        prompt=test_prompt, 
        feature_id=test_feature_id,
        feature_name=test_feature_name,
        existing_events=existing_events
    )
    print("\n" + "=" * 80)
    print("✅ RE-GENERATE EVENTS RESULT")
    print("=" * 80)
    print(json.dumps(re_result, indent=2, ensure_ascii=False))