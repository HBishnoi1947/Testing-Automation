"""
Modern Desktop GUI Application for Testing Automation POC.
Provides a beautiful, modern tkinter-based interface to manage features and events.
"""

import os
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


class DesktopUI:
    """Modern Desktop GUI application for the Testing Automation POC."""
    
    def __init__(self):
        """Initialize the desktop UI with modern styling."""
        self.root = tk.Tk()
        self.root.title("🚀 Testing Automation POC - Modern UI")
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
        self.features = []  # List of Feature objects
        self.events = []    # List of Event objects
        self.current_feature = None  # Current Feature object
        self.api_key = "AIzaSyA_jrCpHgsAY-J3pIeKJWPuZ76su3ug2DY"  # Replace with your API key
        
        # Operation type mapper for efficient lookups
        self.operation_mapper = OperationTypeMapper()
        self.operation_mapper.load_operation_types()
        
        # Configure modern styling
        self.setup_styles()
        
        # Create UI components
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
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Left panel - Features
        self.create_features_panel(content_frame)
        
        # Right panel - Events
        self.create_events_panel(content_frame)
        
        # Bottom panel - Controls
        self.create_controls_panel(main_container)
    
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
    
    def create_features_panel(self, parent):
        """Create the modern features panel."""
        # Features card
        features_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        features_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Features header
        features_header = tk.Frame(features_card, bg=self.colors['primary'], height=50)
        features_header.pack(fill=tk.X)
        features_header.pack_propagate(False)
        
        features_title = tk.Label(features_header,
                                 text="📋 Features",
                                 font=('Segoe UI', 14, 'bold'),
                                 fg='white',
                                 bg=self.colors['primary'])
        features_title.pack(pady=15)
        
        # Features content
        features_content = tk.Frame(features_card, bg=self.colors['surface'])
        features_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Features listbox with modern styling
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
        
        # Scrollbar for features
        features_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.features_listbox.yview)
        features_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.features_listbox.configure(yscrollcommand=features_scrollbar.set)
        
        # Features count
        self.features_count_label = tk.Label(features_content,
                                           text="No features loaded",
                                           font=('Segoe UI', 9),
                                           fg=self.colors['text_light'],
                                           bg=self.colors['surface'])
        self.features_count_label.pack(pady=(10, 0))
    
    def create_events_panel(self, parent):
        """Create the modern events panel."""
        # Events card
        events_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        events_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Events header
        events_header = tk.Frame(events_card, bg=self.colors['primary'], height=50)
        events_header.pack(fill=tk.X)
        events_header.pack_propagate(False)
        
        events_title = tk.Label(events_header,
                               text="📝 Events",
                               font=('Segoe UI', 14, 'bold'),
                               fg='white',
                               bg=self.colors['primary'])
        events_title.pack(pady=15)
        
        # Events content
        events_content = tk.Frame(events_card, bg=self.colors['surface'])
        events_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Events treeview with modern styling
        tree_frame = tk.Frame(events_content, bg=self.colors['surface'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for events
        columns = ('Step', 'Operation', 'URL', 'Component', 'Input')
        self.events_tree = ttk.Treeview(tree_frame, 
                                       columns=columns, 
                                       show='headings', 
                                       style='Modern.Treeview',
                                       height=15)
        
        # Configure column headings
        self.events_tree.heading('Step', text='Step', anchor=tk.CENTER)
        self.events_tree.heading('Operation', text='Operation', anchor=tk.W)
        self.events_tree.heading('URL', text='URL', anchor=tk.W)
        self.events_tree.heading('Component', text='Component', anchor=tk.W)
        self.events_tree.heading('Input', text='Input', anchor=tk.W)
        
        # Configure column widths
        self.events_tree.column('Step', width=60, minwidth=60, anchor=tk.CENTER)
        self.events_tree.column('Operation', width=120, minwidth=120, anchor=tk.W)
        self.events_tree.column('URL', width=250, minwidth=200, anchor=tk.W)
        self.events_tree.column('Component', width=200, minwidth=150, anchor=tk.W)
        self.events_tree.column('Input', width=150, minwidth=100, anchor=tk.W)
        
        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for events
        events_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_tree.configure(yscrollcommand=events_scrollbar.set)
        
        # Events count and run button frame
        events_bottom_frame = tk.Frame(events_content, bg=self.colors['surface'])
        events_bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Events count
        self.events_count_label = tk.Label(events_bottom_frame,
                                         text="Select a feature to view events",
                                         font=('Segoe UI', 9),
                                         fg=self.colors['text_light'],
                                         bg=self.colors['surface'])
        self.events_count_label.pack(side=tk.LEFT)
        
        # Run Events button
        self.run_events_button = tk.Button(events_bottom_frame,
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
        
        # Run events button hover
        self.run_events_button.bind("<Enter>", lambda e: on_enter(self.run_events_button, self.colors['warning'], self.colors['hover']))
        self.run_events_button.bind("<Leave>", lambda e: on_leave(self.run_events_button, self.colors['warning']))
        
    def load_data(self):
        """Load features and events from database."""
        try:
            # Load features as objects
            self.features = get_all_features()
            self.update_features_display()
            self.update_status(f"Loaded {len(self.features)} features", 'success')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            self.update_status("Error loading data", 'error')
    
    
    def update_features_display(self):
        """Update the features listbox display."""
        self.features_listbox.delete(0, tk.END)
        for i, feature in enumerate(self.features, 1):
            # Make feature names unique by adding ID if there are duplicates
            display_name = f"{feature.feature} (ID: {feature.id})"
            self.features_listbox.insert(tk.END, f"{i:2d}. {display_name}")
        
        # Update features count
        count_text = f"{len(self.features)} feature{'s' if len(self.features) != 1 else ''} loaded"
        self.features_count_label.config(text=count_text)
    
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
        # Clear existing items
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        
        # Add events
        for event in self.events:
            operation_name = self._get_operation_name_by_id(event.operation_id)
            
            # Truncate long URLs and components for display
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
        
        # Update events count and run button state
        if self.current_feature:
            count_text = f"{len(self.events)} event{'s' if len(self.events) != 1 else ''} for '{self.current_feature.feature}'"
            # Enable run button if there are events
            if len(self.events) > 0:
                self.run_events_button.config(state=tk.NORMAL, text="▶️ Run Events")
            else:
                self.run_events_button.config(state=tk.DISABLED, text="▶️ Run Events")
        else:
            count_text = "Select a feature to view events"
            self.run_events_button.config(state=tk.DISABLED, text="▶️ Run Events")
        self.events_count_label.config(text=count_text)
    
    def refresh_data(self):
        """Refresh data from database."""
        self.update_status("Refreshing data...", 'info')
        # Refresh operation mapper
        self.operation_mapper.refresh()
        # Load features
        self.load_data()
        if self.current_feature:
            self.load_events_for_feature()
    
    def create_new_feature(self):
        """Create a new feature using automation workflow."""
        # Create a simple dialog window
        input_window = tk.Toplevel(self.root)
        input_window.title("Create New Feature")
        input_window.geometry("500x400")
        input_window.configure(bg='white')
        input_window.transient(self.root)
        input_window.grab_set()
        
        # Center the window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 250
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
        input_window.geometry(f"+{x}+{y}")
        
        # Main container
        main_frame = tk.Frame(input_window, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame,
                              text="Create New Feature",
                              font=('Arial', 16, 'bold'),
                              fg='#2c3e50',
                              bg='white')
        title_label.pack(pady=(0, 20))
        
        # URL input
        url_label = tk.Label(main_frame,
                            text="Target URL:",
                            font=('Arial', 10, 'bold'),
                            fg='#2c3e50',
                            bg='white')
        url_label.pack(anchor=tk.W, pady=(0, 5))
        
        url_entry = tk.Entry(main_frame,
                            font=('Arial', 10),
                            width=60)
        url_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Prompt input
        prompt_label = tk.Label(main_frame,
                               text="Automation Prompt:",
                               font=('Arial', 10, 'bold'),
                               fg='#2c3e50',
                               bg='white')
        prompt_label.pack(anchor=tk.W, pady=(0, 5))
        
        prompt_text = tk.Text(main_frame,
                             font=('Arial', 10),
                             height=6,
                             width=60,
                             wrap=tk.WORD)
        prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def start_automation():
            url = url_entry.get().strip()
            prompt = prompt_text.get("1.0", tk.END).strip()
            
            if not url or not prompt:
                messagebox.showerror("Error", "Please enter both URL and prompt!")
                return
            
            # Close input window
            input_window.destroy()
            
            # Start automation in background thread
            self.update_status("Starting automation workflow...", 'info')
            
            def run_automation():
                try:
                    automation_runner = AutomationRunner(self.api_key)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(
                        automation_runner.run_automation_workflow(url, prompt)
                    )
                    loop.close()
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self._automation_completed(success))
                    
                except Exception as e:
                    self.root.after(0, lambda: self._automation_error(str(e)))
            
            automation_thread = threading.Thread(target=run_automation)
            automation_thread.daemon = True
            automation_thread.start()
        
        def cancel():
            input_window.destroy()
        
        # Buttons
        start_button = tk.Button(buttons_frame,
                               text="Start Automation",
                               font=('Arial', 10, 'bold'),
                               bg='#27ae60',
                               fg='white',
                               relief=tk.RAISED,
                               bd=2,
                               padx=20,
                               pady=8,
                               command=start_automation)
        start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = tk.Button(buttons_frame,
                                text="Cancel",
                                font=('Arial', 10, 'bold'),
                                bg='#e74c3c',
                                fg='white',
                                relief=tk.RAISED,
                                bd=2,
                                padx=20,
                                pady=8,
                                command=cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Focus on URL entry
        url_entry.focus()
    
    def run_events(self):
        """Run all events for the selected feature."""
        if not self.current_feature or not self.events:
            messagebox.showwarning("Warning", "No events to run!")
            return
        
        # Confirm before running
        result = messagebox.askyesno(
            "Confirm Execution", 
            f"Are you sure you want to run {len(self.events)} events for '{self.current_feature.feature}'?\n\nThis will open a browser and execute the automation steps."
        )
        
        if not result:
            return
        
        # Disable the run button and update status
        self.run_events_button.config(state=tk.DISABLED, text="⏳ Running...")
        self.update_status(f"Running {len(self.events)} events for '{self.current_feature.feature}'...", 'info')
        
        # Run events in background thread
        def run_events_thread():
            try:
                # Use the new execute_events function
                success = execute_events(self.events, headless=False)
                
                # Update UI in main thread
                self.root.after(0, lambda: self._events_execution_completed(success))
                
            except Exception as e:
                self.root.after(0, lambda: self._events_execution_error(str(e)))
        
        events_thread = threading.Thread(target=run_events_thread)
        events_thread.daemon = True
        events_thread.start()
    
    def _events_execution_completed(self, success):
        """Handle events execution completion."""
        if success:
            self.update_status(f"Successfully executed {len(self.events)} events for '{self.current_feature.feature}'", 'success')
            messagebox.showinfo("Success", f"Successfully executed {len(self.events)} events for '{self.current_feature.feature}'!")
        else:
            self.update_status("Event execution failed", 'error')
            messagebox.showerror("Error", "Some events failed to execute. Check the console for details.")
        
        # Re-enable the run button
        self.run_events_button.config(state=tk.NORMAL, text="▶️ Run Events")
    
    def _events_execution_error(self, error_msg):
        """Handle events execution error."""
        self.update_status("Event execution error", 'error')
        messagebox.showerror("Error", f"Event execution failed: {error_msg}")
        
        # Re-enable the run button
        self.run_events_button.config(state=tk.NORMAL, text="▶️ Run Events")
    
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
    
    
    def _get_operation_name_by_id(self, operation_id: int) -> str:
        """Get operation name by ID using OperationTypeMapper."""
        try:
            operation_name = self.operation_mapper.get_operation_name_by_id(operation_id)
            return operation_name if operation_name else f"Operation {operation_id}"
        except Exception:
            return f"Operation {operation_id}"
    
    def run(self):
        """Run the desktop application."""
        # Center the window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1400
        window_height = 900
        
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
