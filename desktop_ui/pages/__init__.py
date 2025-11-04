"""
Pages package for the desktop UI application.
Contains separate page folders with their respective components.
"""

from .features_events import FeaturesPage, EventsPage
from .testing_modules import TestingModulePage

__all__ = ['FeaturesPage', 'EventsPage', 'TestingModulePage']
