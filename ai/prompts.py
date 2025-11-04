"""
Prompt templates for AI web automation event generation.
"""


def get_generate_events_prompt(url: str, formatted_elements: str, prompt: str) -> str:
    """
    Generate the system prompt for creating new automation events.
    
    Args:
        url: Target URL
        formatted_elements: Formatted HTML elements string
        prompt: User instruction prompt
        
    Returns:
        Complete system prompt string
    """
    return f"""
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


def get_re_generate_events_prompt(
    url: str, 
    feature_name: str, 
    formatted_elements: str, 
    existing_events_json: str, 
    prompt: str, 
    feature_id: int
) -> str:
    """
    Generate the system prompt for re-generating automation events with existing context.
    
    Args:
        url: Target URL
        feature_name: Name of the feature
        formatted_elements: Formatted HTML elements string
        existing_events_json: JSON string of existing events for context
        prompt: User instruction prompt
        feature_id: ID of the feature to update
        
    Returns:
        Complete system prompt string
    """
    return f"""
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

