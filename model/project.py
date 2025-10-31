"""
Project model for the testing automation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class Project:
    """Represents a project in the system."""
    name: str
    description: Optional[str] = None
    id: Optional[int] = field(default=None, repr=True)
    created_at: Optional[str] = None

    def to_row(self) -> List[Any]:
        """Convert the project to a row format for database operations."""
        return [self.id, self.name, self.description, self.created_at]

