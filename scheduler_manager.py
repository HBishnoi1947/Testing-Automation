"""
Scheduler Manager - Handles Windows Task Scheduler operations
"""

import os
import sys
import subprocess
import platform
from datetime import datetime
from typing import Optional
from datetime import datetime, date, time



class SchedulerManager:
    """Manages Windows Task Scheduler tasks for automated test execution"""
    
    def __init__(self):
        """Initialize the scheduler manager"""
        self.task_prefix = "TestAutomation_"
        self.python_exe = sys.executable
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.execute_script = os.path.join(self.script_dir, "execute.py")
        
        # Verify Windows platform
        if platform.system() != "Windows":
            raise RuntimeError("Task Scheduler is only supported on Windows")
        
        # Verify execute.py exists
        if not os.path.exists(self.execute_script):
            raise FileNotFoundError(f"Execute script not found: {self.execute_script}")
    
    def _get_task_name(self, job_id: int) -> str:
        """Generate task name for a job ID"""
        return f"{self.task_prefix}Job_{job_id}"
    
    def _run_schtasks(self, command: list) -> tuple:
        """
        Run schtasks command
        
        Args:
            command: List of command arguments
        
        Returns:
            tuple: (success, output, error)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        
        except Exception as e:
            return False, "", str(e)
    
    def create_one_time_task(
        self,
        job_id: int,
        module_id: int,
        module_name: str,
        date: str,
        time: str,
        browser: str = "Chrome",
        headless: bool = False
    ) -> bool:
        """Create a one-time scheduled task"""
        task_name = self._get_task_name(job_id)
        
        # Parse and validate date/time
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            time_obj = datetime.strptime(time, "%H:%M")
            
            # Combine date and time to check if it's in the future
            scheduled_datetime = datetime.combine(date_obj.date(), time_obj.time())
            current_datetime = datetime.now()
            
            if scheduled_datetime <= current_datetime:
                print(f"Error: Scheduled time must be in the future!")
                print(f"  Current time: {current_datetime.strftime('%Y-%m-%d %H:%M')}")
                print(f"  Scheduled time: {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
                return False
            
            # Format date for Windows Task Scheduler
            # Use DD/MM/YYYY format (works better across regions)
            formatted_date = date_obj.strftime("%d/%m/%Y")
            
        except ValueError as e:
            print(f"Error: Invalid date or time format: {e}")
            return False
        
        # Build command to execute
        execute_command = (
            f'"{self.python_exe}" "{self.execute_script}" '
            f'--module-id {module_id} '
            f'--module-name "{module_name}" '
            f'--browser {browser} '
            f'--headless {str(headless).lower()}'
        )
        
        # Create scheduled task with proper date format
        schtasks_command = [
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/TR", execute_command,
            "/SC", "ONCE",
            "/SD", formatted_date,
            "/ST", time,
            "/F"  # Force create (overwrite if exists)
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"✓ Created one-time task '{task_name}' for {formatted_date} at {time}")
            print(f"  Module: {module_name} (ID: {module_id})")
            print(f"  Browser: {browser}, Headless: {headless}")
            print(f"  Will execute at: {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"✗ Failed to create task '{task_name}'")
            print(f"  Date format used: {formatted_date}")
            print(f"  Error: {error}")

    
    def create_recurring_task(
        self,
        job_id: int,
        module_id: int,
        module_name: str,
        day: str,
        time: str,
        browser: str = "Chrome",
        headless: bool = False
    ) -> bool:
        """
        Create a recurring scheduled task
        
        Args:
            job_id: ID of the scheduled job
            module_id: ID of the testing module
            module_name: Name of the module
            day: Day of week (Monday, Tuesday, etc.) or "Daily"
            time: Time in HH:MM format
            browser: Browser to use
            headless: Run in headless mode
        
        Returns:
            bool: True if task created successfully
        """
        task_name = self._get_task_name(job_id)
        
        # Build command to execute
        execute_command = (
            f'"{self.python_exe}" "{self.execute_script}" '
            f'--module-id {module_id} '
            f'--module-name "{module_name}" '
            f'--browser {browser} '
            f'--headless {str(headless).lower()}'
        )
        
        # Map day names to schtasks format
        day_mapping = {
            "Monday": "MON",
            "Tuesday": "TUE",
            "Wednesday": "WED",
            "Thursday": "THU",
            "Friday": "FRI",
            "Saturday": "SAT",
            "Sunday": "SUN",
            "Daily": "DAILY"
        }
        
        if day not in day_mapping:
            print(f"Error: Invalid day: {day}")
            return False
        
        schtasks_day = day_mapping[day]
        
        # Create scheduled task
        if day == "Daily":
            schtasks_command = [
                "schtasks",
                "/Create",
                "/TN", task_name,
                "/TR", execute_command,
                "/SC", "DAILY",
                "/ST", time,
                "/F"
            ]
        else:
            schtasks_command = [
                "schtasks",
                "/Create",
                "/TN", task_name,
                "/TR", execute_command,
                "/SC", "WEEKLY",
                "/D", schtasks_day,
                "/ST", time,
                "/F"
            ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"✓ Created recurring task '{task_name}' for every {day} at {time}")
            print(f"  Module: {module_name} (ID: {module_id})")
            print(f"  Browser: {browser}, Headless: {headless}")
        else:
            print(f"✗ Failed to create task '{task_name}'")
            print(f"  Error: {error}")
        
        return success
    
    def delete_task(self, job_id: int) -> bool:
        """
        Delete a scheduled task
        
        Args:
            job_id: ID of the scheduled job
        
        Returns:
            bool: True if task deleted successfully
        """
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Delete",
            "/TN", task_name,
            "/F"  # Force delete without confirmation
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"✓ Deleted task '{task_name}'")
        else:
            # Task might not exist, which is okay
            if "cannot find the file" in error.lower() or "does not exist" in error.lower():
                print(f"✓ Task '{task_name}' does not exist (already deleted)")
                return True
            print(f"✗ Failed to delete task '{task_name}'")
            print(f"  Error: {error}")
        
        return success
    
    def task_exists(self, job_id: int) -> bool:
        """
        Check if a scheduled task exists
        
        Args:
            job_id: ID of the scheduled job
        
        Returns:
            bool: True if task exists
        """
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Query",
            "/TN", task_name
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        return success
    
    def get_task_info(self, job_id: int) -> Optional[dict]:
        """
        Get information about a scheduled task
        
        Args:
            job_id: ID of the scheduled job
        
        Returns:
            Optional[dict]: Task information or None if not found
        """
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Query",
            "/TN", task_name,
            "/V",  # Verbose
            "/FO", "LIST"  # Format as list
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if not success:
            return None
        
        # Parse output into dictionary
        task_info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                task_info[key.strip()] = value.strip()
        
        return task_info
    
    def list_all_tasks(self) -> list:
        """
        List all automation tasks
        
        Returns:
            list: List of task names
        """
        schtasks_command = [
            "schtasks",
            "/Query",
            "/FO", "LIST"
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if not success:
            return []
        
        # Extract task names that match our prefix
        tasks = []
        for line in output.split('\n'):
            if 'TaskName:' in line and self.task_prefix in line:
                task_name = line.split(':', 1)[1].strip()
                # Extract job ID from task name
                try:
                    job_id = int(task_name.split('_')[-1])
                    tasks.append({'task_name': task_name, 'job_id': job_id})
                except:
                    pass
        
        return tasks
    
    def run_task_now(self, job_id: int) -> bool:
        """
        Run a scheduled task immediately
        
        Args:
            job_id: ID of the scheduled job
        
        Returns:
            bool: True if task started successfully
        """
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Run",
            "/TN", task_name
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"✓ Started task '{task_name}' immediately")
        else:
            print(f"✗ Failed to start task '{task_name}'")
            print(f"  Error: {error}")
        
        return success


# Utility functions for standalone use
def create_one_time_schedule(job_id: int, module_id: int, module_name: str, 
                             date: str, time: str, browser: str = "Chrome", 
                             headless: bool = False) -> bool:
    """Create a one-time schedule (standalone function)"""
    manager = SchedulerManager()
    return manager.create_one_time_task(job_id, module_id, module_name, date, time, browser, headless)


def create_recurring_schedule(job_id: int, module_id: int, module_name: str,
                              day: str, time: str, browser: str = "Chrome",
                              headless: bool = False) -> bool:
    """Create a recurring schedule (standalone function)"""
    manager = SchedulerManager()
    return manager.create_recurring_task(job_id, module_id, module_name, day, time, browser, headless)


def delete_schedule(job_id: int) -> bool:
    """Delete a schedule (standalone function)"""
    manager = SchedulerManager()
    return manager.delete_task(job_id)


if __name__ == "__main__":
    # Test the scheduler manager
    print("=== Scheduler Manager Test ===")
    
    manager = SchedulerManager()
    
    # List all tasks
    print("\nExisting tasks:")
    tasks = manager.list_all_tasks()
    if tasks:
        for task in tasks:
            print(f"  - {task['task_name']} (Job ID: {task['job_id']})")
    else:
        print("  No tasks found")
    
    print("\nScheduler Manager is ready!")
