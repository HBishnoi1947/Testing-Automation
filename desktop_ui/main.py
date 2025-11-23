"""
Modern Desktop GUI Application for Testing Automation with Project Support.
Provides a beautiful, modern tkinter-based interface to manage projects, features and events.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.database import get_features_by_project
from model.operation_type import OperationTypeMapper
from model.project import Project

# Import page components
from desktop_ui.pages import FeaturesPage, EventsPage, TestingModulePage
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
        self.root.title("Evently Automation Tool")
        # Set window to fullscreen
        self.root.state('zoomed')  # Maximized on Windows
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
        
        # UI page components
        self.features_page = None
        self.events_page = None
        
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
        
        # Create main widgets (FeaturesPage loads data automatically in __init__)
        self.create_widgets()
    
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
        
        # Create main widgets (FeaturesPage loads data automatically in __init__)
        self.create_widgets()
    
    def setup_styles(self):
        """Configure modern ttk styles."""
        style = ttk.Style()
        
        # Try to use a theme that supports better heading visibility
        try:
            style.theme_use('clam')  # 'clam' theme has better heading visibility on Windows
        except:
            pass  # Use default theme if 'clam' is not available
        
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
                       relief='flat',
                       borderwidth=1)
        
        # Ensure heading is always visible (not just on hover)
        style.map('Modern.Treeview.Heading',
                 background=[('active', self.colors['primary']),
                           ('!active', self.colors['primary']),
                           ('pressed', self.colors['primary']),
                           ('selected', self.colors['primary'])],
                 foreground=[('active', 'white'),
                           ('!active', 'white'),
                           ('pressed', 'white'),
                           ('selected', 'white')],
                 relief=[('active', 'flat'),
                        ('!active', 'flat')])
        
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
        project_id = self.current_project.id if self.current_project else None
        self.features_page = FeaturesPage(
            content_frame,
            self.colors,
            on_feature_select_callback=self.on_feature_select,
            on_create_feature_callback=self.create_new_feature,
            on_refresh_callback=self.refresh_data,
            project_id=project_id
        )
        
        # Right panel - Events
        self.events_page = EventsPage(
            content_frame,
            self.colors,
            on_run_events_callback=self.run_events,
            on_update_feature_callback=self.update_feature
        )
    
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
    
    def on_run_module(self, module, flow, browser="chromium"):
        """Handle run module request from testing module page."""
        tm_run_testing_module(self.root, self.update_status, None, module, flow, browser)
    
    def create_header(self, parent):
        """Create the modern header section."""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title with project name
        title_frame = tk.Frame(header_frame, bg=self.colors['background'])
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(title_frame, 
                              text=f"📦 {self.current_project.name}", 
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
        self.features_page = None
        self.events_page = None
        self.current_view = 'features_events'
        self.show_project_selection()
    
    def load_testing_modules(self):
        """Load testing modules data."""
        if self.testing_module_page:
            self.testing_module_page.load_data()
    
    def on_feature_select(self, feature):
        """Handle feature selection from FeaturesPage."""
        if self.events_page:
            self.events_page.load_events_for_feature(feature)
            self.update_status(f"Loaded events for '{feature.feature}'", 'success')
    
    def refresh_data(self):
        """Refresh data from database."""
        self.update_status("Refreshing data...", 'info')
        self.operation_mapper.load_operation_types()  # Refresh mapper
        
        if self.current_view == 'testing_modules':
            if self.testing_module_page:
                self.testing_module_page.refresh_data()
        else:
            if self.features_page:
                self.features_page.refresh_data()
            if self.events_page:
                self.events_page.refresh_data()
        
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
    
    def update_feature(self, current_feature=None, events=None):
        """Update an existing feature using update automation workflow.
        Accepts optional current_feature and events for callback compatibility.
        """
        # Allow invocation as a callback with parameters or fallback to UI state
        if current_feature is None or events is None:
            if not self.events_page:
                return
            current_feature = self.events_page.get_current_feature()
            events = self.events_page.get_events()
        
        if not current_feature or not events:
            messagebox.showwarning("Warning", "No feature selected or no events to update!")
            return
        
        events_update_feature_workflow(self.root, self.update_status, current_feature, events)
        # Refresh after update completes
        def refresh_after_delay():
            self.root.after(1000, self.refresh_data)
        refresh_after_delay()
    
    def run_events(self, current_feature=None, events=None):
        """Run all events for the selected feature.
        Accepts optional current_feature and events for callback compatibility.
        """
        # Allow invocation as a callback with parameters or fallback to UI state
        if current_feature is None or events is None:
            if not self.events_page:
                return
            current_feature = self.events_page.get_current_feature()
            events = self.events_page.get_events()
        
        if not current_feature or not events:
            messagebox.showwarning("Warning", "No events to run!")
            return
        
        events_run_events_for_feature(self.root, self.update_status, current_feature, events)


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
