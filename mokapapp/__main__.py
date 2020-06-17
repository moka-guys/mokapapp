#!/usr/bin/env python3
"""Imports PanelApp panels into Moka.

Raises an error if PanelApp data cannot be inserted due to missing HGNC ids.
"""
import sys
import logging

from mokapapp import mlogger, check, db, lib, query


def main():
    """Queries PanelApp, checks Moka database and imports Moka PanelApp panels.

    Args:
        args (list): A list of command-line arguments. e.g. ['-c', 'config.ini']
    """
    # Read server details from config file
    _args = lib.cli(sys.argv[1:])
    db_config = _args.config['mokadb']

    # Setup logging
    mlogger.log_setup(_args.logfile)
    logger = logging.getLogger('mokapapp')

    # Get a list of MokaPanel objects, each containing a unique PanelApp panel + colour combination
    logger.info('Getting PanelApp panels as MokaPanel objects')
    panels = query.main()
    logger.debug(f'Retrieved {len(panels)} MokaPanels: {[panel.name for panel in panels]}')

    # Check Moka is ready for import:
    #  - Update panels in Item table
    #  - Update panel versions in Item table
    #  - Raise error if panel HGNCID missing from Moka
    check.main(db_config, panels)

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
    mpu.activator.deactivate_deprecated(panels)

    # For each panel,
    for panel in panels:
        # If the panel is new to Moka, import it. New panels have no entry in the NGS Panel table.
        if not mpu.in_ngs_panel(panel.moka_hash):
            logger.info(f'New panel. Inserting into Moka: {panel}')
            mpu.insert_into_moka(panel)
        # Else if the panel is in Moka
        else:
            # Check if the latest panel version is in NGSPanel
            if mpu.version_in_ngs_panel(panel.moka_hash, panel.version):
                # Moka contains the latest panel so no import is required.
                # Ensure this is the only version visible to users by deactivating older versions
                logger.info(f'Panel is present in NGSPanel. Setting only active version: {panel}')
                mpu.activator.set_only_active(panel.moka_hash, panel.version)
            else:
                # This is a new version of a panel in the NGSPanel Table.
                # Insert into Moka, deactivating old panels first
                logger.info(f'Updated panel. Inserting into Moka & Setting Active: {panel}')
                mpu.insert_into_moka(panel, deactivate_old=True)

    logger.info('Moka Panel import complete')


if __name__ == '__main__':
    main(sys.argv[1:])
