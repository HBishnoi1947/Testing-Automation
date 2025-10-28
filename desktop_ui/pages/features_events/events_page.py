"""
Events Component - Handles the events panel functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from model.database import get_events_by_feature_id
from model.event import Event
from model.feature import Feature
from model.operation_type import OperationTypeMapper


class EventsPage:
    """Events component for the desktop UI."""
    
    def __init__(self, parent_frame, colors, on_run_events_callback, on_update_feature_callback):
        """Initialize the events component.
        
        Args:
            parent_frame: Parent frame to attach to
            colors: Color scheme dictionary
            on_run_events_callback: Callback function when run events is clicked
            on_update_feature_callback: Callback function when update feature is clicked
        """
        self.parent_frame = parent_frame
        self.colors = colors
        self.on_run_events_callback = on_run_events_callback
        self.on_update_feature_callback = on_update_feature_callback
        
        # Data
        self.events = []  # List of Event objects
        self.current_feature = None  # Current Feature object
        
        # Operation type mapper for efficient lookups
        self.operation_mapper = OperationTypeMapper()
        self.operation_mapper.load_operation_types()
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create the events panel widgets."""
        # Events card
        self.events_card = tk.Frame(self.parent_frame, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        self.events_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Events header
        events_header = tk.Frame(self.events_card, bg=self.colors['primary'], height=50)
        events_header.pack(fill=tk.X)
        events_header.pack_propagate(False)
        
        events_title = tk.Label(events_header,
                               text="📝 Events",
                               font=('Segoe UI', 14, 'bold'),
                               fg='white',
                               bg=self.colors['primary'])
        events_title.pack(pady=15)
        
        # Events content
        events_content = tk.Frame(self.events_card, bg=self.colors['surface'])
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
    
    def load_events_for_feature(self, feature: Feature):
        """Load events for the selected feature."""
        if not feature:
            return
        
        try:
            self.current_feature = feature
            self.events = get_events_by_feature_id(feature.id)
            self.update_events_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load events: {e}")
            return False
    
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
    
    def run_events(self):
        """Run all events for the selected feature."""
        if not self.current_feature or not self.events:
            messagebox.showwarning("Warning", "No events to run!")
            return
        
        # Call the callback function
        if self.on_run_events_callback:
            self.on_run_events_callback(self.current_feature, self.events)
    
    def update_feature(self):
        """Update an existing feature."""
        if not self.current_feature or not self.events:
            messagebox.showwarning("Warning", "No feature selected or no events to update!")
            return
        
        # Call the callback function
        if self.on_update_feature_callback:
            self.on_update_feature_callback(self.current_feature, self.events)
    
    def refresh_data(self):
        """Refresh operation mapper data."""
        self.operation_mapper.refresh()
        if self.current_feature:
            return self.load_events_for_feature(self.current_feature)
        return True
    
    def get_current_feature(self) -> Optional[Feature]:
        """Get the currently selected feature."""
        return self.current_feature
    
    def get_events(self) -> List[Event]:
        """Get the current events."""
        return self.events
    
    def set_button_state(self, run_enabled: bool, update_enabled: bool):
        """Set the state of the action buttons."""
        self.run_events_button.config(state=tk.NORMAL if run_enabled else tk.DISABLED)
        self.update_feature_button.config(state=tk.NORMAL if update_enabled else tk.DISABLED)
    
    def _get_operation_name_by_id(self, operation_id: int) -> str:
        """Get operation name by ID using OperationTypeMapper."""
        try:
            operation_name = self.operation_mapper.get_operation_name_by_id(operation_id)
            return operation_name if operation_name else f"Operation {operation_id}"
        except Exception:
            return f"Operation {operation_id}"
