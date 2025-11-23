"""
Scheduler Model - Represents a scheduled testing module job
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ScheduledJob:
    """Represents a scheduled testing module job"""
    
    id: Optional[int] = None
    module_id: int = None
    module_name: str = None
    scheduled_date: Optional[str] = None  # For one-time runs (YYYY-MM-DD)
    scheduled_time: str = None  # Time in HH:MM format
    recurring_day: Optional[str] = None  # For recurring runs (Monday, Tuesday, etc. or Daily)
    browser: str = "Chrome"  # Chrome, Edge, Firefox
    headless: bool = False  # Run in headless mode
    is_active: bool = True  # Whether the job is active
    project_id: Optional[int] = None  # Project filter
    created_at: Optional[str] = None  # Creation timestamp
    
    def __post_init__(self):
        """Validate the scheduled job data"""
        # Ensure we have valid schedule type
        if self.scheduled_date and self.recurring_day:
            raise ValueError("Cannot have both scheduled_date and recurring_day set")
        
        if not self.scheduled_date and not self.recurring_day:
            raise ValueError("Must have either scheduled_date or recurring_day set")
        
        # Validate browser
        valid_browsers = ["Chrome", "Edge", "Firefox"]
        if self.browser not in valid_browsers:
            raise ValueError(f"Browser must be one of {valid_browsers}")
        
        # Validate recurring day if set
        if self.recurring_day:
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Daily"]
            if self.recurring_day not in valid_days:
                raise ValueError(f"Recurring day must be one of {valid_days}")
    
    @property
    def is_recurring(self) -> bool:
        """Check if this is a recurring job"""
        return self.recurring_day is not None
    
    @property
    def is_one_time(self) -> bool:
        """Check if this is a one-time job"""
        return self.scheduled_date is not None
    
    @property
    def schedule_type(self) -> str:
        """Get the schedule type as a string"""
        if self.is_recurring:
            return f"Recurring ({self.recurring_day})"
        else:
            return f"One-time ({self.scheduled_date})"
    
    def to_dict(self) -> dict:
        """Convert the scheduled job to a dictionary"""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'module_name': self.module_name,
            'scheduled_date': self.scheduled_date,
            'scheduled_time': self.scheduled_time,
            'recurring_day': self.recurring_day,
            'browser': self.browser,
            'headless': self.headless,
            'is_active': self.is_active,
            'project_id': self.project_id,
            'created_at': self.created_at,
            'schedule_type': self.schedule_type,
            'is_recurring': self.is_recurring
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledJob':
        """Create a ScheduledJob from a dictionary"""
        return cls(
            id=data.get('id'),
            module_id=data.get('module_id'),
            module_name=data.get('module_name'),
            scheduled_date=data.get('scheduled_date'),
            scheduled_time=data.get('scheduled_time'),
            recurring_day=data.get('recurring_day'),
            browser=data.get('browser', 'Chrome'),
            headless=data.get('headless', False),
            is_active=data.get('is_active', True),
            project_id=data.get('project_id'),
            created_at=data.get('created_at')
        )
    
    def __repr__(self) -> str:
        """String representation of the scheduled job"""
        return (f"ScheduledJob(id={self.id}, module='{self.module_name}', "
                f"schedule={self.schedule_type}, time={self.scheduled_time}, "
                f"browser={self.browser}, headless={self.headless})")
