"""
Features Component - Handles the features panel functionality.
"""

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from model.database import get_all_features, get_features_by_project, delete_feature_by_feature_id
from model.feature import Feature


class FeaturesPage:
    """Features component for the desktop UI."""
    
    def __init__(self, parent_frame, colors, on_feature_select_callback, on_create_feature_callback, on_refresh_callback, project_id: Optional[int] = None):
        """Initialize the features component.
        
        Args:
            parent_frame: Parent frame to attach to
            colors: Color scheme dictionary
            on_feature_select_callback: Callback function when feature is selected
            on_create_feature_callback: Callback function when create feature is clicked
            on_refresh_callback: Callback function when refresh is clicked
            project_id: Optional project ID to filter features by project
        """
        self.parent_frame = parent_frame
        self.colors = colors
        self.on_feature_select_callback = on_feature_select_callback
        self.on_create_feature_callback = on_create_feature_callback
        self.on_refresh_callback = on_refresh_callback
        self.project_id = project_id
        
        # Data
        self.features = []  # List of Feature objects
        self.current_feature = None
        
        # Create UI components
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Create the features panel widgets."""
        # Features card
        self.features_card = tk.Frame(self.parent_frame, bg=self.colors['surface'], relief=tk.RAISED, bd=1)
        self.features_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Features header
        features_header = tk.Frame(self.features_card, bg=self.colors['primary'], height=50)
        features_header.pack(fill=tk.X)
        features_header.pack_propagate(False)
        
        features_title = tk.Label(features_header,
                                 text="📋 Features",
                                 font=('Segoe UI', 14, 'bold'),
                                 fg='white',
                                 bg=self.colors['primary'])
        features_title.pack(pady=15)
        
        # Features content
        features_content = tk.Frame(self.features_card, bg=self.colors['surface'])
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
        
        # Action buttons frame
        buttons_frame = tk.Frame(features_content, bg=self.colors['surface'])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Refresh button
        self.refresh_button = tk.Button(buttons_frame,
                                      text="🔄 Refresh",
                                      font=('Segoe UI', 9, 'bold'),
                                      bg=self.colors['secondary'],
                                      fg='white',
                                      relief=tk.FLAT,
                                      bd=0,
                                      padx=15,
                                      pady=5,
                                      cursor='hand2',
                                      command=self.refresh_data)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create new feature button
        self.new_feature_button = tk.Button(buttons_frame,
                                          text="🆕 New Feature",
                                          font=('Segoe UI', 9, 'bold'),
                                          bg=self.colors['success'],
                                          fg='white',
                                          relief=tk.FLAT,
                                          bd=0,
                                          padx=15,
                                          pady=5,
                                          cursor='hand2',
                                          command=self.create_new_feature)
        self.new_feature_button.pack(side=tk.LEFT)
        
        # Delete feature button
        self.delete_feature_button = tk.Button(buttons_frame,
                                             text="🗑 Delete",
                                             font=('Segoe UI', 9, 'bold'),
                                             bg='crimson',
                                             fg='white',
                                             relief=tk.FLAT,
                                             bd=0,
                                             padx=15,
                                             pady=5,
                                             cursor='hand2',
                                             command=self.delete_selected_feature)
        self.delete_feature_button.pack(side=tk.RIGHT)
    
    def load_data(self):
        """Load features from database."""
        try:
            # Load features as objects - filter by project if project_id is provided
            if self.project_id:
                self.features = get_features_by_project(self.project_id)
            else:
                self.features = get_all_features()
            self.update_features_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load features: {e}")
            return False
    
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
    
    def on_feature_select(self, event):
        """Handle feature selection."""
        selection = self.features_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_feature = self.features[index]
            # Call the callback function
            if self.on_feature_select_callback:
                self.on_feature_select_callback(self.current_feature)
    
    def refresh_data(self):
        """Refresh features data."""
        return self.load_data()
    
    def create_new_feature(self):
        """Create a new feature using automation workflow."""
        # Call the callback function
        if self.on_create_feature_callback:
            self.on_create_feature_callback()

    def delete_selected_feature(self):
        """Delete the currently selected feature from the database."""
        if not self.current_feature:
            messagebox.showwarning("No selection", "Please select a feature to delete.")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete feature '{self.current_feature.feature}' (ID: {self.current_feature.id})?\n\nThis will remove all its events.")
        if not confirm:
            return
        
        try:
            delete_feature_by_feature_id(self.current_feature.id)
            messagebox.showinfo("Deleted", f"Deleted feature '{self.current_feature.feature}'.")
            self.current_feature = None
            self.refresh_data()
            # Notify parent to refresh other pages (e.g., testing module page)
            if self.on_refresh_callback:
                self.on_refresh_callback()
        except Exception as e:
            messagebox.showerror("Delete failed", str(e))
    
    def get_current_feature(self) -> Optional[Feature]:
        """Get the currently selected feature."""
        return self.current_feature
    
    def get_all_features(self) -> List[Feature]:
        """Get all features."""
        return self.features
