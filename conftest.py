"""conftest.py

Settings and fixtures for pytest.
"""
import pytest
import logging

from _jellypy import _panelapp

logging.getLogger("urllib3").setLevel(logging.WARNING)

# Fixtures
@pytest.fixture
def PanelApp():
    return _panelapp.PanelApp
