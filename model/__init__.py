"""
Model package for the Testing Automation POC modules.

This package contains all the data models and database operations
for the testing automation system.
"""

from .enums import OperationTypeEnum
from .feature import Feature
from .operation_type import OperationType, OperationTypeMapper
from .event import Event
from .database import (
    connect_to_sqlite_database,
    create_feature,
    get_feature_by_name,
    get_operation_type_by_name,
    create_event,
    get_all_events_with_details,
    create_bishnoi_shaadi_login_test,
    save_action_to_sqlite,
    get_all_events_from_sqlite,
    update_action_in_sqlite,
    delete_action_from_sqlite,
    get_action_by_id,
    clear_all_events_from_sqlite,
    get_events_count
)

__all__ = [
    'OperationTypeEnum',
    'Feature',
    'OperationType',
    'OperationTypeMapper',
    'Event',
    'connect_to_sqlite_database',
    'create_feature',
    'get_feature_by_name',
    'get_operation_type_by_name',
    'create_event',
    'get_all_events_with_details',
    'create_bishnoi_shaadi_login_test',
    'save_action_to_sqlite',
    'get_all_events_from_sqlite',
    'update_action_in_sqlite',
    'delete_action_from_sqlite',
    'get_action_by_id',
    'clear_all_events_from_sqlite',
    'get_events_count'
]
