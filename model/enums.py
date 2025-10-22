"""
Enums for the testing automation system.
"""

from enum import Enum


class OperationTypeEnum(Enum):
    """Enumeration of operation types for UI automation."""
    CLICK = "click"
    SCROLL = "scroll"
    INPUT_TEXT = "inputText"
