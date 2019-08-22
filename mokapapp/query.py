"""query.py

Query Panel App API and prepare panel data for import into Moka:
1. Query Panel app for current versions of all panels
2. Create MokaPanel objects containing green and amber genes from each Panel
3. Write MokaPanels to standard output in json format.
"""
import json
import logging

from _jellypy import _panelapp
from mokapapp import lib


def main(head=None, print_json=False):
    """Query PanelApp and prepare data for Moka import.

    Args:
        head (int): Limit the number of panels returned to this value
        print_json (bool): If true, prints MokaPanel objects as jsons to standard output.
    Returns:
        json_moka_panels (List): A list of MokaPanel objects build from PanelApp API response
    """
    # Setup logging
    logging.basicConfig(level='DEBUG')
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Query Panel App for current version of all panels
    panels = _panelapp.PanelApp(head=head)
    # lib.MokaPanelFactor returns a generator. Convert to list for downstream applications.
    moka_panels = list(lib.MokaPanelFactory(panels, colours=['Green', 'Amber']).build())

    if print_json:
        # Read panels as dictionary and dump json to std::output
        # Note: If true, this function to behaves like an API response returning MokaPanels as dicts
        #   Designed for streaming Moka Panels to other applications on the machine
        json_moka_panels = [mp.as_dict() for mp in moka_panels]
        print(json.dumps(json_moka_panels))

    # Return moka panels, allowing other modules to work with panel list
    return moka_panels


if __name__ == "__main__":
    main(print_json=True)
