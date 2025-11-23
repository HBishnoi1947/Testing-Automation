"""
Loading overlay utility for showing execution progress.
"""

import tkinter as tk
from typing import Optional


class LoadingOverlay:
    """A loading overlay that can be shown over the main window."""
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the loading overlay.
        
        Args:
            parent: The root window to overlay on
        """
        self.parent = parent
        self.overlay = None
        self.animation_id = None
        self.animation_frame = 0
        
    def show(self, message: str = "Execution in progress..."):
        """
        Show the loading overlay.
        
        Args:
            message: Message to display
        """
        if self.overlay is not None:
            return  # Already showing
        
        # Create overlay window
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.title("")
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.configure(bg='black')
        self.overlay.attributes('-alpha', 0.7)  # Semi-transparent
        
        # Make it fullscreen over parent
        x = self.parent.winfo_x()
        y = self.parent.winfo_y()
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")
        self.overlay.grab_set()  # Capture all events
        self.overlay.focus_set()
        
        # Center content frame
        content_frame = tk.Frame(self.overlay, bg='white', relief=tk.RAISED, bd=2)
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Loading spinner frame
        spinner_frame = tk.Frame(content_frame, bg='white')
        spinner_frame.pack(pady=20, padx=30)
        
        # Animated loading dots
        self.loading_label = tk.Label(
            spinner_frame,
            text="⏳",
            font=('Segoe UI', 40),
            bg='white',
            fg='#3498db'
        )
        self.loading_label.pack()
        
        # Message label
        self.message_label = tk.Label(
            content_frame,
            text=message,
            font=('Segoe UI', 12, 'bold'),
            bg='white',
            fg='#2c3e50',
            wraplength=300
        )
        self.message_label.pack(pady=(0, 20), padx=30)
        
        # Start animation
        self.animation_frame = 0
        self._animate()
        
        # Force update
        self.overlay.update()
        
    def _animate(self):
        """Animate the loading spinner."""
        if self.overlay is None or not self.overlay.winfo_exists():
            return
        
        # Rotate through spinner characters
        spinners = ['⏳', '⏱', '⏰', '⏲']
        self.animation_frame = (self.animation_frame + 1) % len(spinners)
        self.loading_label.config(text=spinners[self.animation_frame])
        
        # Schedule next animation
        self.animation_id = self.overlay.after(200, self._animate)
        
    def update_message(self, message: str):
        """
        Update the loading message.
        
        Args:
            message: New message to display
        """
        if self.message_label:
            self.message_label.config(text=message)
            self.overlay.update_idletasks()
    
    def hide(self):
        """Hide the loading overlay."""
        if self.overlay is None:
            return
        
        # Cancel animation
        if self.animation_id:
            try:
                self.overlay.after_cancel(self.animation_id)
            except:
                pass
        
        # Destroy overlay
        try:
            if self.overlay.winfo_exists():
                self.overlay.destroy()
        except:
            pass
        
        self.overlay = None
        self.animation_id = None
        self.animation_frame = 0

