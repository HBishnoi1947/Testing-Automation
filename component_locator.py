"""
Component Locator for Testing Automation POC.
Helper class for intelligent component identification with high accuracy.
Handles multiple selector types and fallback strategies.
"""

import re
from typing import Optional, Tuple
from playwright.sync_api import Page


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

