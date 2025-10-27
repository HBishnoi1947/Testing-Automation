"""
Database operations for the testing automation system.
"""

import sqlite3
import os
from typing import Optional, List
from .feature import Feature
from .operation_type import OperationType
from .event import Event


def connect_to_sqlite_database(db_path: str = "database.db") -> sqlite3.Connection:
    """Connect to SQLite database and create it if it doesn't exist.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Create features table
    create_features_table = """
    CREATE TABLE IF NOT EXISTS features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature TEXT NOT NULL
    )
    """
    
    # Create operation_types table
    create_operation_types_table = """
    CREATE TABLE IF NOT EXISTS operation_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """
    
    # Create events table
    create_events_table = """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_id INTEGER NOT NULL,
        url TEXT,
        html_component TEXT,
        operation_id INTEGER NOT NULL,
        input_text TEXT,
        step_number INTEGER NOT NULL,
        FOREIGN KEY (feature_id) REFERENCES features (id),
        FOREIGN KEY (operation_id) REFERENCES operation_types (id)
    )
    """
    
    # Execute table creation
    conn.execute(create_features_table)
    conn.execute(create_operation_types_table)
    conn.execute(create_events_table)
    
    # Insert predefined operation types if they don't exist
    insert_operation_types = """
    INSERT OR IGNORE INTO operation_types (operation, description) VALUES
    ('click', 'Click on an element'),
    ('input_text', 'Input text into an element'),
    ('scroll', 'Scroll the page or element')
    """
    
    conn.execute(insert_operation_types)
    conn.commit()
    
    return conn


def create_feature(feature_name: str, db_path: str = "database.db") -> int:
    """Create a new feature and return its ID.
    
    Args:
        feature_name: Name of the feature
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created feature
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert feature
        insert_sql = "INSERT INTO features (feature) VALUES (?)"
        cursor = conn.execute(insert_sql, (feature_name,))
        feature_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created feature '{feature_name}' with ID {feature_id}")
        return feature_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to create feature: {e}")
    
    finally:
        conn.close()

def get_all_features(db_path: str = "database.db") -> List[Feature]:
    """Get all features from the database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List[Feature]: List of Feature objects
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, feature FROM features"
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        return [Feature(id=row['id'], feature=row['feature']) for row in rows]
        
    except Exception as e:
        raise RuntimeError(f"Failed to get features: {e}")
    
    finally:
        conn.close()



def get_operation_type_by_name(operation_name: str, db_path: str = "database.db") -> Optional[OperationType]:
    """Get an operation type by name.
    
    Args:
        operation_name: Name of the operation type to find
        db_path: Path to SQLite database file
        
    Returns:
        Optional[OperationType]: OperationType object if found, None otherwise
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT * FROM operation_types WHERE operation = ?"
        cursor = conn.execute(select_sql, (operation_name,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return OperationType(id=row['id'], operation=row['operation'], description=row['description'])
        
    except Exception as e:
        raise RuntimeError(f"Failed to get operation type: {e}")
    
    finally:
        conn.close()


def create_event(feature_name: str, operation_name: str, step_number: int, url: Optional[str] = None, html_component: Optional[str] = None, input_text: Optional[str] = None, db_path: str = "database.db") -> int:
    """Create a new event.
    
    Args:
        feature_name: Name of the feature
        operation_name: Name of the operation type
        step_number: Order of execution
        url: Optional URL to navigate to
        html_component: Optional HTML component selector
        input_text: Optional input text
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created event
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Get feature ID
        feature_id = create_feature(feature_name, db_path)
        
        # Get operation type ID
        operation_type = get_operation_type_by_name(operation_name, db_path)
        if operation_type is None:
            raise ValueError(f"Operation type '{operation_name}' not found")
        
        # Insert event
        insert_sql = "INSERT INTO events (feature_id, url, html_component, operation_id, input_text, step_number) VALUES (?, ?, ?, ?, ?, ?)"
        cursor = conn.execute(insert_sql, (feature_id, url, html_component, operation_type.id, input_text, step_number))
        event_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created event with ID {event_id} for feature '{feature_name}' and operation '{operation_name}'")
        return event_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to create event: {e}")
    
    finally:
        conn.close()


def _get_or_create_feature_id(conn: sqlite3.Connection, feature_name: str) -> int:
    """Get or create a feature and return its ID using existing connection.
    
    Args:
        conn: Existing database connection
        feature_name: Name of the feature
        
    Returns:
        int: ID of the feature
    """
    try:
        # Insert feature
        insert_sql = "INSERT INTO features (feature) VALUES (?)"
        cursor = conn.execute(insert_sql, (feature_name,))
        feature_id = cursor.lastrowid
        
        print(f"Created feature '{feature_name}' with ID {feature_id}")
        return feature_id
        
    except Exception as e:
        raise RuntimeError(f"Failed to get or create feature: {e}")


def _get_operation_type_by_name(conn: sqlite3.Connection, operation_name: str) -> Optional[OperationType]:
    """Get operation type by name using existing connection.
    
    Args:
        conn: Existing database connection
        operation_name: Name of the operation type
        
    Returns:
        OperationType or None if not found
    """
    try:
        select_sql = "SELECT id, operation, description FROM operation_types WHERE operation = ?"
        cursor = conn.execute(select_sql, (operation_name,))
        row = cursor.fetchone()
        
        if row:
            return OperationType(id=row[0], operation=row[1], description=row[2])
        return None
        
    except Exception as e:
        print(f"Error getting operation type '{operation_name}': {e}")
        return None


def create_events(feature_name: str, events: List[dict], db_path: str = "database.db") -> List[int]:
    """Create multiple events for a single feature.
    
    Args:
        feature_name: Name of the feature
        events: List of event dictionaries with keys: operation_name, step_number, url, html_component, input_text
        db_path: Path to SQLite database file
        
    Returns:
        List[int]: List of created event IDs
        
    Example:
        events = [
            {
                "operation_name": "input_text",
                "step_number": 1,
                "url": "https://example.com/login",
                "html_component": "input[id='email']",
                "input_text": "user@example.com"
            },
            {
                "operation_name": "click",
                "step_number": 2,
                "url": "https://example.com/login",
                "html_component": "button[type='submit']",
                "input_text": None
            }
        ]
        event_ids = create_events("Login Feature", events)
    """
    conn = connect_to_sqlite_database(db_path)
    created_event_ids = []
    
    try:
        # Get feature ID (create if doesn't exist) - use existing connection
        feature_id = _get_or_create_feature_id(conn, feature_name)
        print(f"Using feature ID {feature_id} for feature '{feature_name}'")
        
        # Insert all events
        for event in events:
            try:
                # Get operation type ID - use existing connection
                operation_type = _get_operation_type_by_name(conn, event["operation_name"])
                if operation_type is None:
                    print(f"Warning: Operation type '{event['operation_name']}' not found, skipping event")
                    continue
                
                # Insert event
                insert_sql = "INSERT INTO events (feature_id, url, html_component, operation_id, input_text, step_number) VALUES (?, ?, ?, ?, ?, ?)"
                cursor = conn.execute(insert_sql, (
                    feature_id,
                    event.get("url"),
                    event.get("html_component"),
                    operation_type.id,
                    event.get("input_text"),
                    event["step_number"]
                ))
                event_id = cursor.lastrowid
                created_event_ids.append(event_id)
                
                print(f"Created event with ID {event_id} for operation '{event['operation_name']}' (step {event['step_number']})")
                
            except Exception as e:
                print(f"Error creating event for operation '{event.get('operation_name', 'unknown')}': {e}")
                continue
        
        conn.commit()
        print(f"Successfully created {len(created_event_ids)} events for feature '{feature_name}'")
        return created_event_ids
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to create events: {e}")
    
    finally:
        conn.close()


def update_events(feature_id: int, events: List[dict], db_path: str = "database.db") -> List[int]:
    """Update events for a specific feature by deleting existing events and inserting new ones.
    
    Args:
        feature_id: ID of the feature to update events for
        events: List of event dictionaries with keys: operation_name, step_number, url, html_component, input_text
        db_path: Path to SQLite database file
        
    Returns:
        List[int]: List of created event IDs
        
    Example:
        events = [
            {
                "operation_name": "input_text",
                "step_number": 1,
                "url": "https://example.com/login",
                "html_component": "input[id='email']",
                "input_text": "user@example.com"
            },
            {
                "operation_name": "click",
                "step_number": 2,
                "url": "https://example.com/login",
                "html_component": "button[type='submit']",
                "input_text": None
            }
        ]
        event_ids = update_events(1, events)  # Update events for feature_id 1
    """
    conn = connect_to_sqlite_database(db_path)
    created_event_ids = []
    
    try:
        # First, delete all existing events for this feature_id
        delete_sql = "DELETE FROM events WHERE feature_id = ?"
        cursor = conn.execute(delete_sql, (feature_id,))
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} existing events for feature_id {feature_id}")
        
        # Insert all new events
        for event in events:
            try:
                # Get operation type ID - use existing connection
                operation_type = _get_operation_type_by_name(conn, event["operation_name"])
                if operation_type is None:
                    print(f"Warning: Operation type '{event['operation_name']}' not found, skipping event")
                    continue
                
                # Insert event
                insert_sql = "INSERT INTO events (feature_id, url, html_component, operation_id, input_text, step_number) VALUES (?, ?, ?, ?, ?, ?)"
                cursor = conn.execute(insert_sql, (
                    feature_id,
                    event.get("url"),
                    event.get("html_component"),
                    operation_type.id,
                    event.get("input_text"),
                    event["step_number"]
                ))
                event_id = cursor.lastrowid
                created_event_ids.append(event_id)
                
                print(f"Created event with ID {event_id} for operation '{event['operation_name']}' (step {event['step_number']})")
                
            except Exception as e:
                print(f"Error creating event for operation '{event.get('operation_name', 'unknown')}': {e}")
                continue
        
        conn.commit()
        print(f"Successfully updated {len(created_event_ids)} events for feature_id {feature_id}")
        return created_event_ids
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to update events for feature_id {feature_id}: {e}")
    
    finally:
        conn.close()

def get_all_events_with_details(db_path: str = "database.db") -> List[dict]:
    """Get all events with feature and operation details.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List[dict]: List of event dictionaries with details
    """
    from .operation_type import OperationTypeMapper
    
    # Use optimized mapper for operation types
    operation_mapper = OperationTypeMapper(db_path)
    operation_mapper.load_operation_types()
    
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = """
        SELECT 
            e.id,
            e.step_number,
            e.input_text,
            f.feature,
            e.operation_id
        FROM events e
        JOIN features f ON e.feature_id = f.id
        ORDER BY e.step_number
        """
        
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            # Get operation details from mapper
            operation_type = operation_mapper.get_operation_by_id(row['operation_id'])
            
            events.append({
                'id': row['id'],
                'step_number': row['step_number'],
                'input_text': row['input_text'],
                'feature': row['feature'],
                'operation': operation_type.operation if operation_type else 'unknown',
                'description': operation_type.description if operation_type else 'Unknown operation'
            })
        
        return events
        
    except Exception as e:
        raise RuntimeError(f"Failed to get events with details: {e}")
    
    finally:
        conn.close()

def get_events_by_feature_id(feature_id: int, db_path: str = "database.db") -> List[Event]:
    """Get all events for a specific feature ID from SQLite database.
    
    Args:
        feature_id: ID of the feature to get events for
        db_path: Path to SQLite database file
        
    Returns:
        List[Event]: List of Event objects for the specified feature
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Query events for specific feature_id
        select_sql = "SELECT * FROM events WHERE feature_id = ? ORDER BY step_number"
        cursor = conn.execute(select_sql, (feature_id,))
        rows = cursor.fetchall()
        
        events = []
        
        for row in rows:
            try:
                # Create Event object
                action = Event(
                    id=row['id'],
                    feature_id=row['feature_id'], 
                    operation_id=row['operation_id'],
                    url=row['url'],
                    html_component=row['html_component'],
                    input_text=row['input_text'],
                    step_number=row['step_number']
                )
                events.append(action)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid row with id {row['id']}: {e}")
                continue
                
        return events
        
    except Exception as e:
        raise RuntimeError(f"Failed to get events for feature_id {feature_id}: {e}")
    
    finally:
        conn.close()



def get_all_events_from_sqlite(db_path: str = "database.db") -> List[Event]:
    """Read all events from SQLite database and convert them to Event objects.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List[Event]: List of Event objects from the database
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Query all events from database
        select_sql = "SELECT * FROM events ORDER BY id"
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        events = []
        
        for row in rows:
            try:
                # Create Event object
                action = Event(
                    id=row['id'],
                    feature_id=row['feature_id'],
                    operation_id=row['operation_id'],
                    url=row['url'],
                    html_component=row['html_component'],
                    input_text=row['input_text'],
                    step_number=row['step_number']
                )
                events.append(action)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid row with id {row['id']}: {e}")
                continue
        
        return events
        
    except Exception as e:
        raise RuntimeError(f"Failed to read events from SQLite database: {e}")
    
    finally:
        conn.close()


def update_event_in_sqlite(action: Event, db_path: str = "database.db") -> None:
    """Update an existing event in SQLite database.
    
    Args:
        action: Event object to update (must have valid id)
        db_path: Path to SQLite database file
    """
    if action.id is None:
        raise ValueError("Action ID is required for update operation")
    
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Update action in database
        update_sql = """
        UPDATE events 
        SET feature_id = ?, url = ?, html_component = ?, operation_id = ?, input_text = ?, step_number = ?
        WHERE id = ?
        """
        
        cursor = conn.execute(update_sql, (
            action.feature_id,
            action.url,
            action.html_component,
            action.operation_id,
            action.input_text,
            action.step_number,
            action.id
        ))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Action with ID {action.id} not found")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to update action in SQLite database: {e}")
    
    finally:
        conn.close()


def delete_event_from_sqlite(action_id: int, db_path: str = "database.db") -> None:
    """Delete an action from SQLite database.
    
    Args:
        action_id: ID of the action to delete
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Delete action from database
        delete_sql = "DELETE FROM events WHERE id = ?"
        
        cursor = conn.execute(delete_sql, (action_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Action with ID {action_id} not found")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to delete action from SQLite database: {e}")
    
    finally:
        conn.close()


def get_event_by_id(action_id: int, db_path: str = "database.db") -> Optional[Event]:
    """Get a specific action by ID from SQLite database.
    
    Args:
        action_id: ID of the action to retrieve
        db_path: Path to SQLite database file
        
    Returns:
        Optional[Event]: Event object if found, None otherwise
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Query specific action by ID
        select_sql = "SELECT * FROM events WHERE id = ?"
        cursor = conn.execute(select_sql, (action_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        # Create Event object
        action = Event(
            id=row['id'],
            feature_id=row['feature_id'],
            operation_id=row['operation_id'],
            url=row['url'],
            html_component=row['html_component'],
            input_text=row['input_text'],
            step_number=row['step_number']
        )
        
        return action
        
    except Exception as e:
        raise RuntimeError(f"Failed to get action from SQLite database: {e}")
    
    finally:
        conn.close()


def clear_all_events_from_sqlite(db_path: str = "database.db") -> None:
    """Clear all events from SQLite database.
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Delete all events from database
        delete_sql = "DELETE FROM events"
        conn.execute(delete_sql)
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to clear events from SQLite database: {e}")
    
    finally:
        conn.close()


def get_events_count(db_path: str = "database.db") -> int:
    """Get the total number of events in the SQLite database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        int: Number of events in the database
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Count all events
        count_sql = "SELECT COUNT(*) as count FROM events"
        cursor = conn.execute(count_sql)
        row = cursor.fetchone()
        
        return row['count'] if row else 0
        
    except Exception as e:
        raise RuntimeError(f"Failed to count events in SQLite database: {e}")
    
    finally:
        conn.close()
