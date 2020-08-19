"""check.py

Check that moka contains keys for PanelApp panel hashes, versions and HGNC IDs.

This check ensures that Moka has database keys for PanelApp data when imported.
Panel hashes and versions are stored in dbo.Item where new data can simply be inserted.
HGNC IDs are stored in dbo.GenesHGNC_current, which is Moka's internal copy of the HGNC table. This
snapshot is updated manually, therefore an error should be raised if PanelApp HGNC ids mismatch.
"""
import logging
import sys

from mokapapp import db, lib, query

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main(config, panels):
    """ Checks Moka is able to receive PanelApp panel data.

    Args:
        config (dict): Contains moka database server details as in config file
        panels (List[MokaPanel]): Moka panel objects built from PanelApp API response
    """
    # Initialise the MokaPanelChecker object for running database queries
    logger.info('Initialising MokaDB connection')
    mpc = db.MokaPanelChecker(
        server=config['server'],
        db=config['db'],
        user=config['user'],
        password=config['password']
    )

    # Get list of PanelApp hashes (moka-formatted) that are not in dbo.Item
    new_panel_ids = mpc.get_new_items(panels)
    if new_panel_ids:
        logger.info("Inserting new hashes into dbo.Item: {}".format(new_panel_ids))
        mpc.insert_items(new_panel_ids, mpc.PANEL_MOKA_ID_INDEX)
    else:
        logger.info("No new panel hash items to insert from PanelApp")

    # Get list of PanelApp version numbers that are not in dbo.Item
    new_panel_versions = mpc.get_new_versions(panels)
    if new_panel_versions:
        logger.info("Inserting new versions into dbo.Item: {}".format(new_panel_versions))
        mpc.insert_items(new_panel_versions, mpc.PANEL_VERSION_INDEX)
    else:
        logger.info("No new panel version items to insert from PanelApp")

    # Check that all HGNC IDs from PanelApp are present in the Moka GenesHGNCS_current table
    if panels:
        hgnc_set = lib.get_hgnc_set(panels)
        mpc.check_hgncs(hgnc_set)

    logger.info('Moka DB Check complete')


if __name__ == '__main__':
    # Query PanelApp API and build list of MokaPanels
    logger.info('Getting PanelApp panels as MokaPanel objects')
    panels = [lib.MokaPanel.from_dict(panel) for panel in query.main()]
    # Read config file from command-line arguments
    parsed_args = lib.cli(sys.argv[1:])
    config = parsed_args.config['mokadb']
    # Check MokaDB can import PanelApp data
    main(config, panels)
