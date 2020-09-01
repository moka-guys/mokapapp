"""db.py

Classes for connecting to the Moka database
"""
import logging
import textwrap
from pkg_resources import parse_version

import pyodbc


class MokaDB():
    """A Moka database instance. Contains methods for getting and inserting into Moka tables.

    Args:
        server (str): Moka database server IP address e.g. '10.10.10.10'
        db (str): Moka database name
        user (str): Moka database user
        password (str): User password
        driver (str): Moka database driver. Default is 'ODBC Driver 13 for SQL Server'.
    """

    # Set class variables for panel item and version index values
    PANEL_MOKA_ID_INDEX = 48
    PANEL_VERSION_INDEX = 61
    # Moka User ID for automated scripts
    MOKAUSER = "1201865448"

    def __init__(
        self, server=None, db=None, user=None, password=None,
        driver='ODBC Driver 13 for SQL Server'
    ):
        self.logger = logging.getLogger(__name__ + 'MokaDB')
        # Create pyodbc connection and set databse cursor
        self.cnxn = pyodbc.connect(
            f'DRIVER={{{driver}}};SERVER={server};DATABASE={db};'
            f'UID={user};PWD={password}'
        )
        self.cursor = self.cnxn.cursor()

    def get_item_set(self, index1_id):
        """Get a set of items from dbo.Item with a given index"""
        item_cursor = self.cursor.execute(
            'select ItemID, Item from dbo.Item where ItemCategoryIndex1ID = ?',
            index1_id
        )
        return set((row.Item for row in item_cursor))

    def insert_items(self, item_list, index1_id):
        """Insert a list of items into dbo.Item"""
        self.logger.debug(f'Inserting {item_list} into {index1_id}')
        for item in item_list:
            self.cursor.execute(
                "INSERT into dbo.Item (Item, ItemCategoryIndex1ID) values (?, ?)",
                item,
                index1_id
            )
            self.cursor.commit()

    def get_panel_id(self, panel_item, version):
        """Return the PanelId for a given panel and version"""
        return self.cursor.execute(
            "Select NGSPanelID from dbo.NGSPanel where Category = ? AND SubCategory = ?",
            panel_item,
            version
        ).fetchval()

    def get_item_id(self, item):
        """ Get the ID for an Item from dbo.Item
        """
        # COLLATE Latin1_General_CS_AS makes SQL string comparisons case-sensitive. This is required
        # to get the accurate itemID from dbo.Item.Item, which contains entries like:
        #   245_Amber -- (correct)
        #   245_amber -- (legacy, no longer used)
        return self.cursor.execute(
            "Select ItemID from dbo.Item where Item = ? COLLATE Latin1_General_CS_AS",
            item
        ).fetchval()

    def _get_last_key(self):
        """Returns the Primary Key of the last item inserted into Moka by self.cursor."""
        key = self.cursor.execute("SELECT @@IDENTITY").fetchval()
        if key:
            return key
        else:
            raise ValueError('Last key (insert query) failed.')


class _MokaPanelActivator(MokaDB):
    """Private utilities for activating and deactivating Moka Panels.

    Args:
        cursor (pyodbc.connect().cursor): A cursor object intialised for the moka database.
    """

    def __init__(self, cursor):
        self.cursor = cursor
        self.logger = logging.getLogger(__name__ + '._MokaPanelActivator')

    def set_only_active(self, panel_item, panel_version):
        """For a given panel item, set the given version as the only active version in dbo.NGSPanel

        Args:
            panel_item: Moka-format PanelApp panel item e.g. 345_Amber
            panel_version: PanelApp panel version e.g. 1.2
        """
        self._deactivate_all(panel_item)
        self.cursor.execute(
            "UPDATE dbo.NGSPanel SET Active = 1 WHERE Category = ? AND SubCategory = ?",
            self._get_item_id(panel_item),
            self._get_item_id(panel_version)
        )
        self.cursor.commit()
        self.logger.debug(f'Set only active version: {panel_item}, {panel_version}')

    def deactivate_deprecated(self, panels, reporter=None):
        """Deactivate all panels in Moka that are deprecated in PanelApp.

        panels (List[MokaPanel]): MokaPanel objects built from the PanelApp API response.
            Deprecated panels are those that are active in Moka and absent from this list.
        """
        # Create a set of all Moka panel items active in panel app
        active_in_panelapp_ids = {panel.moka_id for panel in panels}
        # Select all PanelApp panel items in Moka (that are active)
        moka_ids = self._list_moka_ids()
        depreciated_panels = [ 
            panel_moka_id for panel_moka_id in moka_ids 
            if panel_moka_id not in active_in_panelapp_ids
        ]
        for panel_moka_id in depreciated_panels:
            self.logger.debug(f"{panel_moka_id} deprecated in PanelApp.")
            self._deactivate_all(panel_moka_id)
        
        if reporter:
            reporter.add('Depreciated panels deactivated in Moka', len(depreciated_panels))
        
    def _deactivate_all(self, panel_item):
        """Deactivate all matching panel items in dbo.NGSPanel
        Args:
            panel_item(str): Moka-format PanelApp panel item e.g. 345_Amber
        """
        # PanelType 2 = PanelApp panels endpoint
        # PanelType 3 = PanelApp signed-off panels endpoint 
        self.cursor.execute(
            "UPDATE dbo.NGSPanel SET Active = 0 WHERE Category = ?  AND PanelType IN (2,3)",
            self._get_item_id(panel_item)
        )
        self.cursor.commit()
        self.logger.debug(f'Panels matching {panel_item} deactivated in NGSPanel')

    def _get_item_id(self, item):
        """Get the ID for a dbo.Item.Item entry."""
        # Note: Panels exist in dbo.Item.Item with upper and lower-case colour names.
        # "COLLATE Latin1_General_CS_AS" makes SQL string comparisons case-sensitive. Required to
        # return the correct ID and avoid matching legacy panel items e.g.:
        #   345_Amber (correct)
        #   345_amber (legacy)
        return self.cursor.execute(
            "Select ItemID from dbo.Item where Item = ? COLLATE Latin1_General_CS_AS", item
        ).fetchval()

    def _list_moka_ids(self):
        """Get all dbo.Item.Item entries for Active PanelApp Panels in Moka"""
        # PanelType 2 = PanelApp panels endpoint
        # PanelType 3 = PanelApp signed-off panels endpoint 
        rows = self.cursor.execute(
            textwrap.dedent(
                """SELECT Item from dbo.Item as db
                     JOIN dbo.NGSPanel as np
                       ON db.ItemID = np.Category
                    WHERE db.ItemCategoryIndex1ID = ?
                      AND np.PanelType in (2,3)
                      AND np.Active = 1
                """
            ), self.PANEL_MOKA_ID_INDEX
        ).fetchall()
        return (row.Item for row in rows)


class MokaPanelUpdater(MokaDB):
    """Updates PanelApp data in the Moka database.
        Inherits all agruments from class MokaDB.
    Args:
        server (str): Moka database server IP address e.g. '10.10.10.10'
        db (str): Moka database name
        user (str): Moka database user
        password (str): User password
        driver (str): Moka database driver
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + '.MokaPanelUpdater')
        self.activator = _MokaPanelActivator(self.cursor)

    def in_ngs_panel(self, panel_item):
        """Returns True if a panel item is present in dbo.NGSPanel.

        Panel items are stored in dbo.Item and their IDs are present in dbo.NGSPanel.Category.
        Args:
            panel_item(str): Moka-format PanelApp panel item e.g. 345_Amber
        """
        # Note: Panels exist in dbo.Item.Item with upper and lower-case colour names.
        # "COLLATE Latin1_General_CS_AS" makes SQL string comparisons case-sensitive. Required to
        # return the correct ID and avoid matching legacy panel items e.g.:
        #   345_Amber (correct)
        #   345_amber (legacy)
        sql = textwrap.dedent("""
            SELECT Category FROM dbo.NGSPanel as n
              LEFT JOIN dbo.Item as i
                ON n.Category = i.ItemID
             WHERE i.Item = ? COLLATE Latin1_General_CS_AS
        """)
        id_present = self.cursor.execute(sql, panel_item).fetchval()
        self.logger.debug(f"{panel_item} returns {id_present} from dbo.NGSPanel")
        return True if id_present else False

    def version_in_ngs_panel(self, panel_item, panel_version):
        """Returns True if a panel item and version are present in the same record in dbo.NGSPanel.
        Args:
            panel_item (str): Moka-format PanelApp panel item e.g. 345_Amber
            panel_version (str): PanelApp panel version e.g. 1.2
        """
        pan_id, version_id = self.get_item_id(panel_item), self.get_item_id(panel_version)
        panel_present_with_version = self.cursor.execute(
            "SELECT * from dbo.NGSPanel WHERE Category = ? AND SubCategory = ?", pan_id, version_id
            ).fetchval()
        return True if panel_present_with_version else False

    def is_update(self, panel_item, panel_version):
        """Query Moka to determine if given panel version is an update.

        Returns True if query version is greater than the current Moka version.
        Returns False if no active panels found.
        Logs a warning if no version found in Moka for the input panel.
        Args:
            panel_item(str): Moka-format PanelApp panel item e.g. 345_Amber
            panel_version(str): PanelApp panel version e.g. 1.2
        """
        # SQL query to get the panel version. Item and NGSPanel tables are joined by SubCategory and
        # version is selected from the active panel item. Returns false if no active panels found.
        sql = textwrap.dedent("""
            SELECT Item from dbo.Item AS i
              LEFT join dbo.NGSPanel AS n
                ON i.ItemID = n.SubCategory
             WHERE n.Category = (SELECT ItemID FROM dbo.Item
                                  WHERE Item = ? COLLATE Latin1_General_CS_AS)
               AND n.Active = 1
        """)
        moka_version = self.cursor.execute(sql, panel_item).fetchval()
        if moka_version is None:
            self.logger.warning(f'No moka version found for {panel_item}')
            return False
        elif parse_version(panel_version) > parse_version(moka_version):
            return True
        else:
            return False

    def insert_into_moka(self, mokapanel, deactivate_old=False):
        """Insert Panel App panel data into Moka by updating NGSPanel and NGSPanel genes tables.
        Args:
            mokapanel(MokaPanel): An object containing moka-formatted Panel App panel data
        """
        # If deactivate flag passed, deactivate all matching panels in dbo.NGSPanel before insert.
        if deactivate_old:
            self.activator._deactivate_all(mokapanel.moka_id)
        # Insert Panel into NGS Panel
        self._insert_ngs_panel(mokapanel)
        # Insert panel genes into GenesHGNC_current
        self._insert_genes(mokapanel)

    def _insert_ngs_panel(self, mokapanel):
        """Insert MokaPanel into dbo.NGSPanel.
        Args:
            mokapanel(MokaPanel): An object containing moka-formatted Panel App panel data
        """
        # Prepare moka primary keys for panel data
        item_id = self.get_item_id(mokapanel.moka_id)
        version_id = self.get_item_id(mokapanel.version)
        panel_type = 3 if mokapanel.signed_off else 2 # Set panel type based on signed off panel or not
        self.logger.info(f'Inserting {mokapanel.moka_id} into dbo.NGSPanel at {item_id, version_id}')

        # Insert the NGSpanel, returning the key
        sql = textwrap.dedent("""
            INSERT INTO dbo.NGSPanel
                   (Category, SubCategory, Panel, PanelCode, Active, Checker1, CheckDate, PanelType)
            VALUES (?, ?, ?, 'Pan', 1, ? , CURRENT_TIMESTAMP, ?)
        """)
        self.cursor.execute(sql, item_id, version_id, mokapanel.name, self.MOKAUSER, panel_type)
        self.cursor.commit()

        # Update the Pan number record for the inserted panel.
        key = self._get_last_key()
        self.cursor.execute(
            """UPDATE NGSPanel set PanelCode = PanelCode+cast(NGSPanelID as VARCHAR)
                WHERE NGSPanelID = ?""",
            key
        )
        self.cursor.commit()

    def _insert_genes(self, mokapanel):
        """Insert MokaPanel genes into NGSPanelGenes
        Args:
            mokapanel(MokaPanel): An object containing moka-formatted Panel App panel data
        """
        # Prepare moka database primary keys for panel data
        item_id = self.get_item_id(mokapanel.moka_id)
        version_id = self.get_item_id(mokapanel.version)
        key = self.get_panel_id(item_id, version_id)
        self.logger.info(f'Inserting {mokapanel.moka_id} HGNC ids into dbo.NGSPanelGenes at {key}')

        # Prepare sql statement for gene insert
        sql = textwrap.dedent(
            """
            INSERT INTO NGSPanelGenes
                   (NGSPanelID, HGNCID, symbol, checker, checkdate)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
        )
        # For each gene, build the parameter list for the insert query above.
        # mokapanel.genes returns a list of (hgnc, symbol) objects which are accessed by index below
        params = [(key, gene[0], gene[1], self.MOKAUSER) for gene in mokapanel.genes]
        self.cursor.executemany(sql, params)
        self.cursor.commit()


class MokaPanelChecker(MokaDB):
    """Contains methods for checking PanelApp data against a Moka database.
    Inherits all arguments from class MokaDB.
    Args:
        server (str): Moka database server IP address e.g. '10.10.10.10'
        db (str): Moka database name
        user (str): Moka database user
        password (str): User password
        driver (str): Moka database driver
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + '.MokaPanelChecker')

    def get_new_items(self, panels):
        """Returns MokaPanel items in a given list that are not present in Moka's Item table.
        Args:
            panels (List[MokaPanel]): Moka panels built from the PanelApp API response
        Returns:
            new_panel_items (set): A set of panel items from *panels* that are not in dbo.Item
                E.g. { 345_Amber, ... }
        """
        # Build a set of all panels in the moka item table
        mdb_panels = self.get_item_set(self.PANEL_MOKA_ID_INDEX)
        # Build a set of all panel items in panel app
        panel_items = {panel.moka_id for panel in panels}
        # Get panels absent from Moka from the difference of the two sets.
        #   E.g. set(A) - set(B) = set(Items unique to A)
        return panel_items - mdb_panels

    def get_new_versions(self, panels):
        """Returns MokaPanel versions that are not present in dbo.Item.
        Args:
            panels (List[MokaPanel]): Moka panels built from the PanelApp API response
        Returns:
            new_panel_versions(Set): A set of panel versions e.g {1.2, 1.4, 0.56, ...}
        """
        # Build a set of all versions in the moka item table
        mdb_versions = self.get_item_set(self.PANEL_VERSION_INDEX)
        # Build a set of all panel versions in panel app
        panel_versions = {panel.version for panel in panels}
        # Get panel versions absent from Moka from the difference of the two sets.
        #   E.g. set(A) - set(B) = set(Items unique to A)
        return panel_versions - mdb_versions

    def check_hgncs(self, hgnc_list):
        """Returns True if input HGNCs are present in Moka. Otherwise raises an error.
        Args:
            hgnc_list(List): A list of HGNC IDS present in PanelApp. e.g. ['HGNC:123', 'HGNC:234'..]
        """
        # Get the set of hgnc ids in hgnc_list that are missing from Moka
        moka_hgnc = {
            row.HGNCID for row in self.cursor.execute('Select HGNCID from GenesHGNC_current')
        }
        new_hgncs = set(hgnc_list) - moka_hgnc
        if new_hgncs:
            # Raise an error if new HGNC IDS are present. This means the Moka HGNC snapshot must be
            # manually updated in order to import PanelApp data.
            exc_string = 'HGNCS missing from Moka GenesHGNC_current table: {}'.format(new_hgncs)
            self.logger.error(exc_string)
            raise Exception(exc_string)
        else:
            self.logger.info('All HGNC ids present in Moka.')
            return True
