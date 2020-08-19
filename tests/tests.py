import pytest
import logging

from mokapapp import mplogger, lib
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


