# APP/TESTS/test_CIPACwatcher.py
import pytest
from bs4 import BeautifulSoup

from APP.WEBSITES.CIPACwatcher import CIPACwatcher


@pytest.fixture
def cipac_instance():
    """Fixture to provide a minimal CIPACwatcher instance for testing."""
    return CIPACwatcher(items=[], user_config={}, catalog_config={})


def test_extract_ref_basic(cipac_instance):
    """Test that a standard reference like 'Réf. : SR 3231060' is correctly extracted."""
    html = "<p class='ref'>Réf. : SR 3231060</p>"
    soup = BeautifulSoup(html, "html.parser")

    ref = cipac_instance._extract_ref(soup)
    assert ref == "SR 3231060"


def test_extract_ref_with_extra_label(cipac_instance):
    """Ensure the regex stops before the next label like 'EAN'."""
    html = "<p class='ref'>Réf. : SR 3231060  EAN : 123456789</p>"
    soup = BeautifulSoup(html, "html.parser")

    ref = cipac_instance._extract_ref(soup)
    assert ref == "SR 3231060"


def test_extract_ref_missing(cipac_instance):
    """Test when no 'Réf. :' is present in the HTML."""
    html = "<p class='ref'>EAN : 123456789</p>"
    soup = BeautifulSoup(html, "html.parser")

    ref = cipac_instance._extract_ref(soup)
    assert ref is None
