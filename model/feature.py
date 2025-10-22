"""
Feature model for the testing automation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class Feature:
    """Represents a feature in the system."""
    feature: str
    id: Optional[int] = field(default=None, repr=True)

    def to_row(self) -> List[Any]:
        """Convert the feature to a row format for database operations."""
        return [self.id, self.feature]
