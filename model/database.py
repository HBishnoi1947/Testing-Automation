"""
Database operations for the testing automation system.
"""

import sqlite3
import os
from typing import Optional, List
from .feature import Feature
from .project import Project
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
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Create projects table
    create_projects_table = """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Create features table with project_id foreign key
    create_features_table = """
    CREATE TABLE IF NOT EXISTS features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature TEXT NOT NULL,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
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
        FOREIGN KEY (feature_id) REFERENCES features (id) ON DELETE CASCADE,
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
        feature_id INTEGER,
        step_number INTEGER NOT NULL,
        FOREIGN KEY (testing_module_id) REFERENCES testing_modules (id),
        FOREIGN KEY (feature_id) REFERENCES features (id)
    )
    """
    
    # Create module_execution_reports table
    create_module_execution_reports_table = """
    CREATE TABLE IF NOT EXISTS module_execution_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        execution_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_features INTEGER,
        passed_features INTEGER,
        failed_features INTEGER,
        report_json TEXT,
        FOREIGN KEY (module_id) REFERENCES testing_modules(id)
    )
    """
    
    # Execute table creation
    conn.execute(create_projects_table)
    conn.execute(create_features_table)
    conn.execute(create_operation_types_table)
    conn.execute(create_events_table)
    conn.execute(create_testing_module_table)
    conn.execute(create_map_testing_module_table)
    conn.execute(create_module_execution_reports_table)
    
    # Insert predefined operation types if they don't exist
    insert_operation_types = """
    INSERT OR IGNORE INTO operation_types (operation, description) VALUES
    ('click', 'Click on an element'),
    ('input_text', 'Input text into an element'),
    ('scroll', 'Scroll the page or element'),
    ('verify_element', 'Verify element exists on page')
    """
    
    conn.execute(insert_operation_types)
    conn.commit()
    
    return conn


# ==================== PROJECT OPERATIONS ====================

def create_project(name: str, description: str = None, db_path: str = "database.db") -> int:
    """Create a new project and return its ID.
    
    Args:
        name: Name of the project
        description: Optional description of the project
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created project
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert project
        insert_sql = "INSERT INTO projects (name, description) VALUES (?, ?)"
        cursor = conn.execute(insert_sql, (name, description))
        project_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created project '{name}' with ID {project_id}")
        return project_id
        
    except sqlite3.IntegrityError:
        raise RuntimeError(f"Project with name '{name}' already exists")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to create project: {e}")
    
    finally:
        conn.close()


def get_all_projects(db_path: str = "database.db") -> List[Project]:
    """Get all projects from the database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List[Project]: List of Project objects
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, name, description, created_at FROM projects ORDER BY created_at DESC"
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        return [Project(
            id=row['id'], 
            name=row['name'], 
            description=row['description'],
            created_at=row['created_at']
        ) for row in rows]
        
    except Exception as e:
        raise RuntimeError(f"Failed to get projects: {e}")
    
    finally:
        conn.close()


def get_project_by_id(project_id: int, db_path: str = "database.db") -> Optional[Project]:
    """Get a specific project by ID.
    
    Args:
        project_id: ID of the project
        db_path: Path to SQLite database file
        
    Returns:
        Optional[Project]: Project object if found, None otherwise
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, name, description, created_at FROM projects WHERE id = ?"
        cursor = conn.execute(select_sql, (project_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            created_at=row['created_at']
        )
        
    except Exception as e:
        raise RuntimeError(f"Failed to get project: {e}")
    
    finally:
        conn.close()


def update_project(project_id: int, name: str = None, description: str = None, db_path: str = "database.db") -> None:
    """Update a project's details.
    
    Args:
        project_id: ID of the project to update
        name: New name for the project (optional)
        description: New description for the project (optional)
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Build update query dynamically based on what's provided
        update_parts = []
        params = []
        
        if name is not None:
            update_parts.append("name = ?")
            params.append(name)
        
        if description is not None:
            update_parts.append("description = ?")
            params.append(description)
        
        if not update_parts:
            return  # Nothing to update
        
        params.append(project_id)
        update_sql = f"UPDATE projects SET {', '.join(update_parts)} WHERE id = ?"
        
        cursor = conn.execute(update_sql, params)
        
        if cursor.rowcount == 0:
            raise ValueError(f"Project with ID {project_id} not found")
        
        conn.commit()
        print(f"Updated project with ID {project_id}")
        
    except sqlite3.IntegrityError:
        raise RuntimeError(f"Project with name '{name}' already exists")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to update project: {e}")
    
    finally:
        conn.close()


def delete_project(project_id: int, db_path: str = "database.db") -> None:
    """Delete a project and all its associated features and events (CASCADE).
    
    Args:
        project_id: ID of the project to delete
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Delete project (will cascade to features and events)
        delete_sql = "DELETE FROM projects WHERE id = ?"
        cursor = conn.execute(delete_sql, (project_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Project with ID {project_id} not found")
        
        conn.commit()
        print(f"Deleted project with ID {project_id} and all associated data")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to delete project: {e}")
    
    finally:
        conn.close()


# ==================== FEATURE OPERATIONS ====================

def create_feature(feature_name: str, project_id: int, db_path: str = "database.db") -> int:
    """Create a new feature and return its ID.
    
    Args:
        feature_name: Name of the feature
        project_id: ID of the project this feature belongs to
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created feature
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Insert feature
        insert_sql = "INSERT INTO features (feature, project_id) VALUES (?, ?)"
        cursor = conn.execute(insert_sql, (feature_name, project_id))
        feature_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created feature '{feature_name}' with ID {feature_id} for project {project_id}")
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
        select_sql = "SELECT id, feature, project_id FROM features"
        cursor = conn.execute(select_sql)
        rows = cursor.fetchall()
        
        return [Feature(id=row['id'], feature=row['feature'], project_id=row['project_id']) for row in rows]
        
    except Exception as e:
        raise RuntimeError(f"Failed to get features: {e}")
    
    finally:
        conn.close()


def get_features_by_project(project_id: int, db_path: str = "database.db") -> List[Feature]:
    """Get all features for a specific project.
    
    Args:
        project_id: ID of the project
        db_path: Path to SQLite database file
        
    Returns:
        List[Feature]: List of Feature objects for the project
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, feature, project_id FROM features WHERE project_id = ?"
        cursor = conn.execute(select_sql, (project_id,))
        rows = cursor.fetchall()
        
        return [Feature(id=row['id'], feature=row['feature'], project_id=row['project_id']) for row in rows]
        
    except Exception as e:
        raise RuntimeError(f"Failed to get features for project: {e}")
    
    finally:
        conn.close()


def get_feature_by_id(feature_id: int, db_path: str = "database.db") -> Optional[Feature]:
    """Get a specific feature by ID.
    
    Args:
        feature_id: ID of the feature
        db_path: Path to SQLite database file
        
    Returns:
        Optional[Feature]: Feature object if found, None otherwise
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        select_sql = "SELECT id, feature, project_id FROM features WHERE id = ?"
        cursor = conn.execute(select_sql, (feature_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return Feature(id=row['id'], feature=row['feature'], project_id=row['project_id'])
        
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


# ==================== OPERATION TYPE OPERATIONS ====================

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


# ==================== EVENT OPERATIONS ====================

def create_event(
    feature_name: str,
    project_id: int,
    operation_name: str,
    step_number: int,
    url: str,
    html_component: str,
    input_text: str = None,
    db_path: str = "database.db"
) -> int:
    """Create a new event.
    
    Args:
        feature_name: Name of the feature
        project_id: ID of the project
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
        # Get or create feature ID
        feature_id = create_feature(feature_name, project_id, db_path)
        
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


def _get_or_create_feature_id(conn: sqlite3.Connection, feature_name: str, project_id: int) -> int:
    """Get or create a feature and return its ID using existing connection.
    
    Args:
        conn: Existing database connection
        feature_name: Name of the feature
        project_id: ID of the project
        
    Returns:
        int: ID of the feature
    """
    try:
        # Insert feature
        insert_sql = "INSERT INTO features (feature, project_id) VALUES (?, ?)"
        cursor = conn.execute(insert_sql, (feature_name, project_id))
        feature_id = cursor.lastrowid
        
        print(f"Created feature '{feature_name}' with ID {feature_id} for project {project_id}")
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


def create_events(feature_name: str, project_id: int, events: List[dict], db_path: str = "database.db") -> List[int]:
    """Create multiple events for a single feature.
    
    Args:
        feature_name: Name of the feature
        project_id: ID of the project
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
        event_ids = create_events("Login Feature", 1, events)
    """
    conn = connect_to_sqlite_database(db_path)
    created_event_ids = []
    
    try:
        # Get feature ID (create if doesn't exist) - use existing connection
        feature_id = _get_or_create_feature_id(conn, feature_name, project_id)
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
            e.operation_id,
            f.project_id
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
                'project_id': row['project_id'],
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


def get_events_count_by_project(project_id: int, db_path: str = "database.db") -> int:
    """Get the total number of events for a specific project.
    
    Args:
        project_id: ID of the project
        db_path: Path to SQLite database file
        
    Returns:
        int: Number of events in the project
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        count_sql = """
        SELECT COUNT(*) as count 
        FROM events e
        JOIN features f ON e.feature_id = f.id
        WHERE f.project_id = ?
        """
        cursor = conn.execute(count_sql, (project_id,))
        row = cursor.fetchone()
        
        return row['count'] if row else 0
        
    except Exception as e:
        raise RuntimeError(f"Failed to count events for project: {e}")
    
    finally:
        conn.close()


def get_features_count_by_project(project_id: int, db_path: str = "database.db") -> int:
    """Get the total number of features for a specific project.
    
    Args:
        project_id: ID of the project
        db_path: Path to SQLite database file
        
    Returns:
        int: Number of features in the project
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        count_sql = "SELECT COUNT(*) as count FROM features WHERE project_id = ?"
        cursor = conn.execute(count_sql, (project_id,))
        row = cursor.fetchone()
        
        return row['count'] if row else 0
        
    except Exception as e:
        raise RuntimeError(f"Failed to count features for project: {e}")
    
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
    """Deprecated: Event-level flows are not supported. Use add_feature_to_testing_module instead."""
    raise NotImplementedError("Event-level flows have been removed. Use add_feature_to_testing_module().")


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
        # Validate if the feature_id exists in the features table
        check_feature_sql = "SELECT 1 FROM features WHERE id = ?"
        cursor = conn.execute(check_feature_sql, (feature_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Feature ID {feature_id} does not exist in the database.")
        # Insert mapping for feature-only flow
        insert_sql = """
        INSERT INTO map_testing_modules (testing_module_id, feature_id, step_number) 
        VALUES (?, ?, ?)
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
            mtm.feature_id,
            f.feature as feature_name
        FROM map_testing_modules mtm
        LEFT JOIN features f ON mtm.feature_id = f.id
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
                'feature_id': row['feature_id'],
                'feature_name': row['feature_name'],
                'type': 'feature'
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


def reorder_testing_module_step(mapping_id: int, new_step_number: int, db_path: str = "database.db") -> None:
    """Reorder an item in a testing module by updating its step number.
    Swaps step numbers with the item at the target position.
    
    Args:
        mapping_id: ID of the mapping to move
        new_step_number: New step number position (1-based)
        db_path: Path to SQLite database file
    """
    conn = connect_to_sqlite_database(db_path)
    
    try:
        # Get current step and module info
        select_sql = "SELECT testing_module_id, step_number FROM map_testing_modules WHERE id = ?"
        cursor = conn.execute(select_sql, (mapping_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Mapping with ID {mapping_id} not found")
        
        module_id = row['testing_module_id']
        old_step = row['step_number']
        
        # Validate new step number
        count_sql = "SELECT COUNT(*) as count FROM map_testing_modules WHERE testing_module_id = ?"
        cursor = conn.execute(count_sql, (module_id,))
        total_items = cursor.fetchone()['count']
        
        if new_step_number < 1 or new_step_number > total_items:
            raise ValueError(f"New step number {new_step_number} is out of range (1-{total_items})")
        
        if old_step == new_step_number:
            return  # No change needed
        
        # Get the mapping ID at the target position
        target_select_sql = "SELECT id FROM map_testing_modules WHERE testing_module_id = ? AND step_number = ?"
        cursor = conn.execute(target_select_sql, (module_id, new_step_number))
        target_row = cursor.fetchone()
        
        if not target_row:
            raise ValueError(f"No item found at step {new_step_number}")
        
        target_mapping_id = target_row['id']
        
        # Swap step numbers using a temporary value
        # First, set the moving item to a temporary negative value
        temp_step = -(abs(old_step) + abs(new_step_number) + 1000)
        update1_sql = "UPDATE map_testing_modules SET step_number = ? WHERE id = ?"
        conn.execute(update1_sql, (temp_step, mapping_id))
        
        # Set target item to old step
        update2_sql = "UPDATE map_testing_modules SET step_number = ? WHERE id = ?"
        conn.execute(update2_sql, (old_step, target_mapping_id))
        
        # Set moving item to new step
        update3_sql = "UPDATE map_testing_modules SET step_number = ? WHERE id = ?"
        conn.execute(update3_sql, (new_step_number, mapping_id))
        
        conn.commit()
        print(f"Reordered mapping {mapping_id} from step {old_step} to step {new_step_number}")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to reorder testing module step: {e}")
    
    finally:
        conn.close()

#Devesh
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
        
        # Delete all execution reports for this module
        delete_reports_sql = "DELETE FROM module_execution_reports WHERE module_id = ?"
        cursor = conn.execute(delete_reports_sql, (module_id,))
        reports_deleted = cursor.rowcount
        
        # Then delete the module
        delete_module_sql = "DELETE FROM testing_modules WHERE id = ?"
        cursor = conn.execute(delete_module_sql, (module_id,))
        
        if cursor.rowcount == 0:
            raise ValueError(f"Testing module with ID {module_id} not found")
        
        conn.commit()
        print(f"Deleted testing module {module_id}, {mappings_deleted} mappings, and {reports_deleted} execution reports")
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to delete testing module: {e}")
    
    finally:
        conn.close()


# Execution Logs Functions

def log_execution_attempt(feature_id: int,
                         attempt_number: int,
                         validation_result: Optional[dict] = None,
                         final_dom_path: Optional[str] = None,
                         db_path: str = "database.db") -> int:
    """
    Log an execution attempt with validation results.
    
    Args:
        feature_id: ID of the feature executed
        attempt_number: Attempt number (1, 2, 3, etc.)
        validation_result: Dict with validation results
        final_dom_path: Path to final DOM file
        db_path: Path to SQLite database file
        
    Returns:
        int: ID of the created log entry
    """
    conn = connect_to_sqlite_database(db_path)
    try:
        validation_success = None
        validation_confidence = None
        validation_reason = None
        validation_suggestions = None
        
        if validation_result:
            validation_success = validation_result.get('success')
            validation_confidence = validation_result.get('confidence')
            validation_reason = validation_result.get('reason')
            validation_suggestions = validation_result.get('suggestions')
        
        insert_sql = """
        INSERT INTO execution_logs 
        (feature_id, attempt_number, validation_success, validation_confidence, 
         validation_reason, validation_suggestions, final_dom_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = conn.execute(insert_sql, (
            feature_id, attempt_number, validation_success, validation_confidence,
            validation_reason, validation_suggestions, final_dom_path
        ))
        log_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Logged execution attempt {attempt_number} for feature_id {feature_id}")
        return log_id
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to log execution attempt: {e}")
    finally:
        conn.close()


def get_execution_logs(feature_id: int, db_path: str = "database.db") -> List[dict]:
    """
    Get all execution logs for a specific feature.
    
    Args:
        feature_id: ID of the feature
        db_path: Path to SQLite database file
        
    Returns:
        List[Dict]: List of execution log dictionaries
    """
    conn = connect_to_sqlite_database(db_path)
    try:
        select_sql = """
        SELECT * FROM execution_logs 
        WHERE feature_id = ? 
        ORDER BY execution_timestamp DESC
        """
        cursor = conn.execute(select_sql, (feature_id,))
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row['id'],
                'feature_id': row['feature_id'],
                'attempt_number': row['attempt_number'],
                'execution_timestamp': row['execution_timestamp'],
                'validation_success': row['validation_success'],
                'validation_confidence': row['validation_confidence'],
                'validation_reason': row['validation_reason'],
                'validation_suggestions': row['validation_suggestions'],
                'final_dom_path': row['final_dom_path']
            })
        return logs
    except Exception as e:
        raise RuntimeError(f"Failed to get execution logs: {e}")
    finally:
        conn.close()

def add_single_event_to_feature(feature_id: int, event_dict: dict, db_path: str = "database.db") -> int:
    """
    Add a single event to an existing feature.
    
    Args:
        feature_id: ID of the existing feature
        event_dict: Dict with keys: operation_name, step_number, url, html_component, input_text
        db_path: Path to database
        
    Returns:
        int: ID of created event
        
    Raises:
        RuntimeError: If event creation fails
    """
    conn = connect_to_sqlite_database(db_path)
    try:
        # Get operation type
        operation_type = get_operation_type_by_name(event_dict['operation_name'], db_path)
        
        # Insert event
        insert_sql = """
        INSERT INTO events (feature_id, url, html_component, operation_id, input_text, step_number)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor = conn.execute(
            insert_sql,
            (
                feature_id,
                event_dict.get('url'),
                event_dict.get('html_component'),
                operation_type.id,
                event_dict.get('input_text'),
                event_dict.get('step_number', 1)
            )
        )
        conn.commit()
        event_id = cursor.lastrowid
        print(f"Created event with ID {event_id} for feature_id {feature_id}")
        return event_id
        
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to add event to feature: {e}")
    finally:
        conn.close()

def get_features_in_module(module_id: int, db_path: str = "database.db") -> List:
    """
    Get all features belonging to a module.
    
    Returns:
        List of Feature objects with their events
    """
    from model.feature import Feature
    
    conn = connect_to_sqlite_database(db_path)
    try:
        # Get feature IDs from map_testing_modules
        select_sql = """
        SELECT feature_id FROM map_testing_modules 
        WHERE testing_module_id = ? 
        ORDER BY step_number
        """
        cursor = conn.execute(select_sql, (module_id,))
        rows = cursor.fetchall()
        
        features = []
        for row in rows:
            feature_id = row['feature_id']
            feature = get_feature_by_id(feature_id, db_path)
            if feature:
                features.append(feature)
        
        return features
        
    except Exception as e:
        print(f"Error getting features in module: {e}")
        return []
    finally:
        conn.close()


def save_module_execution_report(module_id: int, report_data: dict, db_path: str = "database.db") -> int:
    """
    Save module execution report to database.
    
    Args:
        module_id: ID of the module
        report_data: Dict containing execution results
        
    Returns:
        int: Report ID
    """
    import json
    from datetime import datetime
    
    conn = connect_to_sqlite_database(db_path)
    try:
        # Insert report
        insert_sql = """
        INSERT INTO module_execution_reports 
        (module_id, total_features, passed_features, failed_features, report_json)
        VALUES (?, ?, ?, ?, ?)
        """
        
        cursor = conn.execute(
            insert_sql,
            (
                module_id,
                report_data.get('total_features', 0),
                report_data.get('passed_features', 0),
                report_data.get('failed_features', 0),
                json.dumps(report_data)
            )
        )
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving report: {e}")
        return 0
    finally:
        conn.close()

def delete_verification_event(feature_id: int, db_path: str = "database.db") -> bool:
    """
    Delete existing verification event for a feature.
    Used before updating/regenerating events.
    
    Args:
        feature_id: ID of the feature
        db_path: Path to database
        
    Returns:
        bool: True if deleted, False if none found
    """
    conn = connect_to_sqlite_database(db_path)
    try:
        # Get verify_element operation_id
        cursor = conn.execute(
            "SELECT id FROM operation_types WHERE operation = 'verify_element'"  # ✅ FIXED: operation_types
        )
        row = cursor.fetchone()
        if not row:
            print(f"[DB] Warning: verify_element operation not found in operation_types table")
            return False
        
        verify_operation_id = row['id']
        
        # Delete verification event
        cursor = conn.execute(
            "DELETE FROM events WHERE feature_id = ? AND operation_id = ?",
            (feature_id, verify_operation_id)
        )
        conn.commit()
        
        deleted_count = cursor.rowcount
        print(f"[DB] Deleted {deleted_count} verification event(s) for feature_id {feature_id}")
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"[DB] Error deleting verification event: {e}")
        return False
    finally:
        conn.close()