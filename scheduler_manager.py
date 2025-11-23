"""
Scheduler Manager - Handles Windows Task Scheduler operations
Uses batch file wrapper to avoid command length limits
Automatically disables AC power requirements
"""

import os
import sys
import subprocess
import platform
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional


class SchedulerManager:
    """Manages Windows Task Scheduler tasks for automated test execution"""
    
    def __init__(self):
        """Initialize the scheduler manager"""
        self.task_prefix = "TestAutomation_"
        self.python_exe = sys.executable
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.execute_script = os.path.join(self.script_dir, "execute.py")
        self.batch_dir = os.path.join(self.script_dir, "scheduler_tasks")
        
        # Create batch directory if it doesn't exist
        if not os.path.exists(self.batch_dir):
            os.makedirs(self.batch_dir)
        
        # Verify Windows platform
        if platform.system() != "Windows":
            raise RuntimeError("Task Scheduler is only supported on Windows")
        
        # Verify execute.py exists
        if not os.path.exists(self.execute_script):
            raise FileNotFoundError(f"Execute script not found: {self.execute_script}")
        
        print(f"Scheduler Manager initialized:")
        print(f"  Python: {self.python_exe}")
        print(f"  Script: {self.execute_script}")
        print(f"  Working Dir: {self.script_dir}")
        print(f"  Batch Dir: {self.batch_dir}")
    
    def _get_task_name(self, job_id: int) -> str:
        """Generate task name for a job ID"""
        return f"{self.task_prefix}Job_{job_id}"
    
    def _get_batch_file_path(self, job_id: int) -> str:
        """Generate batch file path for a job ID"""
        return os.path.join(self.batch_dir, f"job_{job_id}.bat")
    
    def _create_batch_file(
        self,
        job_id: int,
        module_id: int,
        module_name: str,
        browser: str,
        headless: bool
    ) -> str:
        """
        Create a batch file to execute the module with logging
        
        Returns:
            str: Path to the created batch file
        """
        batch_file = self._get_batch_file_path(job_id)
        log_file = os.path.join(self.batch_dir, f"job_{job_id}_log.txt")
        
        # Create batch file content with logging
        batch_content = f"""@echo off
REM Scheduled Task Batch File for Job {job_id}
REM Module: {module_name} (ID: {module_id})
REM Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo ================================================================================ > "{log_file}"
echo SCHEDULED TASK EXECUTION - Job {job_id} >> "{log_file}"
echo Module: {module_name} >> "{log_file}"
echo Start Time: %date% %time% >> "{log_file}"
echo ================================================================================ >> "{log_file}"
echo. >> "{log_file}"

cd /d "{self.script_dir}"
echo Working Directory: %CD% >> "{log_file}"
echo. >> "{log_file}"

echo Executing Python Script... >> "{log_file}"
"{self.python_exe}" "{self.execute_script}" --module-id {module_id} --module-name "{module_name}" --browser {browser} --headless {str(headless).lower()} >> "{log_file}" 2>&1

echo. >> "{log_file}"
echo ================================================================================ >> "{log_file}"
echo End Time: %date% %time% >> "{log_file}"
echo Exit Code: %ERRORLEVEL% >> "{log_file}"
echo ================================================================================ >> "{log_file}"

REM Keep window open for 5 seconds to see output
timeout /t 5 /nobreak > nul
"""
        
        # Write batch file
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"  [OK] Created batch file: {batch_file}")
        print(f"  [OK] Log file will be: {log_file}")
        return batch_file
    
    def _run_schtasks(self, command: list) -> tuple:
        """Run schtasks command"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=False
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        
        except Exception as e:
            return False, "", str(e)
    
    def _disable_power_conditions(self, job_id: int) -> bool:
        """
        Disable AC power and battery conditions
        Note: schtasks doesn't have direct flags for this, so we use XML modification
        
        Args:
            job_id: Job ID
            
        Returns:
            bool: Success status
        """
        import time
        task_name = self._get_task_name(job_id)
        
        try:
            # Give Task Scheduler a moment to fully register the task
            time.sleep(0.5)
            
            # Export task to XML
            export_cmd = ["schtasks", "/Query", "/TN", task_name, "/XML"]
            result = subprocess.run(export_cmd, capture_output=True, text=True, shell=False)
            
            if result.returncode != 0:
                print(f"  [DEBUG] Export failed: {result.stderr}")
                return False
            
            # Parse XML
            try:
                root = ET.fromstring(result.stdout)
            except ET.ParseError as e:
                print(f"  [DEBUG] XML parse error: {e}")
                return False
            
            # Define namespace
            ns = {'task': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            
            # Find Settings element
            settings = root.find('task:Settings', ns)
            if settings is None:
                # Try without namespace
                settings = root.find('.//Settings')
                if settings is None:
                    print(f"  [DEBUG] Settings element not found")
                    return False
            
            # Modify power settings
            modified = False
            
            # Handle with namespace
            for elem_name in ['DisallowStartIfOnBatteries', 'StopIfGoingOnBatteries']:
                elem = settings.find(f'task:{elem_name}', ns)
                if elem is None:
                    elem = settings.find(f'.//{elem_name}')
                
                if elem is not None:
                    elem.text = 'false'
                    modified = True
                else:
                    # Create the element
                    if ns:
                        new_elem = ET.SubElement(settings, f'{{http://schemas.microsoft.com/windows/2004/02/mit/task}}{elem_name}')
                    else:
                        new_elem = ET.SubElement(settings, elem_name)
                    new_elem.text = 'false'
                    modified = True
            
            if not modified:
                print(f"  [DEBUG] No modifications made")
                return False
            
            # Save to temp file
            temp_xml = os.path.join(tempfile.gettempdir(), f"task_{job_id}_fix.xml")
            
            # Write XML with proper declaration
            with open(temp_xml, 'w', encoding='utf-16') as f:
                f.write('<?xml version="1.0" encoding="UTF-16"?>\n')
                tree = ET.ElementTree(root)
                tree.write(f, encoding='unicode')
            
            # Delete old task
            delete_cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]
            subprocess.run(delete_cmd, capture_output=True, shell=False)
            time.sleep(0.3)
            
            # Recreate from XML
            create_cmd = ["schtasks", "/Create", "/TN", task_name, "/XML", temp_xml, "/F"]
            result = subprocess.run(create_cmd, capture_output=True, text=True, shell=False)
            
            # Cleanup
            try:
                os.remove(temp_xml)
            except:
                pass
            
            if result.returncode == 0:
                return True
            else:
                print(f"  [DEBUG] Recreation failed: {result.stderr}")
                return False
        
        except Exception as e:
            print(f"  [DEBUG] Exception in _disable_power_conditions: {e}")
            import traceback
            traceback.print_exc()
            return False

    
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
            
            scheduled_datetime = datetime.combine(date_obj.date(), time_obj.time())
            current_datetime = datetime.now()
            
            if scheduled_datetime <= current_datetime:
                print(f"Error: Scheduled time must be in the future!")
                print(f"  Current time: {current_datetime.strftime('%Y-%m-%d %H:%M')}")
                print(f"  Scheduled time: {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
                return False
            
            formatted_date = date_obj.strftime("%d/%m/%Y")
            
        except ValueError as e:
            print(f"Error: Invalid date or time format: {e}")
            return False
        
        # Create batch file
        try:
            batch_file = self._create_batch_file(job_id, module_id, module_name, browser, headless)
        except Exception as e:
            print(f"Error creating batch file: {e}")
            return False
        
        # Create scheduled task with /RU parameter
        schtasks_command = [
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/TR", f'"{batch_file}"',
            "/SC", "ONCE",
            "/SD", formatted_date,
            "/ST", time,
            "/RU", os.environ.get('USERNAME', os.getlogin()),
            "/F"
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"[OK] Created one-time task '{task_name}'")
            print(f"  Scheduled: {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Module: {module_name} (ID: {module_id})")
            print(f"  Browser: {browser}, Headless: {headless}")
            print(f"  Run as: {os.environ.get('USERNAME', 'current user')}")
            
            # Disable power conditions
            if self._disable_power_conditions(job_id):
                print(f"  [OK] Disabled AC power requirements - will run on battery")
            else:
                print(f"  [WARNING] Could not disable AC power requirements")
            
            # Verify task exists
            if self.task_exists(job_id):
                print(f"  [OK] Verified: Task exists in Task Scheduler")
            else:
                print(f"  [WARNING] Task verification failed")
                return False
        else:
            print(f"[FAILED] Failed to create task '{task_name}'")
            print(f"  Error: {error}")
            # Clean up batch file
            if os.path.exists(batch_file):
                os.remove(batch_file)
            return False
        
        return success
    
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
        """Create a recurring scheduled task"""
        task_name = self._get_task_name(job_id)
        
        # Parse time
        try:
            time_obj = datetime.strptime(time, "%H:%M")
        except ValueError as e:
            print(f"Error: Invalid time format: {e}")
            return False
        
        # Map day names
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
        
        # Create batch file
        try:
            batch_file = self._create_batch_file(job_id, module_id, module_name, browser, headless)
        except Exception as e:
            print(f"Error creating batch file: {e}")
            return False
        
        # Create scheduled task with /RU parameter
        if day == "Daily":
            schtasks_command = [
                "schtasks",
                "/Create",
                "/TN", task_name,
                "/TR", f'"{batch_file}"',
                "/SC", "DAILY",
                "/ST", time,
                "/RU", os.environ.get('USERNAME', os.getlogin()),
                "/F"
            ]
        else:
            schtasks_command = [
                "schtasks",
                "/Create",
                "/TN", task_name,
                "/TR", f'"{batch_file}"',
                "/SC", "WEEKLY",
                "/D", schtasks_day,
                "/ST", time,
                "/RU", os.environ.get('USERNAME', os.getlogin()),
                "/F"
            ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"[OK] Created recurring task '{task_name}'")
            print(f"  Schedule: Every {day} at {time}")
            print(f"  Module: {module_name} (ID: {module_id})")
            print(f"  Browser: {browser}, Headless: {headless}")
            print(f"  Run as: {os.environ.get('USERNAME', 'current user')}")
            
            # Disable power conditions
            if self._disable_power_conditions(job_id):
                print(f"  [OK] Disabled AC power requirements - will run on battery")
            else:
                print(f"  [WARNING] Could not disable AC power requirements")
            
            # Verify
            if self.task_exists(job_id):
                print(f"  [OK] Verified: Task exists in Task Scheduler")
            else:
                print(f"  [WARNING] Task verification failed")
                return False
        else:
            print(f"[FAILED] Failed to create task '{task_name}'")
            print(f"  Error: {error}")
            # Clean up
            if os.path.exists(batch_file):
                os.remove(batch_file)
            return False
        
        return success
    
    def delete_task(self, job_id: int) -> bool:
        """Delete a scheduled task and its batch file"""
        task_name = self._get_task_name(job_id)
        
        # Delete from Task Scheduler
        schtasks_command = [
            "schtasks",
            "/Delete",
            "/TN", task_name,
            "/F"
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success or "cannot find" in error.lower() or "does not exist" in error.lower():
            print(f"[OK] Deleted task '{task_name}'")
            
            # Delete batch file
            batch_file = self._get_batch_file_path(job_id)
            if os.path.exists(batch_file):
                try:
                    os.remove(batch_file)
                    print(f"  [OK] Deleted batch file")
                except Exception as e:
                    print(f"  [WARNING] Could not delete batch file: {e}")
            
            # Delete log file
            log_file = os.path.join(self.batch_dir, f"job_{job_id}_log.txt")
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                    print(f"  [OK] Deleted log file")
                except:
                    pass
            
            return True
        else:
            print(f"[FAILED] Failed to delete task '{task_name}'")
            print(f"  Error: {error}")
            return False
    
    def task_exists(self, job_id: int) -> bool:
        """Check if a scheduled task exists"""
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Query",
            "/TN", task_name
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        return success
    
    def list_all_tasks(self) -> list:
        """List all automation tasks"""
        schtasks_command = [
            "schtasks",
            "/Query",
            "/FO", "LIST"
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if not success:
            return []
        
        tasks = []
        for line in output.split('\n'):
            if 'TaskName:' in line and self.task_prefix in line:
                task_name = line.split(':', 1)[1].strip()
                try:
                    job_id = int(task_name.split('_')[-1])
                    tasks.append({'task_name': task_name, 'job_id': job_id})
                except:
                    pass
        
        return tasks
    
    def run_task_now(self, job_id: int) -> bool:
        """Run a scheduled task immediately"""
        task_name = self._get_task_name(job_id)
        
        schtasks_command = [
            "schtasks",
            "/Run",
            "/TN", task_name
        ]
        
        success, output, error = self._run_schtasks(schtasks_command)
        
        if success:
            print(f"[OK] Started task '{task_name}' immediately")
        else:
            print(f"[FAILED] Failed to start task '{task_name}'")
            print(f"  Error: {error}")
        
        return success


if __name__ == "__main__":
    print("=" * 80)
    print("SCHEDULER MANAGER TEST")
    print("=" * 80)
    
    try:
        manager = SchedulerManager()
        
        print("\nExisting automation tasks:")
        tasks = manager.list_all_tasks()
        if tasks:
            for task in tasks:
                print(f"  - {task['task_name']} (Job ID: {task['job_id']})")
        else:
            print("  No tasks found")
        
        print("\n[OK] Scheduler Manager is ready!")
        print("=" * 80)
    
    except Exception as e:
        print(f"\n[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
