import pytest
import logging
import configparser
import sys

from mokapapp import mplogger, lib, db, app
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

    expected_logfile = logdir / (datetime.now().strftime("%y%m%d") + "_mokapapp.log")
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

class TestDB():
    
    @pytest.fixture(scope="class")
    def moka_panel(self, mokapapp_config):
        """A mock moka panel to use for database tests"""
        # Yield moka panel
        mp = lib.MokaPanel(
                '999_test','Test Moka Panel (PanelApp Green v9.99)', '9.99',
                [('HGNC:5', 'TEST_GENE')],'Green',False
        )
        app.prepare_moka_database(mokapapp_config['mokadb_test'], [mp], reporter=self.get_fake_reporter())

        yield mp
        
        # All code after yield is teardown. Ensure all mock moka panel objects are cleared from the database
        #   Don't forget the NGSPanelGenes table!
        mdb = db.MokaDB(**mokapapp_config['mokadb_test'])
        mdb.cursor.execute('DELETE FROM Item where Item = ?', mp.moka_id)
        mdb.cursor.execute('DELETE FROM Item where Item = ?', mp.version)
        mdb.cursor.execute('DELETE FROM NGSPanel where Panel = ?', mp.name)
        mdb.cursor.execute('DELETE FROM NGSPanelGenes where Symbol = ?', mp.genes[0][1])
        mdb.cursor.commit()

    @pytest.fixture(scope="class")
    def updater(self, moka_panel, mokapapp_config):
        """A MokaPanelUpdater object connected ot the test database"""
        updater = db.MokaPanelUpdater(**mokapapp_config['mokadb_test'])
        if not updater.in_ngs_panel(moka_panel.moka_id):
            updater.insert_into_moka(moka_panel)
        return updater

    @pytest.fixture
    def activator(self, mokapapp_config):
        """A MokaPanelActivator object connected to the moka_test database"""
        test_db = mokapapp_config['mokadb_test']
        moka_db =  db.MokaDB(**test_db)
        return db._MokaPanelActivator(moka_db.cursor)

    def get_fake_reporter(self):
        class FakeReporter:
            def __init__(self):
                pass

            def add(self, stat_name, stat):
                pass

            def report_to_log(self):
                pass

        return FakeReporter()

    def test_insert_and_in(self, moka_panel, updater):
        """Test that MokaPanelUpdater.insert_into_moka inserts the Moka panel.
        Test that MokaPanelUpdater.in_ngs_panel returns true for moka IDs present and false for absent ids"""
        # Insert used with the updater fixture. Test here that panel is present
        assert updater.in_ngs_panel(moka_panel.moka_id)
        assert not updater.in_ngs_panel('FAKE_MOKA_ID')

    def test_version_in_ngs_panel(self, moka_panel, updater):
        """Test MokaPanelUpdater.version_in_ngs_panel returns True for moka id, version pairs present in NGSPanel"""
        assert updater.version_in_ngs_panel(moka_panel.moka_id, moka_panel.version)
        assert not updater.version_in_ngs_panel(moka_panel.moka_id, 'FAKE_MOKA_VERSION')

    def test_set_only_active(self, moka_panel, activator, updater):
        """Test MokaPanelActivator.set_only_active sets the panel version as the only active version of that panel""" 
        activator.set_only_active(moka_panel.moka_id, moka_panel.version)
        active_status = activator.cursor.execute("SELECT ACTIVE from dbo.NGSPanel WHERE Panel = ?", moka_panel.name).fetchall()
        assert len(active_status) == 1

    def test_insert_into_moka_deactivate(self, moka_panel, activator, updater):
        """Test MokaPanelUpdater.insert_into_moka with deactivate_old=True deactivates old versions of a MokaPanel"""
        # Select an existing panel version, assumed to be less than version 9.99
        old_version = updater.cursor.execute("SELECT Item from dbo.Item WHERE ItemCategoryIndex1ID = 61").fetchone()[0]
        # Insert new panel with this version into Moka
        _new_panel = list(moka_panel)
        _new_panel[2] = old_version
        updater.insert_into_moka(lib.MokaPanel(*_new_panel))

        updater.insert_into_moka(moka_panel, deactivate_old=True)
        version_id = updater.cursor.execute("SELECT Item from dbo.NGSPanel LEFT JOIN Item on dbo.NGSPanel.SubCategory = Item.ItemID WHERE Panel = ? AND Active = 1", moka_panel.name).fetchval()
        assert version_id == moka_panel.version

def test_app(tmp_path, monkeypatch, mokapapp_config):
    """Test that mokapapp is able to update the test database sufficiently.

    This is equivalent to running:
    > mokapapp --config config.ini --db mokadb_test
    """

    class FakeConfigParser():
        def __init__(self):
            self.config = mokapapp_config
            self.log_to_tempdir()
        def read(self, argument):
            pass
        def __getitem__(self, item):
            return self.config[item]
        def log_to_tempdir(self):
            logdir = (tmp_path / "logdir")
            logdir.mkdir()
            self.config['mokapapp']['logdir'] = str(logdir)

    monkeypatch.setattr(configparser, 'ConfigParser', FakeConfigParser)
    
    sys.argv = ['mokapapp', '--config','using_pytest_config_instead']

    app.main()