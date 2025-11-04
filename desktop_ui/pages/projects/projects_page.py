"""
Projects Page - Main project selection and management interface.
"""

import tkinter as tk
from tkinter import messagebox
from typing import List
from model.database import get_all_projects, create_project, delete_project
from model.project import Project
from .project_card import ProjectCard


class ProjectsPage:
    """Projects selection page with professional card-based layout."""

    def __init__(self, root, colors, on_project_select, on_back_callback=None):
        """
        Initialize the projects page.

        Args:
            root: Root window
            colors: Color scheme dictionary
            on_project_select: Callback function when a project is selected
            on_back_callback: Optional callback for back button
        """
        self.root = root
        self.colors = colors
        self.on_project_select = on_project_select
        self.on_back_callback = on_back_callback
        self.projects = []
        self.projects_canvas = None

        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Main container - gradient background
        self.container = tk.Frame(self.root, bg='#f8f9fa')
        self.container.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        # Create UI components
        self.create_header()
        self.create_projects_container()
        self.load_projects()

    def create_header(self):
        """Create the header section with title and subtitle."""
        header_frame = tk.Frame(self.container, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, pady=(0, 30))

        # Title section
        title_container = tk.Frame(header_frame, bg='#f8f9fa')
        title_container.pack()

        title_label = tk.Label(
            title_container,
            text="Projects",
            font=('Segoe UI', 32, 'bold'),
            fg='#1e293b',
            bg='#f8f9fa'
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_container,
            text="Manage and organize your projects",
            font=('Segoe UI', 13),
            fg='#64748b',
            bg='#f8f9fa'
        )
        subtitle_label.pack(pady=(8, 0))

        # Separator line
        separator = tk.Frame(self.container, bg=self.colors['border'], height=1)
        separator.pack(fill=tk.X, pady=(10, 20))

    def create_projects_container(self):
        """Create the scrollable projects container with grid layout."""
        # Projects container with scrollbar
        projects_container = tk.Frame(self.container, bg=self.colors['background'])
        projects_container.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar
        canvas = tk.Canvas(projects_container, bg='#f8f9fa', highlightthickness=0)
        scrollbar = tk.Scrollbar(projects_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f8f9fa')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make scrollable frame expand to canvas width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width - 4)  # -4 for scrollbar

        canvas.bind('<Configure>', on_canvas_configure)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.projects_canvas = canvas
        self.scrollable_frame = scrollable_frame

        # Mouse wheel binding
        def on_mouse_wheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # Configure grid columns for equal width
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

        # Store scrollable frame for adding cards later
        self.scrollable_frame = scrollable_frame

        # Projects count with modern styling
        count_frame = tk.Frame(self.container, bg='#f8f9fa')
        count_frame.pack(fill=tk.X, pady=(25, 0))

        separator2 = tk.Frame(count_frame, bg='#e2e8f0', height=1)
        separator2.pack(fill=tk.X, pady=(0, 15))

        self.projects_count_label = tk.Label(
            count_frame,
            text="0 projects available",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['text'],
            bg='#f8f9fa'
        )
        self.projects_count_label.pack()

    def load_projects(self):
        """Load projects from database and display them."""
        try:
            self.projects = get_all_projects()
            self.update_projects_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load projects: {e}")

    def update_projects_display(self):
        """Update the projects grid display with cards."""
        # Clear existing project cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        cards_per_row = 2
        current_row = 0
        current_col = 0

        # Create New Project button at the top
        create_btn_frame = tk.Frame(self.scrollable_frame, bg='#f8f9fa')
        create_btn_frame.grid(row=current_row, column=0, columnspan=2, padx=12, pady=(0, 20), sticky='w')

        create_button = tk.Button(
            create_btn_frame,
            text="✨ Create New Project",
            font=('Segoe UI', 11, 'bold'),
            bg='#1e293b',
            fg='white',
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=12,
            cursor='hand2',
            command=self.create_new_project
        )
        create_button.pack(side=tk.LEFT)

        def on_create_enter(e):
            create_button.config(bg='#334155')

        def on_create_leave(e):
            create_button.config(bg='#1e293b')

        create_button.bind('<Enter>', on_create_enter)
        create_button.bind('<Leave>', on_create_leave)

        current_row += 1

        # Add project cards
        for project in self.projects:
            if current_col >= cards_per_row:
                current_col = 0
                current_row += 1

            project_card = ProjectCard(
                self.scrollable_frame,
                project=project,
                on_select=self.on_project_select,
                on_delete=self.delete_project_card,
                colors=self.colors
            )

            # Use sticky='ew' to make cards expand horizontally
            if current_col == 0:
                project_card.grid(row=current_row, column=current_col, padx=(0, 12), pady=12, sticky='ew')
            else:
                project_card.grid(row=current_row, column=current_col, padx=(12, 0), pady=12, sticky='ew')

            # Configure row height
            self.scrollable_frame.grid_rowconfigure(current_row, minsize=200)

            current_col += 1

        # Update projects count
        count_text = f"{len(self.projects)} project{'s' if len(self.projects) != 1 else ''} available"
        self.projects_count_label.config(text=count_text)

    def create_new_project(self):
        """Open dialog to create a new project."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Project")
        dialog.geometry("450x250")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 125
        dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(dialog, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text="Create New Project",
            font=('Arial', 14, 'bold'),
            fg='#2c3e50',
            bg='white'
        )
        title_label.pack(pady=(0, 15))

        # Name input
        name_label = tk.Label(
            main_frame,
            text="Project Name:",
            font=('Arial', 10, 'bold'),
            fg='#2c3e50',
            bg='white'
        )
        name_label.pack(anchor=tk.W, pady=(0, 5))

        name_entry = tk.Entry(main_frame, font=('Arial', 10), width=50)
        name_entry.pack(fill=tk.X, pady=(0, 10))

        # Description input
        desc_label = tk.Label(
            main_frame,
            text="Description (Optional):",
            font=('Arial', 10, 'bold'),
            fg='#2c3e50',
            bg='white'
        )
        desc_label.pack(anchor=tk.W, pady=(0, 5))

        desc_entry = tk.Entry(main_frame, font=('Arial', 10), width=50)
        desc_entry.pack(fill=tk.X, pady=(0, 15))

        def create():
            name = name_entry.get().strip()
            description = desc_entry.get().strip() or None

            if not name:
                messagebox.showerror("Error", "Please enter a project name!")
                return

            try:
                project_id = create_project(name, description)
                messagebox.showinfo("Success", f"Project '{name}' created successfully!")
                dialog.destroy()
                self.load_projects()  # Reload projects to show new one
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create project: {e}")

        buttons_frame = tk.Frame(main_frame, bg='white')
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        create_button = tk.Button(
            buttons_frame,
            text="Create",
            font=('Arial', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=8,
            command=create
        )
        create_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = tk.Button(
            buttons_frame,
            text="Cancel",
            font=('Arial', 10, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=8,
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT)

        name_entry.focus()

    def delete_project_card(self, project: Project):
        """Delete a project from card."""
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete project '{project.name}'?\n\n"
            f"This will also delete all features and events associated with this project."
        )

        if result:
            try:
                delete_project(project.id)
                messagebox.showinfo("Success", f"Project '{project.name}' deleted successfully!")
                self.load_projects()  # Reload projects after deletion
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete project: {e}")

