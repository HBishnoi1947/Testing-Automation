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
    
    # Create testing_module table
    create_testing_module_table = """
    CREATE TABLE IF NOT EXISTS testing_modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        testing_module TEXT NOT NULL UNIQUE
    )
    """
    
    # Create map_testing_modules table
    create_map_testing_module_table = """
    CREATE TABLE IF NOT EXISTS map_testing_modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        testing_module_id INTEGER NOT NULL,
        event_id INTEGER,
        feature_id INTEGER,
        step_number INTEGER NOT NULL,
        FOREIGN KEY (testing_module_id) REFERENCES testing_modules (id),
        FOREIGN KEY (event_id) REFERENCES events (id),
        FOREIGN KEY (feature_id) REFERENCES features (id)
    )
    """
    
    # Execute table creation
    conn.execute(create_features_table)
    conn.execute(create_operation_types_table)
    conn.execute(create_events_table)
    conn.execute(create_testing_module_table)
    conn.execute(create_map_testing_module_table)
    
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

def delete_feature_by_feature_id(feature_id: int, db_path: str = "database.db") -> None:
    """
    Delete a feature by its ID. This will also delete all events mapped to that feature,
    and before deleting, will check if the feature is mapped to a testing module and remove those mappings.

    Args:
        feature_id: ID of the feature
        db_path: Path to SQLite database file

    Raises:
        ValueError: If the feature does not exist.
        RuntimeError: On database failure.
    """
    conn = connect_to_sqlite_database(db_path)
    try:
        # Check if the feature exists
        cursor = conn.execute("SELECT id FROM features WHERE id = ?", (feature_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Feature with ID {feature_id} does not exist.")

        # Check if feature is mapped to a testing module
        cursor = conn.execute("SELECT COUNT(*) as count FROM map_testing_modules WHERE feature_id = ?", (feature_id,))
        mapping_row = cursor.fetchone()
        if mapping_row and mapping_row['count'] > 0:
            raise ValueError(f"Feature with ID {feature_id} is mapped to a testing module and cannot be deleted.")

        # Delete all events mapped to this feature
        conn.execute("DELETE FROM events WHERE feature_id = ?", (feature_id,))

        # Delete the feature itself
        conn.execute("DELETE FROM features WHERE id = ?", (feature_id,))

        conn.commit()
        print(f"Deleted feature ID {feature_id}, associated mappings in testing modules, and all linked events.")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to delete feature ID {feature_id}: {e}")
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


# Testing Module Functions

def create_testing_module(module_name: str, db_path: str = "database.db") -> int:
    """Create a new testing module and return its ID.
    
    Args:
        module_name: Name of the testing module
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created testing module
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert testing module
        insert_sql = "INSERT INTO testing_modules (testing_module) VALUES (?)"
        cursor = conn.execute(insert_sql, (module_name,))
        module_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created testing module '{module_name}' with ID {module_id}")
        return module_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to create testing module: {e}")
    
    finally:
        conn.close()


def get_all_testing_modules(db_path: str = "database.db") -> List[dict]:
    """Get all testing modules from the database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List[dict]: List of testing module dictionaries
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, testing_module FROM testing_modules ORDER BY id"
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        return [{'id': row['id'], 'testing_module': row['testing_module']} for row in rows]
        
    except Exception as e:
        raise RuntimeError(f"Failed to get testing modules: {e}")
    
    finally:
        conn.close()


def add_event_to_testing_module(module_id: int, event_id: int, step_number: int, db_path: str = "database.db") -> int:
    """Add an event to a testing module.
    
    Args:
        module_id: ID of the testing module
        event_id: ID of the event to add
        step_number: Step number in the sequence
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created mapping
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Get feature_id from event
        event_sql = "SELECT feature_id FROM events WHERE id = ?"
        cursor = conn.execute(event_sql, (event_id,))
        event_row = cursor.fetchone()
        
        if not event_row:
            raise ValueError(f"Event with ID {event_id} not found")
        
        feature_id = event_row['feature_id']
        
        # Insert mapping
        insert_sql = """
        INSERT INTO map_testing_modules (testing_module_id, event_id, feature_id, step_number) 
        VALUES (?, ?, ?, ?)
        """
        cursor = conn.execute(insert_sql, (module_id, event_id, feature_id, step_number))
        mapping_id = cursor.lastrowid
        conn.commit()
        
        print(f"Added event {event_id} to testing module {module_id} at step {step_number}")
        return mapping_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to add event to testing module: {e}")
    
    finally:
        conn.close()


def add_feature_to_testing_module(module_id: int, feature_id: int, step_number: int, db_path: str = "database.db") -> int:
    """Add a feature to a testing module.
    
    Args:
        module_id: ID of the testing module
        feature_id: ID of the feature to add
        step_number: Step number in the sequence
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created mapping
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert mapping (event_id will be NULL for feature-only entries)
        insert_sql = """
        INSERT INTO map_testing_modules (testing_module_id, event_id, feature_id, step_number) 
        VALUES (?, NULL, ?, ?)
        """
        cursor = conn.execute(insert_sql, (module_id, feature_id, step_number))
        mapping_id = cursor.lastrowid
        conn.commit()
        
        print(f"Added feature {feature_id} to testing module {module_id} at step {step_number}")
        return mapping_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to add feature to testing module: {e}")
    
    finally:
        conn.close()


def get_testing_module_flow(module_id: int, db_path: str = "database.db") -> List[dict]:
    """Get the complete flow for a testing module.
    
    Args:
        module_id: ID of the testing module
        db_path: Path to SQLite database file
        
    Returns:
        List[dict]: List of flow items with details
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = """
        SELECT 
            mtm.id,
            mtm.step_number,
            mtm.event_id,
            mtm.feature_id,
            f.feature as feature_name,
            e.url,
            e.html_component,
            e.input_text,
            ot.operation,
            ot.description
        FROM map_testing_modules mtm
        LEFT JOIN features f ON mtm.feature_id = f.id
        LEFT JOIN events e ON mtm.event_id = e.id
        LEFT JOIN operation_types ot ON e.operation_id = ot.id
        WHERE mtm.testing_module_id = ?
        ORDER BY mtm.step_number
        """
        
        cursor = conn.execute(select_sql, (module_id,))
        rows = cursor.fetchall()
        
        flow_items = []
        for row in rows:
            flow_items.append({
                'mapping_id': row['id'],
                'step_number': row['step_number'],
                'event_id': row['event_id'],
                'feature_id': row['feature_id'],
                'feature_name': row['feature_name'],
                'url': row['url'],
                'html_component': row['html_component'],
                'input_text': row['input_text'],
                'operation': row['operation'],
                'description': row['description'],
                'type': 'event' if row['event_id'] else 'feature'
            })
        
        return flow_items
        
    except Exception as e:
        raise RuntimeError(f"Failed to get testing module flow: {e}")
    
    finally:
        conn.close()


def remove_from_testing_module(mapping_id: int, db_path: str = "database.db") -> None:
    """Remove an item from a testing module.
    
    Args:
        mapping_id: ID of the mapping to remove
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # First, get the module_id and step_number of the item being removed
        select_sql = "SELECT testing_module_id, step_number FROM map_testing_modules WHERE id = ?"
        cursor = conn.execute(select_sql, (mapping_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Mapping with ID {mapping_id} not found")
        
        module_id, removed_step = row['testing_module_id'], row['step_number']
        
        # Delete the item
        delete_sql = "DELETE FROM map_testing_modules WHERE id = ?"
        cursor = conn.execute(delete_sql, (mapping_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Mapping with ID {mapping_id} not found")
        
        # Reorder step numbers for remaining items
        reorder_sql = """
        UPDATE map_testing_modules 
        SET step_number = step_number - 1 
        WHERE testing_module_id = ? AND step_number > ?
        """
        cursor = conn.execute(reorder_sql, (module_id, removed_step))
        
        conn.commit()
        print(f"Removed mapping {mapping_id} from testing module and reordered steps")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to remove from testing module: {e}")
    
    finally:
        conn.close()


def clear_testing_module_flow(module_id: int, db_path: str = "database.db") -> None:
    """Clear all items from a testing module.
    
    Args:
        module_id: ID of the testing module
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        delete_sql = "DELETE FROM map_testing_modules WHERE testing_module_id = ?"
        cursor = conn.execute(delete_sql, (module_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"Cleared {deleted_count} items from testing module {module_id}")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to clear testing module flow: {e}")
    
    finally:
        conn.close()


def delete_testing_module(module_id: int, db_path: str = "database.db") -> None:
    """Delete a testing module and all its mappings.
    
    Args:
        module_id: ID of the testing module to delete
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # First delete all mappings
        delete_mappings_sql = "DELETE FROM map_testing_modules WHERE testing_module_id = ?"
        cursor = conn.execute(delete_mappings_sql, (module_id,))
        mappings_deleted = cursor.rowcount
        
        # Then delete the module
        delete_module_sql = "DELETE FROM testing_modules WHERE id = ?"
        cursor = conn.execute(delete_module_sql, (module_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Testing module with ID {module_id} not found")
        
        conn.commit()
        print(f"Deleted testing module {module_id} and {mappings_deleted} mappings")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to delete testing module: {e}")
    
    finally:
        conn.close()
