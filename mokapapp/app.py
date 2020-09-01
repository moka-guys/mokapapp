#!/usr/bin/env python3
"""Import PanelApp panels into Moka.

Function main() accepts command line arguments and triggers the import procedure. This raises an
error if PanelApp data cannot be inserted due to missing HGNC ids.
"""
import argparse
import configparser
import logging
import sys
from typing import List

from mokapapp import mplogger, db, lib


def prepare_moka_database(config: dict, panels: List[lib.MokaPanel], reporter):
    """Assert that Moka has all the data required for importing or updating panels: panel IDs,
    panel versions and HGNC IDs.
    
    PanelApp IDs and panel versions are stored in dbo.Item. This function inserts new items as required.

    HGNC IDs are stored in dbo.GenesHGNC_current, which is Moka's internal HGNC database snapshot.
    This snapshot is updated manually, therefore an error is raised if any PanelApp HGNC ids are absent.

    Args:
        config (dict): Moka database server details as structured in config file
        panels (List[lib.MokaPanel]): MokaPanel objects generated from PanelApp API
        reporter (lib.LogReporter): Initialised logger for end-of-logfile summary stats
    """
    
    logger = logging.getLogger('mokapapp.prepare_moka_database')

    # Initialise the MokaPanelChecker object for running database queries
    logger.info('Initialising MokaDB connection for MokaPanelChecker')
    panel_checker = db.MokaPanelChecker(
        server=config['server'],
        db=config['db'],
        user=config['user'],
        password=config['password']
    )

    # Get list of PanelApp ids missing from dbo.Item.
    new_panel_ids = panel_checker.get_new_items(panels)

    # Insert new PanelIDs into dbo.Item if required
    if new_panel_ids:
        logger.info("Inserting new panel IDs into dbo.Item: {}".format(new_panel_ids))
        panel_checker.insert_items(new_panel_ids, panel_checker.PANEL_MOKA_ID_INDEX)
    else:
        logger.info("No new panel IDs items to insert from PanelApp")

    # Insert new version numbers into dbo.Item if required
    new_panel_versions = panel_checker.get_new_versions(panels)
    if new_panel_versions:
        logger.info("Inserting new versions into dbo.Item: {}".format(new_panel_versions))
        panel_checker.insert_items(new_panel_versions, panel_checker.PANEL_VERSION_INDEX)
    else:
        logger.info("No new panel version items to insert from PanelApp")

    # Check that all HGNC IDs from PanelApp are present in the Moka GenesHGNCS_current table
    hgnc_set = set()
    for panel in panels:
        # Panel.genes is a list of tuples containing hgnc-symbol pairs.
        #   Use zip to separate into two lists of hgncs and symbols, then update the set.
        hgncs, symbols = zip(*panel.genes)
        hgnc_set.update(hgncs)
    panel_checker.check_hgncs(hgnc_set)

    # Write to logfile end report
    reporter.add('New panel ids in panelapp', len(new_panel_ids))
    reporter.add('New panel versions in panelapp', len(new_panel_versions))
    logger.info('Moka DB Check complete')

def main():
    """Update PanelApp Panels in the Moka database.
    
    1. Queries PanelApp and converts response into MokaPanel objects for import
    2. Checks Moka database has all keys required to recieve import data
    3. Deactivates all existing Panels that are no longer in the API response
    3. Imports MokaPanel object data into Moka.

    Args:
        args (list): A list of command-line arguments. e.g. ['-c', 'config.ini']
    """
    # Read Config from config file
    parser = argparse.ArgumentParser()
    config = configparser.ConfigParser()
    parser.add_argument('-c', '--config',
        help="A mokapapp config.ini file. See README at https://www.github.com/moka-guys/mokapapp",
        required=True)
    args = parser.parse_args()
    # Set log directory, Moka database, PanelApp endpoints and minimum panel count from config file
    logdir = config['mokapapp']['logdir']
    db_config = config[config['mokapapp']['db']]
    endpoints = config['endpoints']
    min_panel_count = int(config['mokapapp'].get("min_panel_count", 500))

    # Setup loggers
    mplogger.setup(logdir)
    logger = logging.getLogger('mokapapp')
    reporter = lib.LogReporter() # Initialise object to report stats at the end of logfile

    # Get a list of MokaPanel objects. Each object is a unique PanelApp panel + gene colour combination
    logger.info('Getting PanelApp panels as MokaPanel objects')
    panel_factory = lib.MokaPanelFactory(endpoints=endpoints)
    panels = panel_factory.build(colours=["Green", "Amber"], reporter=reporter)
    logger.debug(f'Retrieved {len(panels)} MokaPanels: {[panel.name for panel in panels]}')

    assert panels, 'ERROR: No Moka panel app panels returned from parsing API response'
    assert len(panels) > min_panel_count, f'ERROR: The minimum number of expected panels ({min_panel_count}) was not exceeded'

    # Check Moka is ready for import:
    #  - Update panels in Item table
    #  - Update panel versions in Item table
    #  - Raise error if panel HGNCID missing from Moka
    prepare_moka_database(db_config, panels, reporter)

    # Initialise database object for updating panels
    logger.info('Initialising MokaDB connection')
    mpu = db.MokaPanelUpdater(
        server=db_config['server'],
        db=db_config['db'],
        user=db_config['user'],
        password=db_config['password']
    )

    # Deprecated panels are absent from PanelApp. Deactivate these panels in Moka.
    logger.info('Deactivating all Moka Panels missing from PanelApp API')
    mpu.activator.deactivate_deprecated(panels, reporter)

    # For each panel,
    for panel in panels:
        # If the panel is new to Moka, import it. New panels have no entry in the NGS Panel table.
        if not mpu.in_ngs_panel(panel.moka_id):
            logger.info(f'New panel. Inserting into Moka: {panel}')
            mpu.insert_into_moka(panel)
            reporter.add('Panels inserted into Moka', 1)
        # Else if the panel is in Moka
        else:
            # If the most recent panel version is already in NGSPanel
            if mpu.version_in_ngs_panel(panel.moka_id, panel.version):
                # No import is required. Ensure this is the only version visible to users by deactivating older versions
                logger.info(f'Panel is present in NGSPanel. Setting only active version: {panel}')
                mpu.activator.set_only_active(panel.moka_id, panel.version)
                reporter.add('Panels unchanged in Moka', 1)
            else:
                # This is a new version of a panel in the NGSPanel Table.
                # Insert into Moka, deactivating old panels first
                logger.info(f'Updated panel. Inserting into Moka & Setting Active: {panel}')
                mpu.insert_into_moka(panel, deactivate_old=True)
                reporter.add('Panels updated in Moka', 1)

    # Log statistics to end of logfile and complete
    reporter.report_to_log()
    logger.info('Moka Panel import complete')


if __name__ == '__main__':
    main()
