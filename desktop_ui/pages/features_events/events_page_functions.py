"""
Events page workflows and actions extracted from the main UI.
"""

import threading
import asyncio
import tkinter as tk
from tkinter import messagebox
from typing import List

from execute import execute_events
from run import AutomationRunner


def run_events_for_feature(root: tk.Tk, update_status, feature, events: List):
    """Run all events for the selected feature in a background thread."""
    if not feature or not events:
        messagebox.showwarning("Warning", "No events to run!")
        return

    result = messagebox.askyesno(
        "Confirm Execution",
        f"Are you sure you want to run {len(events)} events for '{feature.feature}'?\n\nThis will open a browser and execute the automation steps."
    )
    if not result:
        return

    update_status(f"Running {len(events)} events for '{feature.feature}'...", 'info')

    def _worker():
        try:
            success = execute_events(events, headless=False)
            root.after(0, lambda: _events_execution_completed(root, update_status, success, feature, events))
        except Exception as e:
            root.after(0, lambda: _events_execution_error(update_status, str(e)))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def update_feature_workflow(root: tk.Tk, update_status, feature, events: List):
    """Open dialog and start update automation workflow for an existing feature."""
    if not feature or not events:
        messagebox.showwarning("Warning", "No feature selected or no events to update!")
        return

    first_event_url = events[0].url if events and events[0].url else "https://example.com"

    update_window = tk.Toplevel(root)
    update_window.title("Update Feature")
    update_window.geometry("500x350")
    update_window.configure(bg='white')
    update_window.transient(root)
    update_window.grab_set()

    x = root.winfo_x() + (root.winfo_width() // 2) - 250
    y = root.winfo_y() + (root.winfo_height() // 2) - 175
    update_window.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(update_window, bg='white')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    title_label = tk.Label(main_frame, text=f"Update Feature: {feature.feature}", font=('Arial', 16, 'bold'), fg='#2c3e50', bg='white')
    title_label.pack(pady=(0, 20))

    url_label = tk.Label(main_frame, text="Target URL:", font=('Arial', 10, 'bold'), fg='#2c3e50', bg='white')
    url_label.pack(anchor=tk.W, pady=(0, 5))

    url_entry = tk.Entry(main_frame, font=('Arial', 10), width=60, state='readonly')
    url_entry.pack(fill=tk.X, pady=(0, 15))
    url_entry.config(state='normal')
    url_entry.insert(0, first_event_url)
    url_entry.config(state='readonly')

    prompt_label = tk.Label(main_frame, text="Updated Automation Prompt:", font=('Arial', 10, 'bold'), fg='#2c3e50', bg='white')
    prompt_label.pack(anchor=tk.W, pady=(0, 5))

    prompt_text = tk.Text(main_frame, font=('Arial', 10), height=6, width=60, wrap=tk.WORD)
    prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    buttons_frame = tk.Frame(main_frame, bg='white')
    buttons_frame.pack(fill=tk.X, pady=(10, 0))

    def _start_update():
        prompt = prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter an updated prompt!")
            return

        update_window.destroy()
        update_status("Starting update automation workflow...", 'info')

        def _run_update():
            try:
                automation_runner = AutomationRunner()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(
                    automation_runner.run_update_automation_workflow(
                        target_url=first_event_url,
                        prompt=prompt,
                        feature_id=feature.id,
                        feature_name=feature.feature
                    )
                )
                loop.close()
                root.after(0, lambda: _update_completed(update_status, success))
            except Exception as e:
                root.after(0, lambda: _update_error(update_status, str(e)))

        threading.Thread(target=_run_update, daemon=True).start()

    def _cancel():
        update_window.destroy()

    update_button = tk.Button(buttons_frame, text="Update Feature", font=('Arial', 10, 'bold'), bg='#3498db', fg='white', relief=tk.RAISED, bd=2, padx=20, pady=8, command=_start_update)
    update_button.pack(side=tk.LEFT, padx=(0, 10))

    cancel_button = tk.Button(buttons_frame, text="Cancel", font=('Arial', 10, 'bold'), bg='#e74c3c', fg='white', relief=tk.RAISED, bd=2, padx=20, pady=8, command=_cancel)
    cancel_button.pack(side=tk.LEFT)

    prompt_text.focus()


def _events_execution_completed(root: tk.Tk, update_status, success: bool, feature, events: List):
    if success:
        update_status(f"Successfully executed {len(events)} events for '{feature.feature}'", 'success')
        messagebox.showinfo("Success", f"Successfully executed {len(events)} events for '{feature.feature}'!")
    else:
        update_status("Event execution failed", 'error')
        messagebox.showerror("Error", "Some events failed to execute. Check the console for details.")


def _events_execution_error(update_status, error_msg: str):
    update_status("Event execution error", 'error')
    messagebox.showerror("Error", f"Event execution failed: {error_msg}")


def _update_completed(update_status, success: bool):
    if success:
        update_status("Feature update completed successfully!", 'success')
        messagebox.showinfo("Success", "Feature updated successfully!")
    else:
        update_status("Feature update failed", 'error')
        messagebox.showerror("Error", "Feature update failed!")


def _update_error(update_status, error_msg: str):
    update_status("Update error", 'error')
    messagebox.showerror("Error", f"Feature update failed: {error_msg}")


