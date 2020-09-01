#!/usr/bin/env python3
"""Import PanelApp panels into Moka.

Raises an error if PanelApp data cannot be inserted due to missing HGNC ids.
"""
import sys
import configparser
import logging

from mokapapp import mplogger, db, lib

from typing import List

def prepare_moka_database(config: dict, panels: List[lib.MokaPanel], reporter):
    """
    Check that moka contains keys for PanelApp panel hashes, versions and HGNC IDs.

    This check ensures that Moka has database keys for PanelApp data when imported. Panel ids and versions are stored in dbo.Item where new data can simply be inserted.

    HGNC IDs are stored in dbo.GenesHGNC_current, which is Moka's internal copy of the HGNC table. This
    snapshot is updated manually, therefore an error should be raised if PanelApp HGNC ids mismatch.

    Args:
        config (dict): Contains moka database server details as in config file
        panels (List[MokaPanel]): Moka panel objects built from PanelApp API response
        reporter (Lib.LogReporter): An object to send statistics for the end of logfile report
    """
    
    # Initialise the MokaPanelChecker object for running database queries
    logger = logging.getLogger('mokapapp.prepare_moka_database')
    logger.info('Initialising MokaDB connection')
    panel_checker = db.MokaPanelChecker(
        server=config['server'],
        db=config['db'],
        user=config['user'],
        password=config['password']
    )

    # Get list of PanelApp hashes (moka-formatted) that are not in dbo.Item
    new_panel_ids = panel_checker.get_new_items(panels)
    if new_panel_ids:
        logger.info("Inserting new hashes into dbo.Item: {}".format(new_panel_ids))
        panel_checker.insert_items(new_panel_ids, panel_checker.PANEL_MOKA_ID_INDEX)
    else:
        logger.info("No new panel hash items to insert from PanelApp")

    # Get list of PanelApp version numbers that are not in dbo.Item
    new_panel_versions = panel_checker.get_new_versions(panels)
    if new_panel_versions:
        logger.info("Inserting new versions into dbo.Item: {}".format(new_panel_versions))
        panel_checker.insert_items(new_panel_versions, panel_checker.PANEL_VERSION_INDEX)
    else:
        logger.info("No new panel version items to insert from PanelApp")

    # Check that all HGNC IDs from PanelApp are present in the Moka GenesHGNCS_current table
    if panels:
        hgnc_set = set()
        for panel in panels:
            # Panel.genes is a list of tuples containing hgnc-symbol pairs.
            #   Use zip to separate into two lists of hgncs and symbols, then update the set.
            hgncs, symbols = zip(*panel.genes)
            hgnc_set.update(hgncs)
        panel_checker.check_hgncs(hgnc_set)

    # Write to logfile end report
    if reporter:
        reporter.add('New panel ids in panelapp', len(new_panel_ids))
        reporter.add('New panel versions in panelapp', len(new_panel_versions))
    logger.info('Moka DB Check complete')

def main():
    """Queries PanelApp, checks Moka database and imports Moka PanelApp panels.

    Args:
        args (list): A list of command-line arguments. e.g. ['-c', 'config.ini']
    """
    # Read server details from config file. Default is mokadb_prod
    args = lib.cli(sys.argv[1:])
    config = configparser.ConfigParser()
    config.read(args.config)
    db_config = config[args.db]
    endpoints = config['endpoints']

    # Setup logging
    mplogger.setup(args.logdir)
    logger = logging.getLogger('mokapapp')
    # Initialise object to report stats at the end of logfile
    reporter = lib.LogReporter()

    # Get a list of MokaPanel objects, each containing a unique PanelApp panel + colour combination
    logger.info('Getting PanelApp panels as MokaPanel objects')
    panel_factory = lib.MokaPanelFactory(endpoints=endpoints)
    panels = panel_factory.build(colours=["Green", "Amber"], reporter=reporter)
    logger.debug(f'Retrieved {len(panels)} MokaPanels: {[panel.name for panel in panels]}')

    # Check Moka is ready for import:
    #  - Update panels in Item table
    #  - Update panel versions in Item table
    #  - Raise error if panel HGNCID missing from Moka
    prepare_moka_database(db_config, panels, reporter)

    # Initialise Moka database object for updating panels
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
            # Check if the latest panel version is in NGSPanel
            if mpu.version_in_ngs_panel(panel.moka_id, panel.version):
                # Moka contains the latest panel so no import is required.
                # Ensure this is the only version visible to users by deactivating older versions
                logger.info(f'Panel is present in NGSPanel. Setting only active version: {panel}')
                mpu.activator.set_only_active(panel.moka_id, panel.version)
                reporter.add('Panels unchanged in Moka', 1)
            else:
                # This is a new version of a panel in the NGSPanel Table.
                # Insert into Moka, deactivating old panels first
                logger.info(f'Updated panel. Inserting into Moka & Setting Active: {panel}')
                mpu.insert_into_moka(panel, deactivate_old=True)
                reporter.add('Panels updated in Moka', 1)

    reporter.report_to_log()
    logger.info('Moka Panel import complete')


if __name__ == '__main__':
    main(sys.argv[1:])
