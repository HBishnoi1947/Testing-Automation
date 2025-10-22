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
        feature TEXT NOT NULL UNIQUE
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


def get_feature_by_name(feature_name: str, db_path: str = "database.db") -> Optional[Feature]:
    """Get a feature by name.
    
    Args:
        feature_name: Name of the feature to find
        db_path: Path to SQLite database file
        
    Returns:
        Optional[Feature]: Feature object if found, None otherwise
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT * FROM features WHERE feature = ?"
        cursor = conn.execute(select_sql, (feature_name,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return Feature(id=row['id'], feature=row['feature'])
        
    except Exception as e:
        raise RuntimeError(f"Failed to get feature: {e}")
    
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
        feature = get_feature_by_name(feature_name, db_path)
        if feature is None:
            feature_id = create_feature(feature_name, db_path)
        else:
            feature_id = feature.id
        
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


def create_bishnoi_shaadi_login_test(db_path: str = "database.db") -> None:
    """Create the Bishnoi Shaadi login test using the new schema.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        # Create events for Bishnoi Shaadi login test
        create_event("Bishnoi Shaadi Login", "input_text", 1, "https://bishnoishaadi.com/login", "input[id='email']", "HARSHBSHNOI@GMAIL.COM", db_path)
        create_event("Bishnoi Shaadi Login", "input_text", 2, "https://bishnoishaadi.com/login", "input[id='password']", "123456", db_path)
        create_event("Bishnoi Shaadi Login", "click", 3, "https://bishnoishaadi.com/login", "button[type='submit']", None, db_path)
        
        print("Successfully created Bishnoi Shaadi login test events")
        
    except Exception as e:
        print(f"Error creating Bishnoi Shaadi login test: {e}")


def save_action_to_sqlite(action: Event, db_path: str = "database.db") -> None:
    """Save the action to SQLite database.
    
    Args:
        action: Event object to save
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert action into database
        insert_sql = """
        INSERT INTO events (feature_id, url, html_component, operation_id, input_text, step_number)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor = conn.execute(insert_sql, (
            action.feature_id,
            action.url,
            action.html_component,
            action.operation_id,
            action.input_text,
            action.step_number
        ))
        
        # Get the auto-generated ID
        action.id = cursor.lastrowid
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to save action to SQLite database: {e}")
    
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


def update_action_in_sqlite(action: Event, db_path: str = "database.db") -> None:
    """Update an existing action in SQLite database.
    
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


def delete_action_from_sqlite(action_id: int, db_path: str = "database.db") -> None:
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


def get_action_by_id(action_id: int, db_path: str = "database.db") -> Optional[Event]:
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
