"""
Launch Animation Window - Beautiful splash screen for the application.
"""

import tkinter as tk


class LaunchAnimationWindow:
    """Beautiful launch animation window."""

    def __init__(self, parent_callback):
        self.parent_callback = parent_callback
        self.window = tk.Tk()
        self.window.title("Testing Automation POC")

        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Window size
        window_width = 600
        window_height = 400

        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(bg='#1a1a2e')
        self.window.overrideredirect(True)  # Remove window decorations

        # Create main frame
        self.main_frame = tk.Frame(self.window, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # App icon/logo area
        self.logo_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.logo_frame.pack(expand=True)

        # Animated logo text
        self.logo_label = tk.Label(
            self.logo_frame,
            text="🚀",
            font=('Segoe UI', 80),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        self.logo_label.pack(pady=(0, 20))

        # App title
        self.title_label = tk.Label(
            self.logo_frame,
            text="Flowgen",
            font=('Segoe UI', 24, 'bold'),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        self.title_label.pack()

        # Subtitle
        self.subtitle_label = tk.Label(
            self.logo_frame,
            text="Testing Automation Tool, Powered by AI",
            font=('Segoe UI', 12),
            bg='#1a1a2e',
            fg='#3498db'
        )
        self.subtitle_label.pack(pady=(5, 30))

        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=50, pady=40)

        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=8,
            bg='#16213e',
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X)

        # Loading text
        self.loading_label = tk.Label(
            self.progress_frame,
            text="Initializing...",
            font=('Segoe UI', 10),
            bg='#1a1a2e',
            fg='#7f8c8d'
        )
        self.loading_label.pack(pady=(10, 0))

        # Animation variables
        self.progress = 0
        self.logo_scale = 1.0
        self.logo_direction = 1
        self._after_id_logo = None

        # Start animations
        self.animate_logo()
        self.animate_progress()

        self.window.mainloop()

    def animate_logo(self):
        """Animate the logo with pulse effect."""
        self.logo_scale += 0.02 * self.logo_direction

        if self.logo_scale >= 1.15:
            self.logo_direction = -1
        elif self.logo_scale <= 0.85:
            self.logo_direction = 1

        # Update logo size (simulated with font size changes)
        if hasattr(self, 'window') and self.window.winfo_exists():
            self._after_id_logo = self.window.after(50, self.animate_logo)

    def animate_progress(self):
        """Animate the progress bar."""
        if self.progress < 100:
            self.progress += 2

            # Update progress bar
            canvas_width = self.progress_canvas.winfo_width()
            if canvas_width > 1:
                progress_width = (canvas_width * self.progress) / 100
                self.progress_canvas.delete('all')

                # Gradient effect (simulated)
                self.progress_canvas.create_rectangle(
                    0, 0, progress_width, 8,
                    fill='#3498db',
                    outline=''
                )

            # Update loading text
            loading_texts = [
                "Initializing...",
                "Loading modules...",
                "Connecting to database...",
                "Preparing interface...",
                "Almost ready..."
            ]
            text_index = min(self.progress // 20, len(loading_texts) - 1)
            self.loading_label.config(text=loading_texts[text_index])

            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.after(30, self.animate_progress)
        else:
            # Animation complete, close splash and show main window
            self.window.after(200, self.close_and_launch)

    def close_and_launch(self):
        """Close splash screen and launch main application."""
        if hasattr(self, 'window') and self.window.winfo_exists():
            if self._after_id_logo:
                self.window.after_cancel(self._after_id_logo)
            self.window.destroy()
        self.parent_callback()

