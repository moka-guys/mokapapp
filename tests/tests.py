import pytest
import logging

from auth import SV_TE_MOKDBS01
from mokapapp import mplogger, lib, db
from datetime import datetime

def test_mplogger(tmp_path):
    """Assert that the mokapapp logger writes to a given output directory"""
    # mokapapp should log to files with the format "year-month-day_mokapapp.log". e.g. 200818_mokapapp.log
    #   tmp_path is a pytest default fixture that provides a pathlib.Path object to create temporary files and directories 
    logdir = (tmp_path / "logdir")
    logdir.mkdir()
    mplogger.setup(logdir)
    logger = logging.getLogger('test_logger')
    logger.info('LOGFILE TEST')

    expected_logfile = logdir / (datetime.now().strftime("%y%d%m") + "_mokapapp.log")
    assert expected_logfile.exists()
    assert "LOGFILE TEST" in expected_logfile.read_text()

def test_mpfactory():
    """Test that mokapanel factory returns Mokapanel objects from the PanelApp API"""
    endpoints = {
        "panels": "https://panelapp.genomicsengland.co.uk/api/v1/panels",
        "signed_off_panels": "https://panelapp.genomicsengland.co.uk/api/v1/panels/signedoff"
    }
    mpf = lib.MokaPanelFactory(endpoints=endpoints)
    panels = mpf.build(colours=["Green", "Amber"], head=10)
    assert type(panels[0]) == lib.MokaPanel
    # MokaPanels are further divided by gene colour so we expect more MokaPanels than were requested
    #   with the head argument.
    assert len(panels) > 10


class TestMokaChecker():

    @pytest.fixture
    def checker(self, mokapapp_config):
        test_db = mokapapp_config['mokadb_test']
        return db.MokaPanelChecker(**test_db)

    def test_get_new_items(self, checker):
        # Test that get_new_items gets panel new items and ignores existing ones
        panels_in_moka = [lib.MokaPanel('34_Amber',None, None, None, None, None)]
        panels_new_to_moka = [lib.MokaPanel('99999_Amber',None, None, None, None, None)]
        assert checker.get_new_items(panels_in_moka) == set()
        assert checker.get_new_items(panels_new_to_moka) == set(['99999_Amber'])

    def test_get_new_versions(self, checker):
        # Test that get_new_versions gets new panel versions and ignores existing ones
        versions_in_moka = [lib.MokaPanel(None,None, '1.112', None, None, None)]
        versions_new_to_moka = [lib.MokaPanel(None,None, '9.9999', None, None, None)]
        assert checker.get_new_versions(versions_in_moka) == set()
        assert checker.get_new_versions(versions_new_to_moka) == set(['9.9999'])

    def test_check_hgncs(self, checker):
        # Test that check_hgncs raises an error if new hgncs are present
        hgncs_in_moka = set(['HGNC:5'])
        hgncs_missing = set(['HGNC:FAKE'])
        
        # Assert no exception is raised
        assert checker.check_hgncs(hgncs_in_moka)
        # Assert an exception is raised when hgncs missing 
        with pytest.raises(Exception):
            checker.check_hgncs(hgncs_missing)