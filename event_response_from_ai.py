import google.generativeai as genai
import json
from typing import Dict, List
from bs4 import BeautifulSoup
import os


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


# --------------------------- TEST SECTION ---------------------------
if __name__ == "__main__":
    API_KEY = "AIzaSyA_jrCpHgsAY-J3pIeKJWPuZ76su3ug2DY"  # replace with your key
    agent = WebAutomationAgent(API_KEY)

    html_path = r"E:\Testing Automation\POC modules\bishnoishaadi_dom.txt"
    test_url = "https://www.bishnoishaadi.com"
    test_prompt = "Signup with email and password"

    print("=" * 80)
    print(f"Testing DOM: {html_path}")
    print("=" * 80)

    result = agent.generate_events(html_file_path=html_path, url=test_url, prompt=test_prompt)

    print("\n" + "=" * 80)
    print("✅ FINAL RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))