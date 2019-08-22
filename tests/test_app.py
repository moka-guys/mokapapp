import pytest
import logging
import json
from mokapapp.lib import cli, MokaPanel
from mokapapp import check, query
from mocks import mock_json

logger = logging.getLogger()

@pytest.fixture
def mock_mp():
    data = json.loads(mock_json)[0]
    return MokaPanel(
        data['id'], data['name'], data['version'], data['genes'], data['colour']
    )

def test_query_json():
    """Test that mokapapp.query.main returns a list of MokaPanel objects"""
    # Prints MokaPanels as json objects
    data = query.main(head=5)
    # Test that data can be read
    assert isinstance(data, list)
    assert isinstance(data[0], MokaPanel)

def test_check(mock_mp):
    # Prints MokaPanels as json objects
    panels = query.main(head=5)
    parsed_args = cli(['-c','config.ini'])
    config = parsed_args.config['mokadb']
    check.main(config, panels)