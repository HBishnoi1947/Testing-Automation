"""
Project Card Component - Modern card widget for displaying projects.
"""

import tkinter as tk
from datetime import datetime
from model.project import Project


class ProjectCard(tk.Frame):
    """Modern project card widget with hover effects and metadata."""

    def __init__(self, parent, project: Project, on_select, on_delete, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.project = project
        self.on_select = on_select
        self.on_delete = on_delete
        self.colors = colors
        self.menu_visible = False

        # Card colors
        self.accent_colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#14b8a6']
        self.card_color = self.accent_colors[project.id % len(self.accent_colors)]

        self.configure(
            bg='white',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            highlightthickness=2,
            highlightbackground='#e2e8f0',
            highlightcolor=self.card_color,
            height=180  # Set minimum height for consistent card sizes
        )

        # Color accent bar at top
        color_bar = tk.Frame(self, bg=self.card_color, height=4)
        color_bar.pack(fill=tk.X)

        # Main card content
        self.card_frame = tk.Frame(self, bg='white')
        self.card_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Top section with icon, name, and three-dot menu
        top_section = tk.Frame(self.card_frame, bg='white')
        top_section.pack(fill=tk.X, pady=(0, 12))

        # Project icon with colored background (left side)
        icon_container = tk.Frame(top_section, bg=self.card_color, width=56, height=56)
        icon_container.pack(side=tk.LEFT)
        icon_container.pack_propagate(False)
        self.icon_label = tk.Label(
            icon_container,
            text="📁",
            font=('Segoe UI', 28),
            bg=self.card_color,
            fg='white'
        )
        self.icon_label.pack(expand=True)

        # Three-dot menu button (right side)
        self.menu_button = tk.Label(
            top_section,
            text="⋮",
            font=('Segoe UI', 20, 'bold'),
            bg='white',
            fg='#94a3b8',
            cursor='hand2',
            padx=8,
            pady=4
        )
        self.menu_button.pack(side=tk.RIGHT)
        self.menu_button.bind('<Button-1>', self.toggle_menu)

        # Project name container (center, between icon and menu)
        name_container = tk.Frame(top_section, bg='white')
        name_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 10))

        # Project name
        self.name_label = tk.Label(
            name_container,
            text=project.name[:50] + "..." if len(project.name) > 50 else project.name,
            font=('Segoe UI', 18, 'bold'),
            bg='white',
            fg='#1e293b',
            anchor='w',
            justify='left'
        )
        self.name_label.pack(anchor='w', pady=(8, 0))

        # Project description (full width below the top section)
        if project.description:
            desc_text = project.description[:100] + "..." if len(project.description) > 100 else project.description
            self.desc_label = tk.Label(
                self.card_frame,
                text=desc_text,
                font=('Segoe UI', 11),
                bg='white',
                fg='#64748b',
                wraplength=600,
                anchor='w',
                justify='left'
            )
            self.desc_label.pack(fill=tk.X, pady=(8, 12), anchor='w')

        # Metadata section with timestamps (full width at bottom)
        metadata_frame = tk.Frame(self.card_frame, bg='white')
        metadata_frame.pack(fill=tk.X, pady=(15, 0))

        # Parse timestamp (format: 2024-10-29 15:30:45 or 2024-10-29)
        try:
            created_date = project.created_at.split()[0] if project.created_at else "N/A"
            formatted_date = datetime.strptime(created_date, '%Y-%m-%d').strftime('%b %d, %Y')
        except:
            formatted_date = "N/A"

        # Created date with icon
        created_container = tk.Frame(metadata_frame, bg='white')
        created_container.pack(fill=tk.X, pady=2)
        created_icon = tk.Label(created_container,
                                text="📅",
                                font=('Segoe UI', 10),
                                bg='white',
                                fg='#64748b')
        created_icon.pack(side=tk.LEFT, padx=(0, 6))
        created_label = tk.Label(created_container,
                                text=f"Created: {formatted_date}",
                                font=('Segoe UI', 9),
                                bg='white',
                                fg='#64748b')
        created_label.pack(side=tk.LEFT)

        # Dropdown menu (hidden by default)
        self.dropdown_menu = tk.Frame(
            self,
            bg='white',
            relief=tk.RAISED,
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors['border']
        )
        delete_btn = tk.Label(
            self.dropdown_menu,
            text="🗑️  Delete Project",
            font=('Segoe UI', 9),
            bg='white',
            fg=self.colors['accent'],
            cursor='hand2',
            padx=15,
            pady=8
        )
        delete_btn.pack(fill=tk.X)
        delete_btn.bind('<Button-1>', lambda e: self.confirm_delete())
        delete_btn.bind('<Enter>', lambda e: delete_btn.config(bg=self.colors['background']))
        delete_btn.bind('<Leave>', lambda e: delete_btn.config(bg='white'))

        # Bind click and hover events to card and ALL child widgets
        self.bind('<Button-1>', self.on_card_click)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

        # Recursively bind events to all child widgets
        def bind_all_children(widget):
            for child in widget.winfo_children():
                # Skip menu button and dropdown
                if child not in [self.menu_button, self.dropdown_menu]:
                    child.bind('<Button-1>', self.on_card_click)
                    child.bind('<Enter>', self.on_enter)
                    child.bind('<Leave>', self.on_leave)
                    bind_all_children(child)

        bind_all_children(self)
        self.winfo_toplevel().bind('<Button-1>', self.hide_menu_on_outside_click, add='+')

    def toggle_menu(self, event):
        """Toggle dropdown menu visibility."""
        if self.menu_visible:
            self.dropdown_menu.place_forget()
            self.menu_visible = False
        else:
            # Position dropdown below three-dot button
            self.dropdown_menu.place(x=self.winfo_width() - 160, y=60)
            self.menu_visible = True
        return "break"  # Stop event propagation

    def hide_menu_on_outside_click(self, event):
        """Hide menu when clicking outside."""
        if self.menu_visible:
            # Check if click is outside the menu
            x, y = event.x_root, event.y_root
            menu_x = self.dropdown_menu.winfo_rootx()
            menu_y = self.dropdown_menu.winfo_rooty()
            menu_w = self.dropdown_menu.winfo_width()
            menu_h = self.dropdown_menu.winfo_height()

            if not (menu_x <= x <= menu_x + menu_w and menu_y <= y <= menu_y + menu_h):
                self.dropdown_menu.place_forget()
                self.menu_visible = False

    def confirm_delete(self):
        """Confirm and delete project."""
        self.dropdown_menu.place_forget()
        self.menu_visible = False
        self.on_delete(self.project)
        return "break"  # Stop event propagation

    def on_card_click(self, event):
        """Handle card click (not menu)."""
        if not self.menu_visible:
            self.on_select(self.project)

    def on_enter(self, event):
        """Handle mouse enter event with simple highlight."""
        self.configure(
            highlightbackground=self.card_color,
            highlightthickness=3
        )

    def on_leave(self, event):
        """Handle mouse leave event."""
        self.configure(
            highlightbackground='#e2e8f0',
            highlightthickness=2
        )

