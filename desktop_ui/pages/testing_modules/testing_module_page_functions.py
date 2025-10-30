"""
Testing Module page workflows extracted from the main UI.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from model.database import get_events_by_feature_id
from execute import execute_events


def run_testing_module(root: tk.Tk, update_status, features_page, module, flow):
    """Convert flow items to events and execute them in a background thread."""
    if not module or not flow:
        messagebox.showwarning("Warning", "No module selected or no flow items to run!")
        return

    result = messagebox.askyesno(
        "Confirm Execution",
        f"Are you sure you want to run the testing module '{module['testing_module']}'?\n\nThis will execute {len(flow)} flow items."
    )
    if not result:
        return

    update_status(f"Running testing module '{module['testing_module']}'...", 'info')

    def _worker():
        try:
            events_to_run = []
            for item in flow:
                if item['type'] == 'event' and item['event_id']:
                    for feature in features_page.get_all_features():
                        feature_events = get_events_by_feature_id(feature.id)
                        for event in feature_events:
                            if event.id == item['event_id']:
                                events_to_run.append(event)
                                break
            if events_to_run:
                success = execute_events(events_to_run, headless=False)
                root.after(0, lambda: _module_execution_completed(update_status, success, module))
            else:
                root.after(0, lambda: _module_execution_error(update_status, "No executable events found in flow"))
        except Exception as e:
            root.after(0, lambda: _module_execution_error(update_status, str(e)))

    threading.Thread(target=_worker, daemon=True).start()


def _module_execution_completed(update_status, success: bool, module):
    if success:
        update_status(f"Successfully executed testing module '{module['testing_module']}'", 'success')
        messagebox.showinfo("Success", f"Successfully executed testing module '{module['testing_module']}'!")
    else:
        update_status("Module execution failed", 'error')
        messagebox.showerror("Error", "Module execution failed. Check the console for details.")


def _module_execution_error(update_status, error_msg: str):
    update_status("Module execution error", 'error')
    messagebox.showerror("Error", f"Module execution failed: {error_msg}")


