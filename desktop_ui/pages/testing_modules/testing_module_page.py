"""
Testing Module Component - Handles testing module creation and flow management.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Optional, Dict, Any
from model.database import (
    get_all_testing_modules, create_testing_module, get_testing_module_flow,
    add_feature_to_testing_module,
    remove_from_testing_module, clear_testing_module_flow, delete_testing_module,
    reorder_testing_module_step
)
from model.database import get_all_features, get_features_by_project
from model.feature import Feature


class TestingModulePage:
    """Testing Module component for the desktop UI."""
    
    def __init__(self, parent_frame, colors, on_run_module_callback, project_id: int = None):
        """Initialize the testing module component.
        
        Args:
            parent_frame: Parent frame to attach to
            colors: Color scheme dictionary
            on_run_module_callback: Callback function when run module is clicked
            project_id: Optional project ID to filter features
        """
        self.parent_frame = parent_frame
        self.colors = colors
        self.on_run_module_callback = on_run_module_callback
        self.project_id = project_id
        
        # Data
        self.testing_modules = []  # List of testing module dictionaries
        self.current_module = None
        self.module_flow = []  # Current module's flow
        self.features = []  # Available features
        
        # Create UI components
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Create the testing module page widgets."""
        # Main container
        main_container = tk.Frame(self.parent_frame, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Content area with three panels
        content_frame = tk.Frame(main_container, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Left panel - Testing Modules
        self.create_modules_panel(content_frame)
        
        # Middle panel - Available Items
        self.create_available_panel(content_frame)
        
        # Right panel - Module Flow
        self.create_flow_panel(content_frame)
    
    def create_header(self, parent):
        """Create the header section."""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(header_frame,
                              text="🧪 Testing Module Manager",
                              font=('Segoe UI', 20, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(header_frame,
                                 text="Create and manage testing flows",
                                 font=('Segoe UI', 12),
                                 fg=self.colors['text_light'],
                                 bg=self.colors['background'])
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(5, 0))
    
    def create_modules_panel(self, parent):
        """Create the testing modules panel."""
        # Modules card
        modules_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        modules_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Modules header
        modules_header = tk.Frame(modules_card, bg=self.colors['primary'], height=50)
        modules_header.pack(fill=tk.X)
        modules_header.pack_propagate(False)
        
        modules_title = tk.Label(modules_header,
                                text="📦 Testing Modules",
                                font=('Segoe UI', 14, 'bold'),
                                fg='white',
                                bg=self.colors['primary'])
        modules_title.pack(pady=15)
        
        # Modules content
        modules_content = tk.Frame(modules_card, bg=self.colors['surface'])
        modules_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Modules listbox
        listbox_frame = tk.Frame(modules_content, bg=self.colors['surface'])
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.modules_listbox = tk.Listbox(listbox_frame,
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
        self.modules_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.modules_listbox.bind('<<ListboxSelect>>', self.on_module_select)
        
        # Scrollbar for modules
        modules_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.modules_listbox.yview)
        modules_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.modules_listbox.configure(yscrollcommand=modules_scrollbar.set)
        
        # Modules count
        self.modules_count_label = tk.Label(modules_content,
                                          text="No modules loaded",
                                          font=('Segoe UI', 9),
                                          fg=self.colors['text_light'],
                                          bg=self.colors['surface'])
        self.modules_count_label.pack(pady=(10, 0))
        
        # Module action buttons
        module_buttons_frame = tk.Frame(modules_content, bg=self.colors['surface'])
        module_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.new_module_button = tk.Button(module_buttons_frame,
                                         text="🆕 New Module",
                                         font=('Segoe UI', 9, 'bold'),
                                         bg=self.colors['success'],
                                         fg='white',
                                         relief=tk.FLAT,
                                         bd=0,
                                         padx=10,
                                         pady=5,
                                         cursor='hand2',
                                         command=self.create_new_module)
        self.new_module_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_module_button = tk.Button(module_buttons_frame,
                                            text="🗑️ Delete",
                                            font=('Segoe UI', 9, 'bold'),
                                            bg=self.colors['accent'],
                                            fg='white',
                                            relief=tk.FLAT,
                                            bd=0,
                                            padx=10,
                                            pady=5,
                                            cursor='hand2',
                                            command=self.delete_module,
                                            state=tk.DISABLED)
        self.delete_module_button.pack(side=tk.LEFT)
    
    def create_available_panel(self, parent):
        """Create the available items panel."""
        # Available card
        available_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        available_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Available header
        available_header = tk.Frame(available_card, bg=self.colors['primary'], height=50)
        available_header.pack(fill=tk.X)
        available_header.pack_propagate(False)
        
        available_title = tk.Label(available_header,
                                  text="📋 Available Features",
                                  font=('Segoe UI', 14, 'bold'),
                                  fg='white',
                                  bg=self.colors['primary'])
        available_title.pack(pady=15)
        
        # Available content
        available_content = tk.Frame(available_card, bg=self.colors['surface'])
        available_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Features listbox
        features_listbox_frame = tk.Frame(available_content, bg=self.colors['surface'])
        features_listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.features_listbox = tk.Listbox(features_listbox_frame,
                                         font=('Segoe UI', 10),
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
        
        features_scrollbar = tk.Scrollbar(features_listbox_frame, orient=tk.VERTICAL, command=self.features_listbox.yview)
        features_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.features_listbox.configure(yscrollcommand=features_scrollbar.set)
        
        # Add feature button
        add_feature_button = tk.Button(available_content,
                                     text="➕ Add Feature to Flow",
                                     font=('Segoe UI', 9, 'bold'),
                                     bg=self.colors['success'],
                                     fg='white',
                                     relief=tk.FLAT,
                                     bd=0,
                                     padx=10,
                                     pady=5,
                                     cursor='hand2',
                                     command=self.add_feature_to_flow)
        add_feature_button.pack(fill=tk.X, pady=(10, 0))
    
    def create_flow_panel(self, parent):
        """Create the module flow panel."""
        # Flow card
        flow_card = tk.Frame(parent, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        flow_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Flow header
        flow_header = tk.Frame(flow_card, bg=self.colors['primary'], height=50)
        flow_header.pack(fill=tk.X)
        flow_header.pack_propagate(False)
        
        flow_title = tk.Label(flow_header,
                             text="🔄 Module Flow",
                             font=('Segoe UI', 14, 'bold'),
                             fg='white',
                             bg=self.colors['primary'])
        flow_title.pack(pady=15)
        
        # Flow content
        flow_content = tk.Frame(flow_card, bg=self.colors['surface'])
        flow_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Flow treeview container with fixed height
        tree_container = tk.Frame(flow_content, bg=self.colors['surface'])
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        tree_frame = tk.Frame(tree_container, bg=self.colors['surface'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Step', 'Name')
        self.flow_tree = ttk.Treeview(tree_frame,
                                    columns=columns,
                                    show='headings',
                                    style='Modern.Treeview',
                                    height=12)  # Reduced height to ensure buttons are visible
        
        # Configure column headings
        self.flow_tree.heading('Step', text='Step', anchor=tk.CENTER)
        self.flow_tree.heading('Name', text='Feature Name', anchor=tk.W)
        
        # Configure column widths
        self.flow_tree.column('Step', width=60, minwidth=60, anchor=tk.CENTER)
        self.flow_tree.column('Name', width=400, minwidth=200, anchor=tk.W)
        
        self.flow_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.flow_tree.bind('<<TreeviewSelect>>', self.on_flow_item_select)
        
        # Scrollbar for flow
        flow_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.flow_tree.yview)
        flow_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.flow_tree.configure(yscrollcommand=flow_scrollbar.set)
        
        # Flow count and action buttons - Fixed layout for full screen
        flow_bottom_frame = tk.Frame(flow_content, bg=self.colors['surface'], height=50)
        flow_bottom_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        flow_bottom_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Left side - Flow count
        left_frame = tk.Frame(flow_bottom_frame, bg=self.colors['surface'])
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.flow_count_label = tk.Label(left_frame,
                                       text="Select a module to view flow",
                                       font=('Segoe UI', 9),
                                       fg=self.colors['text_light'],
                                       bg=self.colors['surface'])
        self.flow_count_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side - Action buttons (increased width for all buttons)
        action_buttons_frame = tk.Frame(flow_bottom_frame, bg=self.colors['surface'], width=380)
        action_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        action_buttons_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.move_up_button = tk.Button(action_buttons_frame,
                                       text="⬆️ Up",
                                       font=('Segoe UI', 9, 'bold'),
                                       bg=self.colors['secondary'],
                                       fg='white',
                                       relief=tk.RAISED,
                                       bd=1,
                                       padx=12,
                                       pady=6,
                                       cursor='hand2',
                                       command=self.move_item_up,
                                       state=tk.DISABLED)
        self.move_up_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
        
        self.move_down_button = tk.Button(action_buttons_frame,
                                         text="⬇️ Down",
                                         font=('Segoe UI', 9, 'bold'),
                                         bg=self.colors['secondary'],
                                         fg='white',
                                         relief=tk.RAISED,
                                         bd=1,
                                         padx=12,
                                         pady=6,
                                         cursor='hand2',
                                         command=self.move_item_down,
                                         state=tk.DISABLED)
        self.move_down_button.pack(side=tk.RIGHT, padx=(0, 8), pady=5)
        
        self.remove_item_button = tk.Button(action_buttons_frame,
                                          text="➖ Remove",
                                          font=('Segoe UI', 9, 'bold'),
                                          bg=self.colors['accent'],
                                          fg='white',
                                          relief=tk.RAISED,
                                          bd=1,
                                          padx=15,
                                          pady=6,
                                          cursor='hand2',
                                          command=self.remove_selected_item,
                                          state=tk.DISABLED)
        self.remove_item_button.pack(side=tk.RIGHT, padx=(0, 8), pady=5)
        
        self.run_module_button = tk.Button(action_buttons_frame,
                                        text="▶️ Run Module",
                                        font=('Segoe UI', 9, 'bold'),
                                        bg=self.colors['warning'],
                                        fg='white',
                                        relief=tk.RAISED,
                                        bd=1,
                                        padx=15,
                                        pady=6,
                                        cursor='hand2',
                                        command=self.run_module,
                                        state=tk.DISABLED)
        self.run_module_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
    
    def load_data(self):
        """Load all data from database."""
        try:
            # Load testing modules
            self.testing_modules = get_all_testing_modules()
            self.update_modules_display()
            
            # Load features - filter by project if project_id is provided
            if self.project_id:
                self.features = get_features_by_project(self.project_id)
            else:
                self.features = get_all_features()
            self.update_features_display()
            
            # Events list no longer used in feature-only flows
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            return False
    
    def refresh_data(self):
        """Refresh data from database."""
        return self.load_data()
    
    def update_modules_display(self):
        """Update the modules listbox display."""
        self.modules_listbox.delete(0, tk.END)
        for i, module in enumerate(self.testing_modules, 1):
            self.modules_listbox.insert(tk.END, f"{i:2d}. {module['testing_module']} (ID: {module['id']})")
        
        # Update modules count
        count_text = f"{len(self.testing_modules)} module{'s' if len(self.testing_modules) != 1 else ''} loaded"
        self.modules_count_label.config(text=count_text)
    
    def update_features_display(self):
        """Update the features listbox display."""
        self.features_listbox.delete(0, tk.END)
        for i, feature in enumerate(self.features, 1):
            self.features_listbox.insert(tk.END, f"{i:2d}. {feature.feature} (ID: {feature.id})")
    
    # Events UI removed
    
    def update_flow_display(self):
        """Update the flow treeview display."""
        # Clear existing items
        for item in self.flow_tree.get_children():
            self.flow_tree.delete(item)
        
        # Add flow items
        for item in self.module_flow:
            # Feature-only: only show step and feature name
            self.flow_tree.insert('', 'end', values=(
                item['step_number'],
                item['feature_name']
            ))
        
        # Update flow count and button states
        if self.current_module:
            count_text = f"{len(self.module_flow)} item{'s' if len(self.module_flow) != 1 else ''} in '{self.current_module['testing_module']}'"
            # Enable buttons if there are items
            if len(self.module_flow) > 0:
                self.run_module_button.config(state=tk.NORMAL, text="▶️ Run Module")
                self.remove_item_button.config(state=tk.NORMAL)
            else:
                self.run_module_button.config(state=tk.DISABLED, text="▶️ Run Module")
                self.remove_item_button.config(state=tk.DISABLED)
                self.move_up_button.config(state=tk.DISABLED)
                self.move_down_button.config(state=tk.DISABLED)
        else:
            count_text = "Select a module to view flow"
            self.run_module_button.config(state=tk.DISABLED, text="▶️ Run Module")
            self.remove_item_button.config(state=tk.DISABLED)
            self.move_up_button.config(state=tk.DISABLED)
            self.move_down_button.config(state=tk.DISABLED)
        self.flow_count_label.config(text=count_text)
    
    def on_flow_item_select(self, event):
        """Handle flow item selection."""
        selection = self.flow_tree.selection()
        if selection and self.current_module and len(self.module_flow) > 0:
            self.remove_item_button.config(state=tk.NORMAL)
            # Enable/disable up/down buttons based on position
            item_id = selection[0]
            children = self.flow_tree.get_children()
            current_index = children.index(item_id)
            
            self.move_up_button.config(state=tk.NORMAL if current_index > 0 else tk.DISABLED)
            self.move_down_button.config(state=tk.NORMAL if current_index < len(children) - 1 else tk.DISABLED)
        else:
            self.remove_item_button.config(state=tk.DISABLED)
            self.move_up_button.config(state=tk.DISABLED)
            self.move_down_button.config(state=tk.DISABLED)
    
    def on_module_select(self, event):
        """Handle module selection."""
        selection = self.modules_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_module = self.testing_modules[index]
            self.load_module_flow()
            self.delete_module_button.config(state=tk.NORMAL)
    
    def load_module_flow(self):
        """Load the flow for the selected module."""
        if not self.current_module:
            return
        
        try:
            self.module_flow = get_testing_module_flow(self.current_module['id'])
            self.update_flow_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load module flow: {e}")
    
    def create_new_module(self):
        """Create a new testing module."""
        module_name = simpledialog.askstring("New Testing Module", "Enter module name:")
        if not module_name:
            return
        
        try:
            module_id = create_testing_module(module_name)
            # Refresh modules list
            self.load_data()
            messagebox.showinfo("Success", f"Created testing module '{module_name}' successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create testing module: {e}")
    
    def delete_module(self):
        """Delete the selected testing module."""
        if not self.current_module:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the testing module '{self.current_module['testing_module']}'?\n\nThis will also delete all flow items in this module."
        )
        
        if not result:
            return
        
        try:
            delete_testing_module(self.current_module['id'])
            self.current_module = None
            self.module_flow = []
            self.update_flow_display()
            self.delete_module_button.config(state=tk.DISABLED)
            # Refresh modules list
            self.load_data()
            messagebox.showinfo("Success", "Testing module deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete testing module: {e}")
    
    def add_feature_to_flow(self):
        """Add selected feature to the current module flow."""
        if not self.current_module:
            messagebox.showwarning("Warning", "Please select a testing module first!")
            return
        
        selection = self.features_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a feature to add!")
            return
        
        try:
            feature_index = selection[0]
            feature = self.features[feature_index]
            
            # Get next step number
            next_step = max([item['step_number'] for item in self.module_flow], default=0) + 1
            
            # Add feature to module
            add_feature_to_testing_module(self.current_module['id'], feature.id, next_step)
            
            # Refresh flow
            self.load_module_flow()
            messagebox.showinfo("Success", f"Added feature '{feature.feature}' to module flow!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add feature to flow: {e}")
    
    # add_event_to_flow removed for feature-only flows
    
    def move_item_up(self):
        """Move selected item up in the sequence."""
        selection = self.flow_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to move!")
            return
        
        try:
            item_id = selection[0]
            item = self.flow_tree.item(item_id)
            current_step = int(item['values'][0])
            
            if current_step <= 1:
                messagebox.showinfo("Info", "Item is already at the top!")
                return
            
            # Find the mapping ID for the current item
            mapping_id = None
            for flow_item in self.module_flow:
                if flow_item['step_number'] == current_step:
                    mapping_id = flow_item['mapping_id']
                    break
            
            if not mapping_id:
                messagebox.showerror("Error", "Could not find item to move!")
                return
            
            # Reorder in database
            reorder_testing_module_step(mapping_id, current_step - 1)
            
            # Refresh flow
            self.load_module_flow()
            
            # Reselect the moved item (it's now at the new position)
            children = self.flow_tree.get_children()
            if current_step - 2 >= 0:  # new index is current_step - 2 (0-based)
                self.flow_tree.selection_set(children[current_step - 2])
                self.flow_tree.focus(children[current_step - 2])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move item up: {e}")
    
    def move_item_down(self):
        """Move selected item down in the sequence."""
        selection = self.flow_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to move!")
            return
        
        try:
            item_id = selection[0]
            item = self.flow_tree.item(item_id)
            current_step = int(item['values'][0])
            
            if current_step >= len(self.module_flow):
                messagebox.showinfo("Info", "Item is already at the bottom!")
                return
            
            # Find the mapping ID for the current item
            mapping_id = None
            for flow_item in self.module_flow:
                if flow_item['step_number'] == current_step:
                    mapping_id = flow_item['mapping_id']
                    break
            
            if not mapping_id:
                messagebox.showerror("Error", "Could not find item to move!")
                return
            
            # Reorder in database
            reorder_testing_module_step(mapping_id, current_step + 1)
            
            # Refresh flow
            self.load_module_flow()
            
            # Reselect the moved item (it's now at the new position)
            children = self.flow_tree.get_children()
            if current_step < len(children):  # new index is current_step (0-based, since step is 1-based)
                self.flow_tree.selection_set(children[current_step])
                self.flow_tree.focus(children[current_step])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move item down: {e}")
    
    def remove_selected_item(self):
        """Remove selected item from the module flow."""
        selection = self.flow_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove!")
            return
        
        try:
            # Get the selected item
            item = self.flow_tree.item(selection[0])
            step_number = int(item['values'][0])  # Convert to int to match database type
            
            # Find the mapping ID
            mapping_id = None
            for flow_item in self.module_flow:
                if flow_item['step_number'] == step_number:
                    mapping_id = flow_item['mapping_id']
                    break
            
            if mapping_id:
                remove_from_testing_module(mapping_id)
                # Refresh flow
                self.load_module_flow()
                messagebox.showinfo("Success", "Item removed from module flow!")
            else:
                messagebox.showerror("Error", "Could not find item to remove!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove item: {e}")
    
    def run_module(self):
        """Run the current testing module."""
        if not self.current_module or not self.module_flow:
            messagebox.showwarning("Warning", "No module selected or no flow items to run!")
            return
        
        # Call the callback function
        if self.on_run_module_callback:
            self.on_run_module_callback(self.current_module, self.module_flow)
    
    def refresh_data(self):
        """Refresh all data from database."""
        return self.load_data()
    
    def get_current_module(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected module."""
        return self.current_module
    
    def get_module_flow(self) -> List[Dict[str, Any]]:
        """Get the current module's flow."""
        return self.module_flow
