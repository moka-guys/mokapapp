"""conftest.py

Configuration for pytest
"""

import configparser
import pytest

def pytest_addoption(parser):
    parser.addoption("--config", action="store", required=True, help="mokapapp config.ini file")

@pytest.fixture
def mokapapp_config(request):
    config = configparser.ConfigParser()
    config.read(request.config.getoption("--config"))
    return config
