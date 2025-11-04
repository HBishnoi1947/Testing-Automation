"""
MapTestingModule model mapping items into a testing module flow.
"""

from dataclasses import dataclass
from typing import Optional, List, Any


@dataclass
class MapTestingModule:
    """Represents a single step mapping in a testing module flow (feature-only)."""
    testing_module_id: int
    step_number: int
    feature_id: Optional[int] = None
    id: Optional[int] = None

    def to_row(self) -> List[Any]:
        """Convert the mapping to a row format for database operations."""
        return [
            self.id,
            self.testing_module_id,
            self.feature_id,
            self.step_number,
        ]


