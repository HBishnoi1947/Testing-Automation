"""
TestingModule model for the testing automation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class TestingModule:
    """Represents a testing module grouping features/events into a flow."""
    testing_module: str
    id: Optional[int] = field(default=None, repr=True)

    def to_row(self) -> List[Any]:
        """Convert the testing module to a row format for database operations."""
        return [self.id, self.testing_module]


