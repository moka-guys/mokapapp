"""_panelapp.py

Python client for GeL PanelApp API
"""
import requests
import logging

logger = logging.getLogger('panelapp')


class PanelApp():
    """Iterable container for panel data from PanelApp /panels endpoint.

    Args:
        head (int): Set a limit of PanelApp response objects to return from the head.
            Useful for testing without iterating over all panels.

    >>> pa = PanelApp()
    >>> for panel in pa:
    >>> ...  # Do something with panel
    """

    def __init__(
        self,
        endpoint="https://panelapp.genomicsengland.co.uk/api/v1/panels",
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
            yield panel
        # API responses from the /panels endpoint are paginated.
        # While the response dictionary contains a url for the next page.
        while r['next']:
            # Set the response dictionary using the next page of API results.
            response = requests.get(r['next'])
            r = response.json()
            # Yield panels from current API results
            for panel in r['results']:
                yield panel

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
