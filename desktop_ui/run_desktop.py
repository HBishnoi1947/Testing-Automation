#!/usr/bin/env python3
"""
Launcher script for the Desktop UI application.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from desktop_ui.main import main
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting desktop UI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
