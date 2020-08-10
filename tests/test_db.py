import pytest
import json
import itertools
from mokapapp.db import MokaDB, MokaPanelChecker, _MokaPanelActivator, MokaPanelUpdater
from mokapapp.lib import MokaPanel
from auth import SV_TE_MOKDBS01
from mocks import mock_json

import logging

log = logging.getLogger('test')
logging.getLogger("urllib3").setLevel(logging.WARNING)

@pytest.fixture()
def mdb():
    return MokaDB(**SV_TE_MOKDBS01)

@pytest.fixture(scope="function")
def activator(mdb):
    return _MokaPanelActivator(mdb.cursor)

@pytest.fixture(scope="module")
def mock_mp():
    data = json.loads(mock_json)[0]
    return MokaPanel(
        data['moka_id'], data['name'], data['version'], data['genes'], data['colour']
    )

@pytest.fixture(scope="module")
def false_mp():
    data = itertools.repeat('FALSE', 5)
    return MokaPanel(*data)

def test_moka_updater(mock_mp):
    """ To test MokaPanelUpdater, we insert the mock panel into Moka and assert all other
    test functions work against this inserted panel."""
    mpu = MokaPanelUpdater(**SV_TE_MOKDBS01)
    assert mpu.in_ngs_panel(mock_mp.moka_id)
    # Check it is not present before running to avoid inserting the panel again.
    #   Note: Record must be absent from Moka prior to running this test. Update mock panel version
    if not mpu.version_in_ngs_panel(mock_mp.moka_id, mock_mp.version):
        mpu.insert_into_moka(mock_mp) # Note: Test is now left active in testdb.
        assert mpu.in_ngs_panel(mock_mp.moka_id) == True
        assert mpu.version_in_ngs_panel(mock_mp.moka_id, mock_mp.version) == True
        assert mpu.is_update(mock_mp.moka_id, '999.999') == True
        assert mpu.is_update(mock_mp.moka_id, '0.0001') == False


class TestMokaDBChecker:
    @pytest.fixture(scope="module")
    def mc(mdb):
        return MokaPanelChecker(**SV_TE_MOKDBS01)
    
    def test_hashes(self, mc, mock_mp, false_mp):
        """Test that old hashes are ignored and new hashes are returned by
        MokaPanelChecker.get_new_hashes"""
        assert mc.get_new_hashes([mock_mp]) == set()
        assert mc.get_new_hashes([false_mp]) == set(['FALSE'])
    
    def test_versions(self, mc, mock_mp, false_mp):
        """Test that old versions are ignored and new versions returned by
        MokaPanelChecker.get_new_versions"""
        assert mc.get_new_versions([mock_mp]) == set()
        assert mc.get_new_versions([false_mp]) == set(['FALSE'])
    
    def test_check_hgncs(self, mc, mock_mp, false_mp):
        """Test that old HGNCs are ignored and new ids returned by
        MokaPanelChecker.check_hgncs"""
        hgnc_list_mock = [ item[0] for item in mock_mp.genes ]
        assert mc.check_hgncs(hgnc_list_mock) == True
        # New HGNC presence should raise an exception
        with pytest.raises(Exception):
            mc.check_hgncs(['FALSE']) == set(['FALSE'])



class TestMokaPanelActivator():
    
    def test_deactivate(self, activator, mock_mp):
        activator._deactivate_all(mock_mp.moka_id)
        status = activator.cursor.execute(
            "SELECT Active from dbo.NGSPanel WHERE Category = ? And Active = 1",
            activator.get_item_id(mock_mp.moka_id)
        ).fetchall()
        assert len(status) == 0

    def test_set_active(self, activator, mock_mp):
        activator._deactivate_all(mock_mp.moka_id)
        activator.set_only_active(mock_mp.moka_id, mock_mp.version)
        category, subcategory = activator.get_item_id(mock_mp.moka_id), activator.get_item_id(mock_mp.version)
        status = activator.cursor.execute(
            "SELECT Active from dbo.NGSPanel WHERE Category = ? AND SubCategory = ? AND Active = 1",
            category,
            subcategory
        ).fetchall()
        log.info(status)
        log.info( ",".join([str(i) for i in (mock_mp.moka_id, mock_mp.version, category, subcategory)]))
        assert len(status) == 1
