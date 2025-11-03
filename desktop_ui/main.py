"""
Modern Desktop GUI Application for Testing Automation POC.
Provides a beautiful, modern tkinter-based interface to manage features, events, and testing modules.
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

from model.database import get_all_features, get_events_by_feature_id
from model.event import Event
from model.operation_type import OperationType, OperationTypeMapper
from run import AutomationRunner
from execute import execute_events

# Import page components
from pages import FeaturesPage, EventsPage, TestingModulePage
from desktop_ui.pages.features_events.events_page_functions import run_events_for_feature as events_run_events_for_feature, update_feature_workflow as events_update_feature_workflow
from desktop_ui.pages.features_events.features_page_functions import open_create_feature_dialog
from desktop_ui.pages.testing_modules.testing_module_page_functions import run_testing_module as tm_run_testing_module


class DesktopUI:
    """Modern Desktop GUI application for the Testing Automation POC."""
    
    def __init__(self):
        """Initialize the desktop UI with modern styling."""
        self.root = tk.Tk()
        self.root.title("🚀 Testing Automation POC - Modern UI")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        
        # Always open in full screen (maximized)
        self.root.state('zoomed')  # For Windows - maximizes the window
        # Alternative for cross-platform: self.root.attributes('-zoomed', True)
        
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
        
        
        # Configure modern styling
        self.setup_styles()
        
        # Create UI components
        self.create_widgets()
    
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
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # Main content area with notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Create tab frames
        self.features_events_frame = tk.Frame(self.notebook, bg=self.colors['background'])
        self.testing_module_frame = tk.Frame(self.notebook, bg=self.colors['background'])
        
        # Add tabs
        self.notebook.add(self.features_events_frame, text="📋 Features & Events")
        self.notebook.add(self.testing_module_frame, text="🧪 Testing Modules")
        
        # Create pages
        self.create_features_events_page()
        self.create_testing_module_page()
    
    def create_header(self, parent):
        """Create the modern header section."""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title with icon
        title_frame = tk.Frame(header_frame, bg=self.colors['background'])
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(title_frame, 
                              text="🚀 Testing Automation POC", 
                              font=('Segoe UI', 24, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        title_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = tk.Label(title_frame,
                                 text="Modern Desktop Interface",
                                 font=('Segoe UI', 12),
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
    
    def create_features_events_page(self):
        """Create the features and events page."""
        # Content frame for features and events
        content_frame = tk.Frame(self.features_events_frame, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create page components
        self.features_page = FeaturesPage(content_frame, self.colors, self.on_feature_select, self.create_new_feature, self.refresh_data)
        self.events_page = EventsPage(content_frame, self.colors, self.on_run_events, self.on_update_feature)
    
    def create_testing_module_page(self):
        """Create the testing module page."""
        # Create page component
        self.testing_module_page = TestingModulePage(self.testing_module_frame, self.colors, self.on_run_module)
    
    # Callback methods for page interactions
    def on_feature_select(self, feature):
        """Handle feature selection from features page."""
        self.events_page.load_events_for_feature(feature)
        self.update_status(f"Selected feature: {feature.feature}", 'info')
    
    def on_run_events(self, feature, events):
        """Handle run events request from events page."""
        self.run_events_for_feature(feature, events)
    
    def on_update_feature(self, feature, events):
        """Handle update feature request from events page."""
        self.update_feature_workflow(feature, events)
    
    def on_run_module(self, module, flow):
        """Handle run module request from testing module page."""
        self.run_testing_module(module, flow)
    
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
    
    # New methods for handling different workflows
    def run_events_for_feature(self, feature, events):
        """Delegate to events page workflow."""
        events_run_events_for_feature(self.root, self.update_status, feature, events)
    
    def update_feature_workflow(self, feature, events):
        """Delegate to events page workflow for update dialog and automation."""
        events_update_feature_workflow(self.root, self.update_status, feature, events)
    
    def run_testing_module(self, module, flow):
        """Delegate to testing module workflow."""
        tm_run_testing_module(self.root, self.update_status, self.features_page, module, flow)
    
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
    
    def refresh_data(self, new_feature_name=None):
        """
        Refresh data from database.
        
        Args:
            new_feature_name: If provided, auto-select this feature after refresh
        """
        self.update_status("Refreshing data...", 'info')
        
        # Refresh all pages
        self.features_page.refresh_data()
        self.events_page.refresh_data()
        self.testing_module_page.refresh_data()
        
        # ✅ If a new feature was created, auto-select it to show events
        if new_feature_name:
            self.root.after(200, lambda: self._auto_select_feature(new_feature_name))
        
        self.update_status("Data refreshed successfully", 'success')

    def _auto_select_feature(self, feature_name):
        """Auto-select a feature by name after creation."""
        try:
            # Find the feature in the features list
            for i, feature in enumerate(self.features_page.features):
                if feature.feature == feature_name:
                    # Select it in the listbox
                    self.features_page.features_listbox.selection_clear(0, tk.END)
                    self.features_page.features_listbox.selection_set(i)
                    self.features_page.features_listbox.activate(i)
                    
                    # Trigger the selection event to load events
                    self.features_page.current_feature = feature
                    self.on_feature_select(feature)
                    
                    print(f"[UI] Auto-selected newly created feature: {feature_name} (ID: {feature.id})")
                    break
        except Exception as e:
            print(f"[UI] Error auto-selecting feature: {e}")

    
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
        """Delegate to features page dialog for creating a feature."""
        open_create_feature_dialog(self.root, self.update_status, self.refresh_data)
    
    
    
    def run(self):
        """Run the desktop application."""
        # Center the window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1600
        window_height = 1000
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Start the main loop
        self.root.mainloop()


def main():
    """Main function to run the desktop UI."""
    try:
        app = DesktopUI()
        app.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
