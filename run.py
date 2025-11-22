"""
Entry Point
"""

import sys
import os

# Add the current directory to Python path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop_ui.main import main

if __name__ == "__main__":
    main()

