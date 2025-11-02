"""
Testing Module page workflows extracted from the main UI.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from model.database import get_events_by_feature_id
from execute import execute_events


def run_testing_module(root: tk.Tk, update_status, features_page, module, flow, on_complete=None):
    """
    Execute all features in a testing module and generate report.
    
    Args:
        root: Tkinter root
        update_status: Status update callback
        features_page: Reference to features page (if needed)
        module: TestingModule object or dict
        flow: Module flow data
        on_complete: Callback after completion
    """
    import threading
    from tkinter import messagebox
    from execute import execute_events
    from model.database import get_events_by_feature_id, save_module_execution_report
    from datetime import datetime
    
    if not module:
        messagebox.showwarning("Warning", "No module selected!")
        return
    
    # Handle module as either dict or object
    if isinstance(module, dict):
        module_name = module.get('testing_module', 'Unknown Module')
        module_id = module.get('id', 0)
    else:
        module_name = module.testing_module
        module_id = module.id
    
    result = messagebox.askyesno(
        "Confirm Execution",
        f"Run module '{module_name}'?\n\nThis will execute all features in the module flow and generate a report."
    )
    
    if not result:
        return
    
    update_status(f"Executing module: {module_name}...", 'info')
    
    def _worker():
        try:
            # Handle flow as either list or dict
            if isinstance(flow, list):
                features = flow
            elif isinstance(flow, dict):
                features = flow.get('features', [])
            else:
                features = []
            
            if not features:
                error_msg = "No features found in module flow"
                root.after(0, lambda: _show_error(error_msg))
                return
            
            # ✅ STEP 1: Prepare ALL features with their events FIRST
            features_with_events = []
            
            for idx, feature in enumerate(features, 1):
                # Handle feature as dict or object
                if isinstance(feature, dict):
                    feature_name = (feature.get('feature') or 
                                feature.get('name') or 
                                feature.get('feature_name') or 
                                'Unknown')
                    feature_id = (feature.get('id') or 
                                feature.get('feature_id') or 
                                0)
                else:
                    feature_name = getattr(feature, 'feature', getattr(feature, 'name', 'Unknown'))
                    feature_id = getattr(feature, 'id', getattr(feature, 'feature_id', 0))
                
                print(f"[Preparing] Feature {idx}: {feature_name} (ID: {feature_id})")
                
                # Get events for feature
                events = get_events_by_feature_id(feature_id)
                
                if not events:
                    print(f"  ⚠️ No events found for feature: {feature_name}")
                else:
                    print(f"  ✓ Found {len(events)} events")
                
                # Add to list (even if no events, so it shows as failed)
                features_with_events.append({
                    'feature_name': feature_name,
                    'feature_id': feature_id,
                    'events': events
                })
            
            print(f"\n{'='*80}")
            print(f"🚀 EXECUTING MODULE: {module_name}")
            print(f"{'='*80}")
            print(f"Total Features: {len(features_with_events)}")
            print(f"Execution Mode: ✅ Single browser session (all features)")
            print(f"{'='*80}\n")
            
            # ✅ STEP 2: Execute ALL features in ONE browser session
            from execute import EventExecutor
            executor = EventExecutor()
            module_execution_result = executor.execute_module_features(features_with_events, headless=False)
            
            # ✅ STEP 3: Build final results from module execution
            module_results = {
                'module_name': module_name,
                'execution_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_features': module_execution_result['total_features'],
                'passed_features': module_execution_result['passed_features'],
                'failed_features': module_execution_result['failed_features'],
                'feature_results': module_execution_result['feature_results']
            }
            
            # Save report to database
            report_id = save_module_execution_report(module_id, module_results)
            
            print(f"\n{'='*80}")
            print(f"📊 MODULE EXECUTION COMPLETED")
            print(f"{'='*80}")
            print(f"Total Features: {module_results['total_features']}")
            print(f"Passed: {module_results['passed_features']}")
            print(f"Failed: {module_results['failed_features']}")
            print(f"Report ID: {report_id}")
            print(f"{'='*80}\n")
            
            # Capture results before callback
            final_results = module_results
            
            def _show_report():
                # Generate PDF report
                from pdf_report_generator import generate_test_execution_pdf
                import os
                import platform
                
                try:
                    pdf_path = generate_test_execution_pdf(final_results)
                    update_status(f"✅ Report generated: {pdf_path}", 'success')
                    
                    result = messagebox.askyesno(
                        "Report Generated",
                        f"Test execution report generated successfully!\n\n"
                        f"Location: {pdf_path}\n\n"
                        f"Would you like to open the report now?"
                    )
                    
                    if result:
                        if platform.system() == 'Windows':
                            os.startfile(pdf_path)
                        elif platform.system() == 'Darwin':
                            os.system(f'open "{pdf_path}"')
                        else:
                            os.system(f'xdg-open "{pdf_path}"')
                    
                except Exception as e:
                    error_msg = f"Failed to generate PDF: {str(e)}"
                    update_status(error_msg, 'error')
                    messagebox.showerror("PDF Generation Error", error_msg)
                
                if on_complete:
                    on_complete()
            
            root.after(0, _show_report)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            root.after(0, lambda: _show_error(error_msg))

    
    def _show_error(error_msg):
        update_status(f"❌ Error: {error_msg}", 'error')
        messagebox.showerror("Execution Error", f"Failed to execute module:\n\n{error_msg}")
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()



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




