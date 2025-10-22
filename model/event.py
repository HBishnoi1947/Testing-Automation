"""
Event model for the testing automation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class Event:
    """Represents one UI action step for browsing automation."""
    # Required fields first (no defaults)
    feature_id: int
    operation_id: int
    step_number: int

    # Optional fields with defaults after required ones
    url: Optional[str] = None
    html_component: Optional[str] = None
    input_text: Optional[str] = None
    # Auto-incrementing primary key; assigned if not provided
    id: Optional[int] = field(default=None, repr=True)

    def to_row(self) -> List[Any]:
        """Convert the event to a row format for database operations."""
        return [self.id, self.feature_id, self.url, self.html_component, self.operation_id, self.input_text, self.step_number]
