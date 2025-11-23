"""
Prompt templates for AI web automation event generation.
Enhanced for maximum DOM component identification accuracy.
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
    "feature": "<feature_name>",
    "events": [
        {{
            "url": "{url}",
            "html_component": "<selector>",
            "operation_name": "<operation>",
            "input_text": "<text_or_null>",
            "step_number": <number>
        }}
    ]
}}

CRITICAL RULES FOR DOM COMPONENT SELECTION (html_component):

1. SELECTOR PRIORITY HIERARCHY (use in this order):

   HIGHEST PRIORITY (Most Reliable):
   a) Unique ID attributes: #unique-id
   b) Unique name attributes: input[name='unique_name']
   c) Data attributes: [data-testid='value'] or [data-id='value']
   d) Text content for links/buttons: text=Click Here (exact visible text)
   e) Unique aria-labels: [aria-label='Submit Form']

   MEDIUM PRIORITY:
   f) Type + name combinations: input[type='email'][name='user_email']
   g) Role + name combinations: button[role='button'][aria-label='Submit']
   h) Placeholder for inputs: input[placeholder='Enter email']

   LOWER PRIORITY (Use only if above unavailable):
   i) Stable class combinations: button.btn.btn-primary.submit-btn
   j) Parent context + attribute: form[id='login'] input[type='password']
   k) Position-based (LAST RESORT): form > div:nth-child(2) > input

2. ENSURE UNIQUENESS - The selector MUST identify ONE SPECIFIC element:
   - ✅ GOOD: input[name='email'][type='email'] (specific)
   - ❌ BAD: input (matches multiple elements)
   - ✅ GOOD: button[type='submit'][form='login-form'] (unique)
   - ❌ BAD: button.btn (matches many buttons)
   - ✅ GOOD: a[text='Contact Us'] or text=Contact Us (exact text)
   - ❌ BAD: a (matches all links)

3. ATTRIBUTE COMBINATION STRATEGY:
   - Combine 2-3 attributes for uniqueness when needed
   - Examples:
     * input[type='text'][name='username'][placeholder='Username']
     * button[type='submit'][class*='primary'][aria-label='Login']
     * a[href='/products'][text='View Products']

4. TEXT-BASED SELECTORS (Highly Reliable):
   - For buttons with visible text: text=Login or button:has-text('Login')
   - For links: a[text='About Us'] or text=About Us
   - For any element with unique text: text=Unique Heading
   - Use exact visible text as shown in WEBPAGE ELEMENTS

5. INPUT FIELD BEST PRACTICES:
   - Priority order for inputs:
     a) name attribute: input[name='email']
     b) id attribute: #email-input
     c) placeholder: input[placeholder='Enter your email']
     d) type + label association: label:has-text('Email') + input[type='email']
     e) aria-label: input[aria-label='Email Address']

6. BUTTON SELECTION BEST PRACTICES:
   - Priority order:
     a) Text content: text=Submit or button:has-text('Submit')
     b) ID: #submit-btn
     c) Type + form: button[type='submit'][form='contact-form']
     d) aria-label: button[aria-label='Submit Contact Form']
     e) Class + text: button.submit-btn:has-text('Send')

7. LINK SELECTION BEST PRACTICES:
   - Priority order:
     a) Text content: text=Contact or a:has-text('Contact')
     b) href attribute: a[href='/contact']
     c) ID/data attributes: a[data-nav='contact']
     d) Combined: a[href='/about']:has-text('About Us')

8. AVOID UNSTABLE SELECTORS:
   - ❌ Dynamic classes: .css-123abc-XYZ
   - ❌ Generated IDs: #component-1234567890
   - ❌ Numeric-only classes: .x1234.x5678
   - ❌ Framework-specific: [class^='MuiButton-root-']
   - ✅ Use stable semantic attributes instead

9. DATA-* AND ARIA-* ATTRIBUTES (Highly Stable):
   - data-testid, data-test, data-id are specifically for testing
   - aria-label, aria-labelledby for accessibility
   - Examples:
     * [data-testid='login-button']
     * [aria-label='Close Dialog']
     * [data-action='submit-form']

10. CONTEXT-AWARE SELECTORS:
    - Use parent context when element isn't unique:
      * form[id='signup'] input[name='email'] (email input in signup form)
      * div[class='modal'] button:has-text('Confirm') (button in modal)
      * nav[class='header'] a:has-text('Login') (login link in header)

11. REAL-WORLD EXAMPLES BY ELEMENT TYPE:

    LOGIN FORMS:
    - Username: input[name='username'] or input[type='text'][autocomplete='username']
    - Password: input[name='password'] or input[type='password']
    - Submit: button[type='submit']:has-text('Login') or text=Login

    SEARCH FUNCTIONALITY:
    - Search input: input[name='q'] or input[placeholder='Search...']
    - Search button: button[type='submit'][aria-label='Search'] or text=Search

    NAVIGATION:
    - Nav links: nav a:has-text('Products') or a[href='/products']
    - Dropdowns: button[aria-haspopup='true']:has-text('Menu')

    MODALS/DIALOGS:
    - Close button: button[aria-label='Close'] or [data-dismiss='modal']
    - Confirm: div[role='dialog'] button:has-text('Confirm')

    TABLES:
    - Specific cell: table tr:nth-child(2) td:nth-child(3)
    - Action button in row: tr:has-text('John Doe') button:has-text('Edit')

12. OPERATION-SPECIFIC REQUIREMENTS:

    - operation_name must be one of: "click", "scroll", "input_text", "verify_element"

    - For "input_text": 
      * Provide the text to input as a string in input_text field
      * Selector must target input/textarea element

    - For "click": 
      * Set input_text to null
      * Selector must target clickable element (button, link, checkbox, etc.)

    - For "scroll": 
      * Set input_text to null
      * Use: "down", "up", "top", "bottom", or element selector to scroll to

    - For "verify_element":
      * Set input_text to description of what element represents (optional)
      * Selector should target the success indicator element

13. VALIDATION CHECKLIST BEFORE RETURNING:
    ✓ Each html_component uses the most specific attributes available
    ✓ Each selector would match exactly ONE element on the page
    ✓ Selectors use stable attributes (not generated classes/IDs)
    ✓ Text-based selectors use exact visible text from WEBPAGE ELEMENTS
    ✓ Combined attributes are used when single attributes aren't unique
    ✓ operation_name matches the action needed
    ✓ Events are ordered logically to achieve the goal
    ✓ Input fields have appropriate input_text values

14. FINAL REQUIREMENTS:
    - Use ONLY the HTML elements shown in the WEBPAGE ELEMENTS section above
    - Return ONLY valid JSON, no explanation or comments
    - Each event must have all required fields
    - Test your selectors mentally against the provided elements for uniqueness

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
            "html_component": "<selector>",
            "operation_name": "<operation>",
            "input_text": "<text_or_null>",
            "step_number": <number>
        }}
    ]
}}

CRITICAL RULES FOR DOM COMPONENT SELECTION (html_component):

1. SELECTOR PRIORITY HIERARCHY (use in this order):

   HIGHEST PRIORITY (Most Reliable):
   a) Unique ID attributes: #unique-id
   b) Unique name attributes: input[name='unique_name']
   c) Data attributes: [data-testid='value'] or [data-id='value']
   d) Text content for links/buttons: text=Click Here (exact visible text)
   e) Unique aria-labels: [aria-label='Submit Form']

   MEDIUM PRIORITY:
   f) Type + name combinations: input[type='email'][name='user_email']
   g) Role + name combinations: button[role='button'][aria-label='Submit']
   h) Placeholder for inputs: input[placeholder='Enter email']

   LOWER PRIORITY (Use only if above unavailable):
   i) Stable class combinations: button.btn.btn-primary.submit-btn
   j) Parent context + attribute: form[id='login'] input[type='password']
   k) Position-based (LAST RESORT): form > div:nth-child(2) > input

2. ENSURE UNIQUENESS - The selector MUST identify ONE SPECIFIC element:
   - ✅ GOOD: input[name='email'][type='email'] (specific)
   - ❌ BAD: input (matches multiple elements)
   - ✅ GOOD: button[type='submit'][form='login-form'] (unique)
   - ❌ BAD: button.btn (matches many buttons)
   - ✅ GOOD: a[text='Contact Us'] or text=Contact Us (exact text)
   - ❌ BAD: a (matches all links)

3. ATTRIBUTE COMBINATION STRATEGY:
   - Combine 2-3 attributes for uniqueness when needed
   - Examples:
     * input[type='text'][name='username'][placeholder='Username']
     * button[type='submit'][class*='primary'][aria-label='Login']
     * a[href='/products'][text='View Products']

4. TEXT-BASED SELECTORS (Highly Reliable):
   - For buttons with visible text: text=Login or button:has-text('Login')
   - For links: a[text='About Us'] or text=About Us
   - For any element with unique text: text=Unique Heading
   - Use exact visible text as shown in WEBPAGE ELEMENTS

5. INPUT FIELD BEST PRACTICES:
   - Priority order for inputs:
     a) name attribute: input[name='email']
     b) id attribute: #email-input
     c) placeholder: input[placeholder='Enter your email']
     d) type + label association: label:has-text('Email') + input[type='email']
     e) aria-label: input[aria-label='Email Address']

6. BUTTON SELECTION BEST PRACTICES:
   - Priority order:
     a) Text content: text=Submit or button:has-text('Submit')
     b) ID: #submit-btn
     c) Type + form: button[type='submit'][form='contact-form']
     d) aria-label: button[aria-label='Submit Contact Form']
     e) Class + text: button.submit-btn:has-text('Send')

7. LINK SELECTION BEST PRACTICES:
   - Priority order:
     a) Text content: text=Contact or a:has-text('Contact')
     b) href attribute: a[href='/contact']
     c) ID/data attributes: a[data-nav='contact']
     d) Combined: a[href='/about']:has-text('About Us')

8. AVOID UNSTABLE SELECTORS:
   - ❌ Dynamic classes: .css-123abc-XYZ
   - ❌ Generated IDs: #component-1234567890
   - ❌ Numeric-only classes: .x1234.x5678
   - ❌ Framework-specific: [class^='MuiButton-root-']
   - ✅ Use stable semantic attributes instead

9. DATA-* AND ARIA-* ATTRIBUTES (Highly Stable):
   - data-testid, data-test, data-id are specifically for testing
   - aria-label, aria-labelledby for accessibility
   - Examples:
     * [data-testid='login-button']
     * [aria-label='Close Dialog']
     * [data-action='submit-form']

10. CONTEXT-AWARE SELECTORS:
    - Use parent context when element isn't unique:
      * form[id='signup'] input[name='email'] (email input in signup form)
      * div[class='modal'] button:has-text('Confirm') (button in modal)
      * nav[class='header'] a:has-text('Login') (login link in header)

11. OPERATION-SPECIFIC REQUIREMENTS:

    - operation_name must be one of: "click", "scroll", "input_text", "verify_element"

    - For "input_text": 
      * Provide the text to input as a string in input_text field
      * Selector must target input/textarea element

    - For "click": 
      * Set input_text to null
      * Selector must target clickable element (button, link, checkbox, etc.)

    - For "scroll": 
      * Set input_text to null
      * Use: "down", "up", "top", "bottom", or element selector to scroll to

    - For "verify_element":
      * Set input_text to description of what element represents (optional)
      * Selector should target the success indicator element

12. VALIDATION CHECKLIST BEFORE RETURNING:
    ✓ Each html_component uses the most specific attributes available
    ✓ Each selector would match exactly ONE element on the page
    ✓ Selectors use stable attributes (not generated classes/IDs)
    ✓ Text-based selectors use exact visible text from WEBPAGE ELEMENTS
    ✓ Combined attributes are used when single attributes aren't unique
    ✓ operation_name matches the action needed
    ✓ Events are ordered logically to achieve the goal
    ✓ Input fields have appropriate input_text values

13. CONSIDER EXISTING EVENTS:
    - Review the selectors used in existing_events_json
    - If they failed, choose alternative, more specific selectors
    - If they worked, maintain consistency in selector strategy
    - Improve upon any vague or non-unique selectors

14. FINAL REQUIREMENTS:
    - Use ONLY the HTML elements shown in the WEBPAGE ELEMENTS section above
    - Return ONLY valid JSON, no explanation or comments
    - Each event must have all required fields
    - Order events logically to achieve the goal

"""


def get_validate_execution_prompt(
    feature_name: str,
    initial_formatted: str,
    final_formatted: str,
    expected_outcome: str = None
) -> str:

    """
    Generate the system prompt for validating execution success.

    Args:
        feature_name: Name of the feature being validated
        initial_formatted: Formatted HTML elements from initial page state
        final_formatted: Formatted HTML elements from final page state
        expected_outcome: Optional description of expected outcome

    Returns:
        Complete validation prompt string
    """

    expected_outcome_text = f"EXPECTED OUTCOME: {expected_outcome}" if expected_outcome else ""

    return f"""
You are a web automation validation expert. Compare the initial and final state of a webpage after executing automation events for the feature: "{feature_name}".

INITIAL PAGE STATE:
{initial_formatted[:3000]}

FINAL PAGE STATE:
{final_formatted[:3000]}

FEATURE: {feature_name}
{expected_outcome_text}

Your task:
1. Determine if the automation was SUCCESSFUL by analyzing the changes
2. Identify a SUCCESS INDICATOR element that proves the feature worked (e.g., success message, new page element, logged-in state indicator)
3. Provide the MOST RELIABLE CSS selector for this verification element

Respond in this EXACT JSON format:

{{
    "success": true/false,
    "reason": "Detailed explanation of why it succeeded or failed",
    "suggestions": "If failed, suggest what to fix",
    "verification_selector": "CSS selector for success indicator element",
    "verification_description": "Brief description of what this element represents"
}}

CRITICAL RULES FOR verification_selector:

1. SELECTOR PRIORITY HIERARCHY (use in this order):

   HIGHEST PRIORITY (Most Reliable):
   a) Unique ID: #success-message
   b) Data attributes: [data-testid='success-indicator']
   c) Unique class: .success-alert (if truly unique)
   d) Text content: text=Success or div:has-text('successfully')
   e) Aria attributes: [aria-label='Success Message']

   MEDIUM PRIORITY:
   f) Type + class: div.alert.alert-success
   g) Role + text: [role='alert']:has-text('Success')

   LOWER PRIORITY:
   h) Context + element: .modal-body .success-message
   i) Multiple classes: div.message.success.show

2. ENSURE UNIQUENESS:
   - Selector must identify ONE SPECIFIC success indicator
   - Must be visible and stable across page loads
   - Prefer semantic attributes over generated classes

3. COMMON SUCCESS INDICATORS:
   - Success/confirmation messages
   - New dashboard/profile elements after login
   - Form disappearance after submission
   - URL change to success page
   - Notification badges
   - "Welcome [username]" text
   - Logout button appearing (for login features)
   - Cart count updating (for add-to-cart features)

4. SELECTOR EXAMPLES FOR COMMON SCENARIOS:
   - Login success: text=Welcome or [aria-label='User Menu'] or .user-avatar
   - Form submission: .alert-success or text=Thank you or [role='alert']
   - Item added: .cart-badge or text=Added to cart
   - Registration: text=Check your email or .verification-sent
   - Error state: .alert-danger or [role='alert']:has-text('error')

5. VALIDATION REQUIREMENTS:
   - verification_selector must be a valid CSS selector or text selector
   - verification_description should explain what the element indicates
   - selector should be specific enough to avoid false positives
   - selector should be reliable enough to work on subsequent runs

6. SET success TO:
   - true: If clear success indicators are present in FINAL STATE
   - false: If no success indicators found, or error indicators present

7. FINAL CHECKLIST:
   ✓ verification_selector is unique and specific
   ✓ verification_selector uses stable attributes
   ✓ verification_description clearly explains the success indicator
   ✓ reason provides detailed analysis of state changes
   ✓ suggestions are actionable (if failed)

IMPORTANT:
- Return ONLY valid JSON, no explanation or comments
- Be thorough in comparing initial vs final states
- Look for both positive indicators (success) and negative indicators (errors)

"""
