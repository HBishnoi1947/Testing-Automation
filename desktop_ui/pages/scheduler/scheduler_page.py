"""
Scheduler Page - UI for scheduling testing modules
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from .scheduler_page_functions import SchedulerPageFunctions


class SchedulerPage:
    """Scheduler page for testing modules"""
    
    def __init__(self, parent_window, colors, project_id=None):
        """
        Initialize the scheduler page
        
        Args:
            parent_window: Parent window/frame
            colors: Color scheme dictionary
            project_id: Optional project ID to filter modules
        """
        self.parent_window = parent_window
        self.colors = colors
        self.project_id = project_id
        
        # Initialize functions handler
        self.functions = SchedulerPageFunctions(self, colors, project_id)
        
        # Create UI
        self.create_widgets()
        
        # Load initial data
        self.functions.load_modules()
        self.functions.load_scheduled_jobs()
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_container = tk.Frame(self.parent_window, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Scheduler form
        self.create_scheduler_form(main_container)
        
        # Scheduled jobs list
        self.create_jobs_list(main_container)
    
    def create_header(self, parent):
        """Create the header section"""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="⏰ Testing Module Scheduler",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        )
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Schedule automated test runs",
            font=('Segoe UI', 12),
            fg=self.colors['text_light'],
            bg=self.colors['background']
        )
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(8, 0))
    
    def create_scheduler_form(self, parent):
        """Create the scheduler form"""
        form_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        form_card.pack(fill=tk.X, pady=(0, 20))
        
        # Form header
        form_header = tk.Frame(form_card, bg=self.colors['primary'], height=50)
        form_header.pack(fill=tk.X)
        form_header.pack_propagate(False)
        
        form_title = tk.Label(
            form_header,
            text="📝 Create Scheduled Job",
            font=('Segoe UI', 14, 'bold'),
            fg='white',
            bg=self.colors['primary']
        )
        form_title.pack(pady=12)
        
        # Form content
        form_content = tk.Frame(form_card, bg=self.colors['surface'])
        form_content.pack(fill=tk.X, padx=20, pady=20)
        
        # Create three columns
        col1 = tk.Frame(form_content, bg=self.colors['surface'])
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        col2 = tk.Frame(form_content, bg=self.colors['surface'])
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10))
        
        # NEW: Toggle button frame (between col2 and col3)
        toggle_frame = tk.Frame(form_content, bg=self.colors['surface'], width=60)
        toggle_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 10))
        toggle_frame.pack_propagate(False)
        
        col3 = tk.Frame(form_content, bg=self.colors['surface'])
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # COLUMN 1: Module Selection
        self.create_module_selection(col1)
        
        # COLUMN 2: Date and Time (One-time run)
        self.create_datetime_selection(col2)
        
        # NEW: TOGGLE BUTTON (between columns)
        self.create_schedule_toggle(toggle_frame)
        
        # COLUMN 3: Recurring Schedule
        self.create_recurring_selection(col3)
        
        # ADDED: Additional options row
        options_row = tk.Frame(form_card, bg=self.colors['surface'])
        options_row.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Browser selection
        browser_frame = tk.Frame(options_row, bg=self.colors['surface'])
        browser_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            browser_frame,
            text="🌐 Browser:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.browser_var = tk.StringVar(value="Chrome")
        self.browser_combo = ttk.Combobox(
            browser_frame,
            textvariable=self.browser_var,
            values=["Chrome", "Edge", "Firefox"],
            state="readonly",
            width=15,
            font=('Segoe UI', 10)
        )
        self.browser_combo.pack(side=tk.LEFT)
        
        # Headless mode toggle
        headless_frame = tk.Frame(options_row, bg=self.colors['surface'])
        headless_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            headless_frame,
            text="👤 Headless Mode:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.headless_var = tk.BooleanVar(value=False)
        self.headless_check = tk.Checkbutton(
            headless_frame,
            text="Enabled",
            variable=self.headless_var,
            font=('Segoe UI', 10),
            bg=self.colors['surface'],
            fg=self.colors['text'],
            selectcolor=self.colors['surface'],
            activebackground=self.colors['surface']
        )
        self.headless_check.pack(side=tk.LEFT)
        
        # Create button
        self.create_button = tk.Button(
            options_row,
            text="✅ Create Schedule",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['success'],
            fg='white',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.functions.create_schedule
        )
        self.create_button.pack(side=tk.RIGHT)


    def create_module_selection(self, parent):
        """Create module selection dropdown"""
        tk.Label(
            parent,
            text="Select Module",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.module_var = tk.StringVar()
        self.module_combo = ttk.Combobox(
            parent,
            textvariable=self.module_var,
            state="readonly",
            width=25,
            font=('Segoe UI', 10)
        )
        self.module_combo.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            parent,
            text="Choose a testing module to schedule",
            font=('Segoe UI', 9),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W)

    def create_schedule_toggle(self, parent):
        """Create toggle button between one-time and recurring schedule"""
        # Add some top padding to align with other columns
        tk.Label(parent, text="", bg=self.colors['surface'], height=1).pack()
        
        # Container for toggle
        toggle_container = tk.Frame(parent, bg=self.colors['surface'])
        toggle_container.pack(expand=True)
        
        # Schedule type variable (True = One-Time, False = Recurring)
        self.schedule_type_var = tk.BooleanVar(value=True)
        
        # One-Time indicator
        self.onetime_label = tk.Label(
            toggle_container,
            text="One-Time",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['success'],
            bg=self.colors['surface']
        )
        self.onetime_label.pack(pady=(0, 5))
        
        # Toggle button
        toggle_btn_frame = tk.Frame(
            toggle_container,
            bg=self.colors['border'],
            relief=tk.RAISED,
            bd=1
        )
        toggle_btn_frame.pack(pady=5)
        
        self.toggle_button = tk.Button(
            toggle_btn_frame,
            text="⬇",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['success'],
            fg='white',
            width=3,
            height=2,
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            command=self.toggle_schedule_type
        )
        self.toggle_button.pack(padx=2, pady=2)
        
        # Recurring indicator
        self.recurring_label = tk.Label(
            toggle_container,
            text="Recurring",
            font=('Segoe UI', 9),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        )
        self.recurring_label.pack(pady=(5, 0))
        
        # OR divider
        tk.Label(
            toggle_container,
            text="OR",
            font=('Segoe UI', 8, 'bold'),
            fg=self.colors['border'],
            bg=self.colors['surface']
        ).pack(pady=(15, 0))

    def toggle_schedule_type(self):
        """Toggle between one-time and recurring schedule"""
        current = self.schedule_type_var.get()
        new_value = not current
        self.schedule_type_var.set(new_value)
        
        if new_value:  # One-Time selected
            # Update toggle button
            self.toggle_button.config(
                text="⬇",
                bg=self.colors['success']
            )
            
            # Update labels
            self.onetime_label.config(
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['success']
            )
            self.recurring_label.config(
                font=('Segoe UI', 9),
                fg=self.colors['text_light']
            )
            
            # Enable one-time fields
            self.date_entry.config(state='normal')
            self.time_entry.config(state='normal')
            
            # Disable recurring fields
            self.day_combo.config(state='disabled')
            self.recurring_time_entry.config(state='disabled')
            
        else:  # Recurring selected
            # Update toggle button
            self.toggle_button.config(
                text="⬆",
                bg=self.colors['accent']
            )
            
            # Update labels
            self.onetime_label.config(
                font=('Segoe UI', 9),
                fg=self.colors['text_light']
            )
            self.recurring_label.config(
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['accent']
            )
            
            # Disable one-time fields
            self.date_entry.config(state='disabled')
            self.time_entry.config(state='disabled')
            
            # Enable recurring fields
            self.day_combo.config(state='readonly')
            self.recurring_time_entry.config(state='normal')


    
    def create_datetime_selection(self, parent):
        """Create date and time selection"""
        tk.Label(
            parent,
            text="One-Time Schedule",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Date selection
        date_frame = tk.Frame(parent, bg=self.colors['surface'])
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            date_frame,
            text="📅 Date:",
            font=('Segoe UI', 10),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.date_entry = tk.Entry(
            date_frame,
            font=('Segoe UI', 10),
            width=12,
            state='normal'  # CHANGED: explicitly set initial state
        )
        self.date_entry.pack(side=tk.LEFT)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Time selection
        time_frame = tk.Frame(parent, bg=self.colors['surface'])
        time_frame.pack(fill=tk.X)
        
        tk.Label(
            time_frame,
            text="⏰ Time:",
            font=('Segoe UI', 10),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.time_entry = tk.Entry(
            time_frame,
            font=('Segoe UI', 10),
            width=12,
            state='normal'  # CHANGED: explicitly set initial state
        )
        self.time_entry.pack(side=tk.LEFT)
        self.time_entry.insert(0, "09:00")
        
        tk.Label(
            parent,
            text="Format: YYYY-MM-DD, HH:MM (24h)",
            font=('Segoe UI', 8),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W, pady=(5, 0))

    
    def create_recurring_selection(self, parent):
        """Create recurring schedule selection"""
        tk.Label(
            parent,
            text="Recurring Schedule",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Day selection
        day_frame = tk.Frame(parent, bg=self.colors['surface'])
        day_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            day_frame,
            text="📆 Day:",
            font=('Segoe UI', 10),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.day_var = tk.StringVar(value="Monday")  # CHANGED: default to Monday instead of None
        self.day_combo = ttk.Combobox(
            day_frame,
            textvariable=self.day_var,
            values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Daily"],  # CHANGED: removed "None"
            state="disabled",  # CHANGED: initially disabled
            width=12,
            font=('Segoe UI', 10)
        )
        self.day_combo.pack(side=tk.LEFT)
        
        # Time selection for recurring
        recurring_time_frame = tk.Frame(parent, bg=self.colors['surface'])
        recurring_time_frame.pack(fill=tk.X)
        
        tk.Label(
            recurring_time_frame,
            text="⏰ Time:",
            font=('Segoe UI', 10),
            fg=self.colors['text'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.recurring_time_entry = tk.Entry(
            recurring_time_frame,
            font=('Segoe UI', 10),
            width=12,
            state='disabled'  # CHANGED: initially disabled
        )
        self.recurring_time_entry.pack(side=tk.LEFT)
        self.recurring_time_entry.insert(0, "09:00")
        
        tk.Label(
            parent,
            text="Select day and time for recurring runs",
            font=('Segoe UI', 8),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        ).pack(anchor=tk.W, pady=(5, 0))

    
    def create_jobs_list(self, parent):
        """Create scheduled jobs list"""
        jobs_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        jobs_card.pack(fill=tk.BOTH, expand=True)
        
        # Jobs header
        jobs_header = tk.Frame(jobs_card, bg=self.colors['primary'], height=50)
        jobs_header.pack(fill=tk.X)
        jobs_header.pack_propagate(False)
        
        jobs_title = tk.Label(
            jobs_header,
            text="📋 Scheduled Jobs",
            font=('Segoe UI', 14, 'bold'),
            fg='white',
            bg=self.colors['primary']
        )
        jobs_title.pack(pady=12)
        
        # Jobs content
        jobs_content = tk.Frame(jobs_card, bg=self.colors['surface'])
        jobs_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create treeview
        tree_frame = tk.Frame(jobs_content, bg=self.colors['surface'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Module', 'Date', 'Day', 'Time', 'Browser', 'Headless')
        self.jobs_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        # Configure columns
        self.jobs_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.jobs_tree.heading('Module', text='Module Name', anchor=tk.W)
        self.jobs_tree.heading('Date', text='Scheduled Date', anchor=tk.CENTER)
        self.jobs_tree.heading('Day', text='Recurring Day', anchor=tk.CENTER)
        self.jobs_tree.heading('Time', text='Time', anchor=tk.CENTER)
        self.jobs_tree.heading('Browser', text='Browser', anchor=tk.CENTER)
        self.jobs_tree.heading('Headless', text='Headless', anchor=tk.CENTER)
        
        self.jobs_tree.column('ID', width=50, minwidth=50, anchor=tk.CENTER)
        self.jobs_tree.column('Module', width=200, minwidth=150, anchor=tk.W)
        self.jobs_tree.column('Date', width=120, minwidth=100, anchor=tk.CENTER)
        self.jobs_tree.column('Day', width=120, minwidth=100, anchor=tk.CENTER)
        self.jobs_tree.column('Time', width=80, minwidth=80, anchor=tk.CENTER)
        self.jobs_tree.column('Browser', width=100, minwidth=80, anchor=tk.CENTER)
        self.jobs_tree.column('Headless', width=80, minwidth=80, anchor=tk.CENTER)
        
        self.jobs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.jobs_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.jobs_tree.configure(yscrollcommand=scrollbar.set)
        
        # Action buttons
        action_frame = tk.Frame(jobs_content, bg=self.colors['surface'])
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.delete_job_button = tk.Button(
            action_frame,
            text="🗑️ Delete Selected Job",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=self.functions.delete_selected_job
        )
        self.delete_job_button.pack(side=tk.LEFT)
        
        self.refresh_button = tk.Button(
            action_frame,
            text="🔄 Refresh",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=self.functions.load_scheduled_jobs
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Jobs count
        self.jobs_count_label = tk.Label(
            action_frame,
            text="0 scheduled jobs",
            font=('Segoe UI', 10),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        )
        self.jobs_count_label.pack(side=tk.RIGHT)
