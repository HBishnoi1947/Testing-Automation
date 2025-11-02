"""
Features page workflows extracted from the main UI.
"""

import threading
import asyncio
import tkinter as tk
from tkinter import messagebox

from run import AutomationRunner


def open_create_feature_dialog(root: tk.Tk, update_status, on_refresh):
    """Open dialog to create a new feature and start automation workflow."""
    input_window = tk.Toplevel(root)
    input_window.title("Create New Feature")
    input_window.geometry("500x400")
    input_window.configure(bg='white')
    input_window.transient(root)
    input_window.grab_set()

    x = root.winfo_x() + (root.winfo_width() // 2) - 250
    y = root.winfo_y() + (root.winfo_height() // 2) - 200
    input_window.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(input_window, bg='white')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    title_label = tk.Label(main_frame, text="Create New Feature", font=('Arial', 16, 'bold'), fg='#2c3e50', bg='white')
    title_label.pack(pady=(0, 20))

    url_label = tk.Label(main_frame, text="Target URL:", font=('Arial', 10, 'bold'), fg='#2c3e50', bg='white')
    url_label.pack(anchor=tk.W, pady=(0, 5))

    url_entry = tk.Entry(main_frame, font=('Arial', 10), width=60)
    url_entry.pack(fill=tk.X, pady=(0, 15))

    prompt_label = tk.Label(main_frame, text="Automation Prompt:", font=('Arial', 10, 'bold'), fg='#2c3e50', bg='white')
    prompt_label.pack(anchor=tk.W, pady=(0, 5))

    prompt_text = tk.Text(main_frame, font=('Arial', 10), height=6, width=60, wrap=tk.WORD)
    prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    buttons_frame = tk.Frame(main_frame, bg='white')
    buttons_frame.pack(fill=tk.X, pady=(10, 0))

    def _start_automation():
        url = url_entry.get().strip()
        prompt = prompt_text.get("1.0", tk.END).strip()
        if not url or not prompt:
            messagebox.showerror("Error", "Please enter both URL and prompt!")
            return

        input_window.destroy()
        update_status("Starting automation workflow...", 'info')

        def _run_automation():
            try:
                automation_runner = AutomationRunner()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    automation_runner.run_automation_workflow(url, prompt)
                )
                loop.close()
                
                # Capture result before callback
                workflow_result = result
                
                def _complete():
                    if workflow_result.get('success'):
                        validation = workflow_result.get('validation', {})
        
                        reason = validation.get('reason', 'No details')
                        
                        update_status(f"✅ Feature '{workflow_result['feature_name']}' created and validated!", 'success')
                        
                        messagebox.showinfo(
                            "✅ Validation Successful",
                            f"Feature: {workflow_result['feature_name']}\n\n"
                      
                            f"Result: {reason}"
                        )
                    else:
                        validation = workflow_result.get('validation', {})
                        reason = validation.get('reason', workflow_result.get('error', 'Unknown error'))
                        suggestions = validation.get('suggestions', 'No suggestions available')
                        
                        update_status(f"❌ Validation failed", 'error')
                        
                        messagebox.showerror(
                            "❌ Validation Failed",
                            f"Feature creation completed but validation failed.\n\n"
                            f"Reason: {reason}\n\n"
                            f"Suggestions: {suggestions}"
                        )
                    
                    if on_refresh:
                        on_refresh()
                
                root.after(0, _complete)
                
            except Exception as e:
                error_msg = str(e)
                
                def _show_error():
                    update_status(f"❌ Error: {error_msg}", 'error')
                    messagebox.showerror("Error", f"Automation failed:\n\n{error_msg}")
                
                root.after(0, _show_error)



        threading.Thread(target=_run_automation, daemon=True).start()

    def _cancel():
        input_window.destroy()

    start_button = tk.Button(buttons_frame, text="Start Automation", font=('Arial', 10, 'bold'), bg='#27ae60', fg='white', relief=tk.RAISED, bd=2, padx=20, pady=8, command=_start_automation)
    start_button.pack(side=tk.LEFT, padx=(0, 10))

    cancel_button = tk.Button(buttons_frame, text="Cancel", font=('Arial', 10, 'bold'), bg='#e74c3c', fg='white', relief=tk.RAISED, bd=2, padx=20, pady=8, command=_cancel)
    cancel_button.pack(side=tk.LEFT)

    url_entry.focus()


def _automation_error(update_status, error_msg: str):
    update_status("Automation error", 'error')
    messagebox.showerror("Error", f"Automation failed: {error_msg}")


