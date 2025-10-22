"""
OperationType model for the testing automation system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict


@dataclass
class OperationType:
    """Represents an operation type in the system."""
    operation: str
    description: Optional[str] = None
    id: Optional[int] = field(default=None, repr=True)

    def to_row(self) -> List[Any]:
        """Convert the operation type to a row format for database operations."""
        return [self.id, self.operation, self.description]


class OperationTypeMapper:
    """Optimized mapper for operation types to avoid repeated database queries."""
    
    def __init__(self, db_path: str = "database.db"):
        """Initialize the mapper with database path."""
        self.db_path = db_path
        self._operation_types: Dict[int, OperationType] = {}
        self._operation_name_to_id: Dict[str, int] = {}
        self._loaded = False
    
    def load_operation_types(self) -> None:
        """Load all operation types from database once for optimization."""
        if self._loaded:
            return
            
        from .database import connect_to_sqlite_database
        
        conn = connect_to_sqlite_database(self.db_path)
        
        try:
            select_sql = "SELECT * FROM operation_types"
            cursor = conn.execute(select_sql)
            rows = cursor.fetchall()
            
            for row in rows:
                operation_type = OperationType(
                    id=row['id'],
                    operation=row['operation'],
                    description=row['description']
                )
                
                # Store by ID
                self._operation_types[row['id']] = operation_type
                
                # Store name to ID mapping
                self._operation_name_to_id[row['operation']] = row['id']
            
            self._loaded = True
            print(f"Loaded {len(self._operation_types)} operation types for optimization")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load operation types: {e}")
        
        finally:
            conn.close()
    
    def get_operation_by_id(self, operation_id: int) -> Optional[OperationType]:
        """Get operation type by ID."""
        if not self._loaded:
            self.load_operation_types()
        
        return self._operation_types.get(operation_id)
    
    def get_operation_name_by_id(self, operation_id: int) -> Optional[str]:
        """Get operation name by ID."""
        if not self._loaded:
            self.load_operation_types()
        
        operation_type = self._operation_types.get(operation_id)
        return operation_type.operation if operation_type else None
    
    def get_all_operation_types(self) -> Dict[int, OperationType]:
        """Get all operation types."""
        if not self._loaded:
            self.load_operation_types()
        
        return self._operation_types.copy()
    
    def refresh(self) -> None:
        """Refresh the operation types from database."""
        self._operation_types.clear()
        self._operation_name_to_id.clear()
        self._loaded = False
        self.load_operation_types()
