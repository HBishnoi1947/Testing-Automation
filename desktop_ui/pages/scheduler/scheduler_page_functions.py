"""
Scheduler Page Functions - Logic for scheduler operations
"""

from tkinter import messagebox
from datetime import datetime
from typing import Optional
import tkinter as tk


class SchedulerPageFunctions:
    """Functions for scheduler page operations"""
    
    def __init__(self, page, colors, project_id=None):
        """
        Initialize scheduler functions
        
        Args:
            page: Reference to SchedulerPage instance
            colors: Color scheme dictionary
            project_id: Optional project ID to filter modules
        """
        self.page = page
        self.colors = colors
        self.project_id = project_id
        
        # Data
        self.modules = []
        self.scheduled_jobs = []
    
    def load_modules(self):
        """Load all testing modules"""
        try:
            from model.database import get_testing_modules_by_project, get_all_testing_modules
            
            # Load modules based on project filter
            if self.project_id:
                self.modules = get_testing_modules_by_project(self.project_id)
            else:
                self.modules = get_all_testing_modules()
            
            # Update module dropdown
            module_names = [f"{m['testing_module']} (ID: {m['id']})" for m in self.modules]
            self.page.module_combo['values'] = module_names
            
            if module_names:
                self.page.module_combo.current(0)
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load modules: {e}")
            return False
    
    def load_scheduled_jobs(self):
        """Load all scheduled jobs from database"""
        try:
            # TODO: This will be implemented in Task 2
            # For now, just clear the tree and show message
            from model.database import get_all_scheduled_jobs
            
            # Clear existing items
            for item in self.page.jobs_tree.get_children():
                self.page.jobs_tree.delete(item)
            
            # Load jobs from database
            self.scheduled_jobs = get_all_scheduled_jobs(self.project_id)
            
            # Populate tree
            for job in self.scheduled_jobs:
                self.page.jobs_tree.insert('', 'end', values=(
                    job['id'],
                    job['module_name'],
                    job['scheduled_date'] or '-',
                    job['recurring_day'] or '-',
                    job['scheduled_time'],
                    job['browser'],
                    'Yes' if job['headless'] else 'No'
                ))
            
            # Update count
            count = len(self.scheduled_jobs)
            self.page.jobs_count_label.config(
                text=f"{count} scheduled job{'s' if count != 1 else ''}"
            )
            
            return True
        except Exception as e:
            # If function doesn't exist yet, just show 0 jobs
            self.page.jobs_count_label.config(text="0 scheduled jobs")
            return False
    
    def create_schedule(self):
        """Create a new scheduled job"""
        # Validate module selection
        if not self.page.module_var.get():
            messagebox.showwarning("Warning", "Please select a module!")
            return
        
        # Extract module ID from selection
        module_text = self.page.module_var.get()
        try:
            module_id = int(module_text.split("ID: ")[1].rstrip(")"))
            module_name = module_text.split(" (ID:")[0]
        except:
            messagebox.showerror("Error", "Invalid module selection!")
            return
        
        # Get schedule type from toggle (True = One-Time, False = Recurring)
        is_onetime = self.page.schedule_type_var.get()
        
        if is_onetime:
            # One-time schedule
            scheduled_date = self.page.date_entry.get().strip()
            scheduled_time = self.page.time_entry.get().strip()
            recurring_day = None
            
            # Validate date format
            if not self.validate_date(scheduled_date):
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
                return
            
            # Validate time format
            if not self.validate_time(scheduled_time):
                messagebox.showerror("Error", "Invalid time format! Use HH:MM (24-hour)")
                return
        else:
            # Recurring schedule
            scheduled_date = None
            scheduled_time = self.page.recurring_time_entry.get().strip()
            recurring_day = self.page.day_var.get()
            
            # Validate time format
            if not self.validate_time(scheduled_time):
                messagebox.showerror("Error", "Invalid time format! Use HH:MM (24-hour)")
                return
        
        # Get browser and headless settings
        browser = self.page.browser_var.get()
        headless = self.page.headless_var.get()
        
        # Create schedule in database
        

        
        # Create schedule in database
        try:
            from model.database import create_scheduled_job
            
            job_id = create_scheduled_job(
                module_id=module_id,
                module_name=module_name,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                recurring_day=recurring_day,
                browser=browser,
                headless=headless,
                project_id=self.project_id
            )
            
            # Register with system task scheduler
            try:
                from scheduler_manager import SchedulerManager
                scheduler = SchedulerManager()
                
                if recurring_day:
                    success = scheduler.create_recurring_task(
                        job_id=job_id,
                        module_id=module_id,
                        module_name=module_name,
                        day=recurring_day,
                        time=scheduled_time,
                        browser=browser,
                        headless=headless
                    )
                else:
                    success = scheduler.create_one_time_task(
                        job_id=job_id,
                        module_id=module_id,
                        module_name=module_name,
                        date=scheduled_date,
                        time=scheduled_time,
                        browser=browser,
                        headless=headless
                    )
                
                if success:
                    schedule_type = f"{recurring_day} at {scheduled_time}" if recurring_day else f"{scheduled_date} at {scheduled_time}"
                    messagebox.showinfo(
                        "Success", 
                        f"Schedule created successfully!\n\n"
                        f"Job ID: {job_id}\n"
                        f"Module: {module_name}\n"
                        f"Schedule: {schedule_type}\n"
                        f"Browser: {browser}\n"
                        f"Headless: {'Yes' if headless else 'No'}\n\n"
                        f"✅ Windows Task Scheduler entry created!"
                    )
                    self.load_scheduled_jobs()
                    self.clear_form()
                else:
                    # Rollback database entry if task creation failed
                    from model.database import delete_scheduled_job_permanent
                    delete_scheduled_job_permanent(job_id)
                    messagebox.showerror(
                        "Error", 
                        "Failed to create Windows scheduled task!\n\n"
                        "The job has been removed from the database.\n\n"
                        "Possible reasons:\n"
                        "- Insufficient Administrator privileges\n"
                        "- Invalid date/time format\n"
                        "- System Task Scheduler service not running"
                    )
                    
            except Exception as scheduler_error:
                # Rollback database entry if scheduler failed
                try:
                    from model.database import delete_scheduled_job_permanent
                    delete_scheduled_job_permanent(job_id)
                except:
                    pass
                messagebox.showerror("Error", f"Scheduler error: {scheduler_error}\n\nThe job has been removed from the database.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create schedule: {e}")



    def delete_selected_job(self):
        """Delete the selected scheduled job"""
        selection = self.page.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a job to delete!")
            return
        
        # Get job ID
        item = self.page.jobs_tree.item(selection[0])
        job_id = item['values'][0]
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this scheduled job?"
        )
        
        if not result:
            return
        
        try:
            # Remove from system task scheduler first
            try:
                from scheduler_manager import SchedulerManager
                scheduler = SchedulerManager()
                scheduler.delete_task(job_id)
                print(f"✓ Deleted Windows Task Scheduler entry for Job ID {job_id}")
            except Exception as e:
                print(f"Warning: Failed to delete system task: {e}")
            
            # Delete from database
            from model.database import delete_scheduled_job
            delete_scheduled_job(job_id)
            
            messagebox.showinfo("Success", f"Scheduled job deleted successfully!\n\nJob ID: {job_id}\nModule: {module_name}")
            self.load_scheduled_jobs()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete job: {e}")

        
    
    def validate_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except:
            return False
    
    def validate_time(self, time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except:
            return False
    
    def clear_form(self):
        """Clear the scheduler form"""
        # Reset one-time fields
        self.page.date_entry.delete(0, tk.END)
        self.page.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        self.page.time_entry.delete(0, tk.END)
        self.page.time_entry.insert(0, "09:00")
        
        # Reset recurring fields
        self.page.recurring_time_entry.delete(0, tk.END)
        self.page.recurring_time_entry.insert(0, "09:00")
        
        self.page.day_var.set("Monday")  # FIXED: Use "Monday" as default
        
        # Reset browser and headless
        self.page.browser_var.set("Chrome")
        self.page.headless_var.set(False)
        
        # Reset toggle to one-time mode
        self.page.schedule_type_var.set(True)
        self.page.toggle_schedule_type()  # Apply the toggle state

