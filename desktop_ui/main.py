"""
Modern Desktop GUI Application for Testing Automation with Project Support.
Provides a beautiful, modern tkinter-based interface to manage projects, features and events.
"""

import os
from dotenv import load_dotenv
import sys
import threading
import webbrowser
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
from typing import List, Optional
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.database import get_features_by_project, get_events_by_feature_id
from model.event import Event
from model.operation_type import OperationType, OperationTypeMapper
from model.project import Project
from run import AutomationRunner
from execute import execute_events

# Import page components
from pages import FeaturesPage, EventsPage, TestingModulePage
from desktop_ui.pages.launch import LaunchAnimationWindow
from desktop_ui.pages.projects import ProjectsPage
from desktop_ui.pages.features_events.events_page_functions import run_events_for_feature as events_run_events_for_feature, update_feature_workflow as events_update_feature_workflow
from desktop_ui.pages.features_events.features_page_functions import open_create_feature_dialog
from desktop_ui.pages.testing_modules.testing_module_page_functions import run_testing_module as tm_run_testing_module


class DesktopUI:
    """Modern Desktop GUI application for the Testing Automation  with Project Support."""
    
    def __init__(self):
        """Initialize the desktop UI with modern styling."""
        # Show launch animation first
        LaunchAnimationWindow(self.initialize_main_window)
    
    def initialize_main_window(self):
        """Initialize the main application window after splash screen."""
        self.root = tk.Tk()
        self.root.title("🚀 Testing Automation - Modern UI")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2c3e50',      # Dark blue-gray
            'secondary': '#3498db',    # Bright blue
            'accent': '#e74c3c',       # Red accent
            'success': '#27ae60',      # Green
            'warning': '#f39c12',      # Orange
            'background': '#ecf0f1',   # Light gray
            'surface': '#ffffff',      # White
            'text': '#2c3e50',         # Dark text
            'text_light': '#7f8c8d',   # Light text
            'border': '#bdc3c7',       # Light border
            'hover': '#34495e'         # Darker on hover
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['background'])
        
        # Data
        self.projects = []  # List of Project objects
        self.current_project = None  # Current Project object
        self.features = []  # List of Feature objects
        self.events = []    # List of Event objects
        self.current_feature = None  # Current Feature object
        
        # Operation type mapper for efficient lookups
        self.operation_mapper = OperationTypeMapper()
        self.operation_mapper.load_operation_types()
        
        # UI state
        self.main_container = None
        self.current_view = 'features_events'  # 'features_events' or 'testing_modules'
        self.testing_module_page = None
        
        # Configure modern styling
        self.setup_styles()
        
        # Show project selection screen first
        self.show_project_selection()
        
        # Center window
        self.center_window()
        
        # Start the main loop
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1400
        window_height = 900
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def show_project_selection(self):
        """Show the project selection screen."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create projects page
        self.projects_page = ProjectsPage(
            self.root,
            self.colors,
            on_project_select=self.select_project
        )
    
    def select_project(self, project: Project):
        """Select and open a project."""
        self.current_project = project
        self.show_main_interface()
    
    def show_main_interface(self):
        """Show the main interface with features and events."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Reset view to features/events
        self.current_view = 'features_events'
        
        # Create main widgets
        self.create_widgets()
        self.load_data()
    
    def show_testing_modules_view(self):
        """Switch to testing modules view."""
        if self.current_view == 'testing_modules':
            return  # Already on testing modules view
        
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Set current view
        self.current_view = 'testing_modules'
        
        # Create main widgets with testing modules
        self.create_widgets()
        self.load_testing_modules()
    
    def show_features_events_view(self):
        """Switch back to features/events view."""
        if self.current_view == 'features_events':
            return  # Already on features/events view
        
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Set current view
        self.current_view = 'features_events'
        
        # Create main widgets
        self.create_widgets()
        self.load_data()
    
    def setup_styles(self):
        """Configure modern ttk styles."""
        style = ttk.Style()
        
        # Configure modern button styles
        style.configure('Modern.TButton',
                       background=self.colors['secondary'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 10),
                       relief='flat',
                       borderwidth=0)
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['hover']),
                           ('pressed', self.colors['primary'])])
        
        # Configure success button style
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 10),
                       relief='flat',
                       borderwidth=0)
        
        # Configure warning button style
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 10),
                       relief='flat',
                       borderwidth=0)
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       background=self.colors['surface'],
                       relief='solid',
                       borderwidth=1)
        
        # Configure label styles
        style.configure('Title.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['primary'],
                       font=('Segoe UI', 18, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Info.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['text_light'],
                       font=('Segoe UI', 9))
        
        # Configure listbox styles
        style.configure('Modern.TListbox',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       selectbackground=self.colors['secondary'],
                       selectforeground='white',
                       relief='solid',
                       borderwidth=1)
        
        # Configure treeview styles
        style.configure('Modern.Treeview',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9),
                       rowheight=25,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Modern.Treeview.Heading',
                       background=self.colors['primary'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        
        # Configure entry styles
        style.configure('Modern.TEntry',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       relief='solid',
                       borderwidth=1,
                       padding=8)
        
        # Configure text styles
        style.configure('Modern.TText',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       relief='solid',
                       borderwidth=1,
                       padding=8)
        
    def create_widgets(self):
        """Create and layout the modern UI widgets."""
        # Main container with padding
        self.main_container = tk.Frame(self.root, bg=self.colors['background'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(self.main_container)
        
        # Create view based on current_view
        if self.current_view == 'testing_modules':
            self.create_testing_modules_widgets()
        else:
            self.create_features_events_widgets()
    
    def create_features_events_widgets(self):
        """Create features and events widgets."""
        # Main content area
        content_frame = tk.Frame(self.main_container, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Left panel - Features
        self.create_features_panel(content_frame)
        
        # Right panel - Events
        self.create_events_panel(content_frame)
        
        # Bottom panel - Controls
        self.create_controls_panel(self.main_container)
    
    def create_testing_modules_widgets(self):
        """Create testing modules widgets."""
        # Content frame for testing modules
        testing_module_frame = tk.Frame(self.main_container, bg=self.colors['background'])
        testing_module_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Create testing module page with current project ID
        project_id = self.current_project.id if self.current_project else None
        self.testing_module_page = TestingModulePage(
            testing_module_frame,
            self.colors,
            self.on_run_module,
            project_id=project_id
        )
    
    def on_run_module(self, module, flow):
        """Handle run module request from testing module page."""
        tm_run_testing_module(self.root, self.update_status, None, module, flow)
    
    def create_header(self, parent):
        """Create the modern header section."""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title with project name
        title_frame = tk.Frame(header_frame, bg=self.colors['background'])
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(title_frame, 
                              text=f"🚀 {self.current_project.name}", 
                              font=('Segoe UI', 24, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        title_label.pack(side=tk.LEFT)
        
        # Navigation buttons frame
        nav_frame = tk.Frame(title_frame, bg=self.colors['background'])
        nav_frame.pack(side=tk.RIGHT)
        
        # View switcher buttons
        if self.current_view == 'features_events':
            # Show Testing Modules button when on features/events view
            self.view_switch_button = tk.Button(nav_frame,
                                              text="🧪 Testing Modules",
                                              font=('Segoe UI', 10, 'bold'),
                                              bg=self.colors['secondary'],
                                              fg='white',
                                              relief=tk.FLAT,
                                              bd=0,
                                              padx=15,
                                              pady=8,
                                              cursor='hand2',
                                              command=self.show_testing_modules_view)
            self.view_switch_button.pack(side=tk.RIGHT, padx=(0, 10))
        else:
            # Show Features & Events button when on testing modules view
            self.view_switch_button = tk.Button(nav_frame,
                                              text="📋 Features & Events",
                                              font=('Segoe UI', 10, 'bold'),
                                              bg=self.colors['secondary'],
                                              fg='white',
                                              relief=tk.FLAT,
                                              bd=0,
                                              padx=15,
                                              pady=8,
                                              cursor='hand2',
                                              command=self.show_features_events_view)
            self.view_switch_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Back to projects button
        back_button = tk.Button(nav_frame,
                               text="⬅️ Back to Projects",
                               font=('Segoe UI', 10, 'bold'),
                               bg=self.colors['text_light'],
                               fg='white',
                               relief=tk.FLAT,
                               bd=0,
                               padx=15,
                               pady=8,
                               cursor='hand2',
                               command=self.back_to_projects)
        back_button.pack(side=tk.RIGHT)
        
        # Subtitle
        if self.current_project.description:
            subtitle_label = tk.Label(title_frame,
                                     text=self.current_project.description,
                                     font=('Segoe UI', 11),
                                     fg=self.colors['text_light'],
                                     bg=self.colors['background'])
            subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(8, 0))
        
        # Status indicator
        self.status_frame = tk.Frame(header_frame, bg=self.colors['background'])
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_indicator = tk.Label(self.status_frame,
                                       text="●",
                                       font=('Segoe UI', 12),
                                       fg=self.colors['success'],
                                       bg=self.colors['background'])
        self.status_indicator.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(self.status_frame,
                                   text="Ready",
                                   font=('Segoe UI', 10),
                                   fg=self.colors['text_light'],
                                   bg=self.colors['background'])
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def back_to_projects(self):
        """Go back to project selection screen."""
        self.current_project = None
        self.current_feature = None
        self.features = []
        self.events = []
        self.current_view = 'features_events'
        self.show_project_selection()
    
    def load_testing_modules(self):
        """Load testing modules data."""
        if self.testing_module_page:
            self.testing_module_page.load_data()
    
    def create_features_panel(self, parent):
        """Create the modern features panel."""
        features_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        features_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        features_header = tk.Frame(features_card, bg=self.colors['primary'], height=50)
        features_header.pack(fill=tk.X)
        features_header.pack_propagate(False)
        
        features_title = tk.Label(features_header,
                                 text="📋 Features",
                                 font=('Segoe UI', 14, 'bold'),
                                 fg='white',
                                 bg=self.colors['primary'])
        features_title.pack(pady=15)
        
        features_content = tk.Frame(features_card, bg=self.colors['surface'])
        features_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        listbox_frame = tk.Frame(features_content, bg=self.colors['surface'])
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.features_listbox = tk.Listbox(listbox_frame,
                                         font=('Segoe UI', 11),
                                         bg=self.colors['surface'],
                                         fg=self.colors['text'],
                                         selectbackground=self.colors['secondary'],
                                         selectforeground='white',
                                         relief=tk.FLAT,
                                         bd=0,
                                         highlightthickness=1,
                                         highlightcolor=self.colors['secondary'],
                                         highlightbackground=self.colors['border'])
        self.features_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.features_listbox.bind('<<ListboxSelect>>', self.on_feature_select)
        
        features_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.features_listbox.yview)
        features_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.features_listbox.configure(yscrollcommand=features_scrollbar.set)
        
        self.features_count_label = tk.Label(features_content,
                                           text="No features loaded",
                                           font=('Segoe UI', 9),
                                           fg=self.colors['text_light'],
                                           bg=self.colors['surface'])
        self.features_count_label.pack(pady=(10, 0))
    
    def create_events_panel(self, parent):
        """Create the modern events panel."""
        events_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        events_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        events_header = tk.Frame(events_card, bg=self.colors['primary'], height=50)
        events_header.pack(fill=tk.X)
        events_header.pack_propagate(False)
        
        events_title = tk.Label(events_header,
                               text="⚡ Events",
                               font=('Segoe UI', 14, 'bold'),
                               fg='white',
                               bg=self.colors['primary'])
        events_title.pack(pady=15)
        
        events_content = tk.Frame(events_card, bg=self.colors['surface'])
        events_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tree_frame = tk.Frame(events_content, bg=self.colors['surface'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Step', 'Operation', 'URL', 'Component', 'Input')
        self.events_tree = ttk.Treeview(tree_frame, 
                                       columns=columns, 
                                       show='headings', 
                                       style='Modern.Treeview',
                                       height=15)
        
        self.events_tree.heading('Step', text='Step', anchor=tk.CENTER)
        self.events_tree.heading('Operation', text='Operation', anchor=tk.W)
        self.events_tree.heading('URL', text='URL', anchor=tk.W)
        self.events_tree.heading('Component', text='Component', anchor=tk.W)
        self.events_tree.heading('Input', text='Input', anchor=tk.W)
        
        self.events_tree.column('Step', width=60, minwidth=60, anchor=tk.CENTER)
        self.events_tree.column('Operation', width=120, minwidth=120, anchor=tk.W)
        self.events_tree.column('URL', width=250, minwidth=200, anchor=tk.W)
        self.events_tree.column('Component', width=200, minwidth=150, anchor=tk.W)
        self.events_tree.column('Input', width=150, minwidth=100, anchor=tk.W)
        
        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        events_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_tree.configure(yscrollcommand=events_scrollbar.set)
        
        events_bottom_frame = tk.Frame(events_content, bg=self.colors['surface'])
        events_bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.events_count_label = tk.Label(events_bottom_frame,
                                         text="Select a feature to view events",
                                         font=('Segoe UI', 9),
                                         fg=self.colors['text_light'],
                                         bg=self.colors['surface'])
        self.events_count_label.pack(side=tk.LEFT)
        
        # Buttons frame for run and update
        buttons_frame = tk.Frame(events_bottom_frame, bg=self.colors['surface'])
        buttons_frame.pack(side=tk.RIGHT)
        
        # Update Feature button
        self.update_feature_button = tk.Button(buttons_frame,
                                             text="🔄 Update Feature",
                                             font=('Segoe UI', 9, 'bold'),
                                             bg=self.colors['secondary'],
                                             fg='white',
                                             relief=tk.FLAT,
                                             bd=0,
                                             padx=15,
                                             pady=5,
                                             cursor='hand2',
                                             command=self.update_feature,
                                             state=tk.DISABLED)
        self.update_feature_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Run Events button
        self.run_events_button = tk.Button(buttons_frame,
                                         text="▶️ Run Events",
                                         font=('Segoe UI', 9, 'bold'),
                                         bg=self.colors['warning'],
                                         fg='white',
                                         relief=tk.FLAT,
                                         bd=0,
                                         padx=15,
                                         pady=5,
                                         cursor='hand2',
                                         command=self.run_events,
                                         state=tk.DISABLED)
        self.run_events_button.pack(side=tk.RIGHT)
    
    def load_data(self):
        """Load features for the current project."""
        if not self.current_project:
            return
        
        try:
            from model.feature import Feature
            self.features = get_features_by_project(self.current_project.id)
            self.update_features_display()
            self.update_status(f"Loaded {len(self.features)} features", 'success')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            self.update_status("Error loading data", 'error')
    
    def update_features_display(self):
        """Update the features listbox display."""
        self.features_listbox.delete(0, tk.END)
        for i, feature in enumerate(self.features, 1):
            display_name = f"{feature.feature} (ID: {feature.id})"
            self.features_listbox.insert(tk.END, f"{i:2d}. {display_name}")
        
        count_text = f"{len(self.features)} feature{'s' if len(self.features) != 1 else ''} loaded"
        self.features_count_label.config(text=count_text)
    
    def on_feature_select(self, event):
        """Handle feature selection."""
        selection = self.features_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_feature = self.features[index]
            self.load_events_for_feature()
    
    def load_events_for_feature(self):
        """Load events for the selected feature."""
        if not self.current_feature:
            return
        
        try:
            self.events = get_events_by_feature_id(self.current_feature.id)
            self.update_events_display()
            self.update_status(f"Loaded {len(self.events)} events for '{self.current_feature.feature}'", 'success')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load events: {e}")
            self.update_status("Error loading events", 'error')
    
    def update_events_display(self):
        """Update the events treeview display."""
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        
        for event in self.events:
            operation_name = self._get_operation_name_by_id(event.operation_id)
            
            url_display = event.url[:50] + "..." if event.url and len(event.url) > 50 else event.url or ""
            component_display = event.html_component[:50] + "..." if event.html_component and len(event.html_component) > 50 else event.html_component or ""
            input_display = event.input_text[:30] + "..." if event.input_text and len(event.input_text) > 30 else event.input_text or ""
            
            self.events_tree.insert('', 'end', values=(
                event.step_number,
                operation_name,
                url_display,
                component_display,
                input_display
            ))
        
        # Update events count and button states
        if self.current_feature:
            count_text = f"{len(self.events)} event{'s' if len(self.events) != 1 else ''} for '{self.current_feature.feature}'"
            # Enable buttons if there are events
            if len(self.events) > 0:
                self.run_events_button.config(state=tk.NORMAL, text="▶️ Run Events")
                self.update_feature_button.config(state=tk.NORMAL, text="🔄 Update Feature")
            else:
                self.run_events_button.config(state=tk.DISABLED, text="▶️ Run Events")
                self.update_feature_button.config(state=tk.DISABLED, text="🔄 Update Feature")
        else:
            count_text = "Select a feature to view events"
            self.run_events_button.config(state=tk.DISABLED, text="▶️ Run Events")
            self.update_feature_button.config(state=tk.DISABLED, text="🔄 Update Feature")
        self.events_count_label.config(text=count_text)
    
    def _get_operation_name_by_id(self, operation_id: int) -> str:
        """Get operation name by ID using OperationTypeMapper."""
        try:
            operation_name = self.operation_mapper.get_operation_name_by_id(operation_id)
            return operation_name if operation_name else f"Operation {operation_id}"
        except Exception:
            return f"Operation {operation_id}"
    
    def create_controls_panel(self, parent):
        """Create the modern controls panel."""
        controls_frame = tk.Frame(parent, bg=self.colors['background'])
        controls_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Left side - Action buttons
        buttons_frame = tk.Frame(controls_frame, bg=self.colors['background'])
        buttons_frame.pack(side=tk.LEFT)
        
        # Refresh button
        self.refresh_button = tk.Button(buttons_frame,
                                      text="🔄 Refresh Data",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=self.colors['secondary'],
                                      fg='white',
                                      relief=tk.FLAT,
                                      bd=0,
                                      padx=20,
                                      pady=10,
                                      cursor='hand2',
                                      command=self.refresh_data)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create new feature button
        self.new_feature_button = tk.Button(buttons_frame,
                                          text="🆕 Create New Feature",
                                          font=('Segoe UI', 10, 'bold'),
                                          bg=self.colors['success'],
                                          fg='white',
                                          relief=tk.FLAT,
                                          bd=0,
                                          padx=20,
                                          pady=10,
                                          cursor='hand2',
                                          command=self.create_new_feature)
        self.new_feature_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side - Status info
        status_frame = tk.Frame(controls_frame, bg=self.colors['background'])
        status_frame.pack(side=tk.RIGHT)
        
        # Add hover effects
        self.add_hover_effects()
    
    def add_hover_effects(self):
        """Add modern hover effects to buttons."""
        def on_enter(button, original_color, hover_color):
            button.config(bg=hover_color)
        
        def on_leave(button, original_color):
            button.config(bg=original_color)
        
        # Refresh button hover
        self.refresh_button.bind("<Enter>", lambda e: on_enter(self.refresh_button, self.colors['secondary'], self.colors['hover']))
        self.refresh_button.bind("<Leave>", lambda e: on_leave(self.refresh_button, self.colors['secondary']))
        
        # New feature button hover
        self.new_feature_button.bind("<Enter>", lambda e: on_enter(self.new_feature_button, self.colors['success'], self.colors['hover']))
        self.new_feature_button.bind("<Leave>", lambda e: on_leave(self.new_feature_button, self.colors['success']))
        
    # Completion handlers
    def _events_execution_completed(self, success, feature, events):
        """Handle events execution completion."""
        if success:
            self.update_status(f"Successfully executed {len(events)} events for '{feature.feature}'", 'success')
            messagebox.showinfo("Success", f"Successfully executed {len(events)} events for '{feature.feature}'!")
        else:
            self.update_status("Event execution failed", 'error')
            messagebox.showerror("Error", "Some events failed to execute. Check the console for details.")
    
    def _events_execution_error(self, error_msg):
        """Handle events execution error."""
        self.update_status("Event execution error", 'error')
        messagebox.showerror("Error", f"Event execution failed: {error_msg}")
    
    def _module_execution_completed(self, success, module):
        """Handle module execution completion."""
        if success:
            self.update_status(f"Successfully executed testing module '{module['testing_module']}'", 'success')
            messagebox.showinfo("Success", f"Successfully executed testing module '{module['testing_module']}'!")
        else:
            self.update_status("Module execution failed", 'error')
            messagebox.showerror("Error", "Module execution failed. Check the console for details.")
    
    def _module_execution_error(self, error_msg):
        """Handle module execution error."""
        self.update_status("Module execution error", 'error')
        messagebox.showerror("Error", f"Module execution failed: {error_msg}")
    
    def _automation_completed(self, success):
        """Handle automation completion."""
        if success:
            self.update_status("Automation completed successfully!", 'success')
            messagebox.showinfo("Success", "Automation workflow completed successfully!")
            self.refresh_data()
        else:
            self.update_status("Automation failed", 'error')
            messagebox.showerror("Error", "Automation workflow failed!")
    
    def _automation_error(self, error_msg):
        """Handle automation error."""
        self.update_status("Automation error", 'error')
        messagebox.showerror("Error", f"Automation failed: {error_msg}")
    
    def _update_completed(self, success):
        """Handle update completion."""
        if success:
            self.update_status("Feature update completed successfully!", 'success')
            messagebox.showinfo("Success", "Feature updated successfully!")
            self.refresh_data()
        else:
            self.update_status("Feature update failed", 'error')
            messagebox.showerror("Error", "Feature update failed!")
    
    def _update_error(self, error_msg):
        """Handle update error."""
        self.update_status("Update error", 'error')
        messagebox.showerror("Error", f"Feature update failed: {error_msg}")
    
    def refresh_data(self):
        """Refresh data from database."""
        self.update_status("Refreshing data...", 'info')
        self.operation_mapper.load_operation_types()  # Refresh mapper
        
        if self.current_view == 'testing_modules':
            if self.testing_module_page:
                self.testing_module_page.refresh_data()
        else:
            self.load_data()
            if self.current_feature:
                self.load_events_for_feature()
        
        self.update_status("Data refreshed successfully", 'success')
    
    def update_status(self, message, status_type='info'):
        """Update the status indicator and message."""
        status_colors = {
            'success': self.colors['success'],
            'error': self.colors['accent'],
            'warning': self.colors['warning'],
            'info': self.colors['text_light']
        }
        
        self.status_indicator.config(fg=status_colors.get(status_type, self.colors['text_light']))
        self.status_label.config(text=message, fg=status_colors.get(status_type, self.colors['text_light']))
    
    def create_new_feature(self):
        """Create a new feature using automation workflow."""
        if not self.current_project:
            messagebox.showerror("Error", "No project selected!")
            return
        
        open_create_feature_dialog(self.root, self.update_status, self.refresh_data, self.current_project.id)
    
    def update_feature(self):
        """Update an existing feature using update automation workflow."""
        if not self.current_feature or not self.events:
            messagebox.showwarning("Warning", "No feature selected or no events to update!")
            return
        
        events_update_feature_workflow(self.root, self.update_status, self.current_feature, self.events)
        # Refresh after update completes
        def refresh_after_delay():
            self.root.after(1000, self.refresh_data)
        refresh_after_delay()
    
    def run_events(self):
        """Run all events for the selected feature."""
        if not self.current_feature or not self.events:
            messagebox.showwarning("Warning", "No events to run!")
            return
        
        events_run_events_for_feature(self.root, self.update_status, self.current_feature, self.events)


def main():
    """Main function to run the desktop UI."""
    try:
        app = DesktopUI()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
