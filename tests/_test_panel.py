"""test_panel.py

Tests for Panel App API client and Moka Panel Factory
"""
import pytest
import logging
from mokapapp import lib
import json
from mocks import mock_panel, mock_json
from _jellypy import _panelapp

logger = logging.getLogger()


def test_panels(PanelApp):
    """Assert that the panelapp object is an iterable container of panels"""
    panelapp = PanelApp()
    first_panel = next(panelapp)
    logger.info(first_panel)
    expected_keys = ['id', 'hash_id', 'name', 'version']
    assert all([key in first_panel.keys() for key in expected_keys])

def test_panel_loop(PanelApp):
    """Check that PanelApp objects are iterable"""
    panelapp = PanelApp()
    counter = 0
    for panel in panelapp:
        counter += 1
    assert counter > 300

def test_panel_head(PanelApp):
    """Test that the PanelApp 'head' kwarg limits expected number of panels"""
    counter = 0
    limit = 10
    for panel in PanelApp(head=limit):
        counter += 1
    assert counter == limit   

def test_moka_panel_factory():
    """Test that the Moka Panel factory returns a list of Moka Panel objects"""
    panels = [mock_panel, mock_panel, mock_panel]
    mp_factory = lib.MokaPanelFactory(panels, colours=['Green', 'Amber'])
    moka_panels = mp_factory.build()
    logger.info(next(moka_panels))
    assert all([isinstance(pan, lib.MokaPanel) for pan in moka_panels])

def test_mp_dict():
    """Test that the mokapanel dict contains expected keys"""
    moka_panels = lib.MokaPanelFactory([mock_panel], colours=['Green']).build()
    test = next(moka_panels).as_dict()
    expected_keys = ['name', 'colour', 'moka_id', 'version', 'genes']
    assert all(map(
        lambda x: x in test.keys(), expected_keys
    ))

def test_mp_genes():
    """Test that the moka panel factory produces a list of tuples for genes"""
    moka_panels = lib.MokaPanelFactory([mock_panel], colours=['Green']).build()
    test = next(moka_panels)
    assert all([
        isinstance(gene_tuple, tuple) for gene_tuple in test.genes
    ])

def test_mp_from_dict():
    """Test that the MokaPanel can be read from a dictionary object"""
    data = json.loads(mock_json)
    mp = lib.MokaPanel.from_dict(data[0])
    assert mp.name == "Adult solid tumours cancer susceptibility (Panel App SO Amber v1.6)"
    assert mp.genes[0] == ("HGNC:25070", "ACD")
    assert mp.moka_id == "245_Amber"
    assert mp.colour == "Amber"
    assert mp.signed_off == True

def test_moka_panels(PanelApp):
    """Test that MokaPanels generated from API have a panel id and genes.
        Note: Long API call if this iterates over all panelapp panels. Use head options for speedup
    """
    mp_factory = lib.MokaPanelFactory(PanelApp(head=40), colours=['Green', 'Amber'])
    counter = 0
    for panel in mp_factory.build():
        counter += 1
        if counter % 20 == 0:
            logger.info(f"Tested {counter} panels succesfully. Working on {panel.name}")
        assert panel.moka_id is not None
        assert len(panel.genes) > 0

def test_signed_off(PanelApp):
    panel_signed_off = next(PanelApp(head=1, endpoint=PanelApp.SIGNED_OFF_ENDPOINT))
    panel_normal = next(PanelApp(head=1, endpoint=PanelApp.PANELS_ENDPOINT))

    assert panel_normal["signed_off"] == False
    assert panel_signed_off["signed_off"] == True

    normal_mps = list(lib.MokaPanelFactory(PanelApp(head=3), colours=['Green', 'Amber']).build())
    so_mps = list(lib.MokaPanelFactory(PanelApp(head=3, endpoint=PanelApp.SIGNED_OFF_ENDPOINT), colours=['Green', 'Amber']).build())
