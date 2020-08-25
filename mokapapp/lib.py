import argparse
import requests
import itertools
import logging
from collections import namedtuple

MokaPanel = namedtuple("MokaPanel", "moka_id name version genes colour signed_off")

def cli(args):
    """Parse command line arguments.
    Args:
        args (List): Command line arguments e.g. ['-c', 'config.ini']
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="A mokapapp config.ini file", required=True)
    parser.add_argument('--logdir', help="A directory to write application logs. Default is current working directory.", default='.')
    parser.add_argument('--db', help="Database config entry to use. Default is mokadb_prod.", default="mokadb_prod")
    return parser.parse_args(args)

class MokaPanelFactory():
    def __init__(self, endpoints, mpobject=MokaPanel):
        self.endpoints = endpoints
        self.MokaPanelObject = mpobject

    def build(self, colours=None, head=None, reporter=None):
        panels = self._get_panelapp_data(head=head)

        unfiltered_moka_panels = [ 
            self._create_moka_panel(colour, panel)
            for colour, panel in itertools.product(colours, panels)
        ]
        moka_panels = list(filter(lambda x: len(x.genes) > 0, unfiltered_moka_panels))
        
        if reporter:
            reporter.add('Panels retrieved from panelapp', len(panels))
            reporter.add('MokaPanel objects created', len(moka_panels))

        return moka_panels

    def _create_moka_panel(self, colour, panel):
        """Returns a MokaPanel object for the colour and panel provided"""
        # To create accurate Moka Panel name and key binding, colour must be
        # capitalized. E.g. "Amber"
        colour = colour.capitalize()
        # Get genes in panel filtered to the colour
        confidence_colour_map = {
            "4": "Green", "3": "Green", "2": "Amber", "1": "Red", "0": "Red"
        }

        genes = [ # Creates a tuple of hgncid, gene symbol
            (record[0], record[1]) for record in panel["genes"]
            if confidence_colour_map[record[2]] == colour # Check that colour in panelapp
        ]

        # Set Moka name e.g.: "Intellectual disability (Panel App SO Green v3.2)"
        moka_name = "{} (Panel App {}{} v{})".format(
            panel['name'].replace('_','-'),
            "SO " if panel["signed_off"] else "",
            colour,
            panel['version']
        )

        moka_panel = self.MokaPanelObject(
                moka_id="{}_{}".format(panel['id'], colour),
                name=moka_name,
                version=panel['version'],
                genes=genes,
                colour=colour,
                signed_off=panel["signed_off"]
        )

        return moka_panel

    def _get_panelapp_data(self, head=None):
        # Get data for all signed off panels
        panels = list(PanelApp(endpoint=self.endpoints["signed_off_panels"], head=head))
        # Filter regular panels for those missing from signed-off endpoint.
        signed_off_panel_ids = { panel["id"] for panel in panels }
        regular_panels = PanelApp(endpoint=self.endpoints["panels"], head=head)
        remaining_panels = filter(
            lambda x: x["id"] not in signed_off_panel_ids,
            regular_panels
        )
        # Add additional regular panels to signedoff panels 
        panels.extend(list(remaining_panels))
        return panels

class PanelApp():
    """Iterable for panel data from PanelApp API /panels endpoints.

    Additionally, the result appends 

    Args:
        endpoint (str): A URL for a panelapp /panels endpoint to query
        head (int): Set a limit of PanelApp response objects to return from the head.
            Useful for testing without iterating over all panels.

    >>> pa = PanelApp()
    >>> for panel in pa:
    >>> ...  # Do something with panel
    """

    def __init__(
        self,
        endpoint=None,
        head=None
    ):
        self.endpoint = endpoint
        # Query PanelApp API. This is a generator and will not yield until iterated
        self._panels = self._get_panels()
        self.head = head
        # Set counter for head argument
        self.counter = 0

    def _get_panels(self):
        """Get all panels from instance endpoint"""
        # Get response from endpoint as dictionary
        response = requests.get(self.endpoint)
        response.raise_for_status()
        r = response.json()
        # Yield panels from the first response
        for panel in r['results']:
            panel_with_genes = self._add_panel_metadata(panel)
            yield panel_with_genes
        # API responses from the /panels endpoint are paginated.
        # While the response dictionary contains a url for the next page.
        while r['next']:
            # Set the response dictionary using the next page of API results.
            response = requests.get(r['next'])
            r = response.json()
            # Yield panels from current API results
            for panel in r['results']:
                panel_with_genes = self._add_panel_metadata(panel)
                yield panel_with_genes

    def _add_panel_metadata(self, panel: dict):
        """Add 'genes' and 'signed_off' as additional entries to a panelapp panel dictionary.

        For each gene in the panel, the 'genes' result contains a list of 
            (hgncid, symbol, confidence_level).
        'signed_off' is True if data came from the endpoint for signed off panels, else it is False.
        """
        # Query metadata endpoint for this panel
        genes_endpoint = f'{self.endpoint}/{panel["id"]}'
        genes_response = requests.get(genes_endpoint)
        genes_response.raise_for_status()
        r_json = genes_response.json()

        # Add genes list to panel
        panel["genes"] = [
            (record['gene_data']['hgnc_id'], record['gene_data']['hgnc_symbol'], record['confidence_level'])
            for record in r_json['genes']
        ]
        
        # Add signed off boolean to panel
        panel["signed_off"] = True if "signed_off" in r_json.keys() else False

        return panel

    def __iter__(self):
        return self

    def __next__(self):
        if self.head:
            while self.counter < self.head:
                self.counter += 1
                return next(self._panels)
            else:
                raise StopIteration()
        else:
            return next(self._panels)

class LogReporter():
    """Report stats from running of mokapapp to logfile."""

    def __init__(self):
        self.stats = {}
        self.logger = logging.getLogger('mokapapp.report')

    def add(self, stat_name, stat):
        try:
            self.stats[stat_name] += stat
        except KeyError:
            self.stats[stat_name] = stat

    def report_to_log(self):
        for stat, count in self.stats.items():
            log_string = ": ".join([str(stat), str(count)]) 
            self.logger.info(log_string)