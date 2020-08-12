"""lib.py

General class and function library for updating Moka panels.
"""
import argparse
import configparser
import itertools
import logging

import requests

logger = logging.getLogger(__name__)


def _config_reader(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def cli(args):
    """Parse command line arguments.
    Args:
        args (List): Command line arguments e.g. ['-c', 'config.ini']
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="A mokapapp config.ini file", type=_config_reader)
    parser.add_argument('--logfile', help="A file to write application log outputs", default=None)
    return parser.parse_args(args)


def get_hgnc_set(panels):
    """Returns a set of all HGNC ids from a list of MokaPanel objects"""
    # Create a list of all unique HGNCID-GeneSymbol combinations in the MokaPanels
    genes_nest = [panel.genes for panel in panels]
    genes_list = itertools.chain.from_iterable(genes_nest)  # Flatten list of lists
    # Return the set of unique HGNCIDs
    hgnc_list, _ = zip(*genes_list)
    hgnc_set = set(hgnc_list)
    logger.debug('Pulled {} hgnc ids from {} MokaPanel objects'.format(len(hgnc_set), len(panels)))
    return hgnc_set


class MokaPanel():
    """Convert PanelApp data into Moka readable panels.

    Args:
        moka_id(str): A moka-form panelapp panel identifer e.g. 254_Amber
        name(str): A moka-form panel name
            e.g. "Congenital disorders of glycosylation version (PanelApp Amber v1.6)"
        version(str): Panel version e.g. 1.6
        genes(List[Tuple,]): A list of (HGNC, SYMBOL) tuples from PanelApp
        colour(str): Human readable panel colour converted from PanelApp
            gene confidence level scores. e.g. 'Amber'.
    """
    def __init__(self, moka_id, name, version, genes, colour):
        self.moka_id = moka_id
        self.name = name
        self.version = version
        self.genes = genes
        self.colour = colour

    def __str__(self):
        return f"{self.moka_id}, {self.name}. No Genes: {len(self.genes)}"

    def as_dict(self):
        return {
            "moka_id": self.moka_id,
            "name": self.name,
            "version": self.version,
            "genes": self.genes,
            "colour": self.colour
        }

    @staticmethod
    def from_dict(data):
        """Returns a MokaPanel object from a dictionary of MokaPanel key-value pairs.

        @staticmethod allows panels to be build from the class rather than from instances e.g.:
            MokaPanel.from_dict(data)
        """
        genes = [tuple(hgnc_symbol) for hgnc_symbol in data['genes']]
        return MokaPanel(
            data['moka_id'], data['name'], data['version'], genes,
            data['colour']
        )


class MokaPanelFactory():
    """Build Moka Panels from PanelApp data and separate panels by gene colours.

    Args:
        colours(List): Gene colours to filter for each panel
        panels(List[dict,]): List of dictionary objects containing PanelApp
            /panels API endpoint responses."""

    def __init__(self, panels, colours=None):
        self.colours = colours
        self.panels = panels
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f'Building Moka Panels with {self.colours}')

    def build(self):
        """Returns a list of MokaPanel objects for each colour-panel combination.
        Args:
            panels(dict): Panel response from Panel App /panels endpoint
        """
        # All panels and colours
        all_panels = itertools.product(self.colours, self.panels)

        # Build MokaPanels
        for colour, panel in all_panels:
                self.logger.debug('Getting {}, {}, {}'.format(colour, panel['id'], panel['name']))
                # Get MokaPanel object.
                moka_panel = self._get_moka_panel(colour, panel)
                self.logger.debug(moka_panel)
                # moka_panel is None if panel has 0 genes or 0 hash present in the API
                if moka_panel:
                    # Yield panel. Generator can be chained to more efficiently process
                    yield(moka_panel)

    def _get_moka_panel(self, colour, panel):
        """Returns a MokaPanel object for the colour and panel provided"""
        # To create accurate Moka Panel name and key binding, colour must be
        # capitalized. E.g. "Amber"
        _colour = colour.capitalize()
        # Get genes in panel filtered to the colour
        genes = self._get_panel_genes(_colour, panel['id'])
        # Return none if panel has no genes or hash
        if len(genes) == 0 or panel['id'] is None:
            self.logger.debug(
                f'{panel["name"], panel["id"]} Skipping MokaPanel build: HashID {panel["hash_id"]}, gene_count {len(genes)})'
            )
            return None
        else:  # Return MokaPanel
            mp = MokaPanel(
                "{}_{}".format(panel['id'], _colour),
                self._get_moka_name(panel['name'], _colour, panel['version']),
                panel['version'],
                genes,
                _colour
            )
            self.logger.debug(f"Returning {mp}")
            return mp

    def _get_moka_name(self, name, colour, version):
        """Return a string containing the human-readable panel name for Moka"""
        clean_name = name.replace('_', '-')
        return "{} (Panel App {} v{})".format(clean_name, colour, version)

    def _get_panel_genes(self, colour, panel_id):
        """Query PanelApp API for panel genes filtered by colour.

        Args:
            colour (str): Filter for genes returned for input panel. Options: Green, Amber, Red
            panel_id (str): ID for a PanelApp panel. E.g. 67
        """
        endpoint = "https://panelapp.genomicsengland.co.uk/api/v1/panels"
        # PanelApp genes API contains a confidence_level field with values (0-4). The PanelApp
        # handbook describes the mapping of these values to gene colours. We represent this as a
        # dictionary for lookups.
        panel_colour_map = {
            "4": "Green", "3": "Green", "2": "Amber", "1": "Red", "0": "Red"
        }
        # Call PanelApp API for panel data using ID
        response = requests.get(f"{endpoint}/{panel_id}")
        response.raise_for_status()
        r_json = response.json()
        self.logger.debug(f"Found genes for {panel_id}")

        # Return a list of (HGNCID, GeneSymbol) tuples for each gene in the API response,
        # filtered by colour
        genes = [
            (record['gene_data']['hgnc_id'], record['gene_data']['hgnc_symbol'])
            for record in r_json['genes']
            if panel_colour_map[record['confidence_level']] == colour
        ]
        self.logger.debug(f'{len(genes)} {colour} present in panel {panel_id}')
        return genes
