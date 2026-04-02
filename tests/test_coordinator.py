# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Tests for BEETrashCoordinator fetch behavior."""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

import pytest
from aioresponses import aioresponses
from aiohttp import ClientSession

# Setup HA mocks before importing
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"


class MockDataUpdateCoordinator:
    """Mock that mimics DataUpdateCoordinator's __init__ signature."""
    def __init__(self, hass, logger, *, name, update_interval=None):
        self.hass = hass
        self.name = name
        self.update_interval = update_interval
        self.last_update_success = True
        self.data = None

class MockUpdateFailed(Exception):
    """Mock UpdateFailed exception."""
    pass

def _setup_ha_mocks():
    """Install mock Home Assistant modules."""
    mock_device_registry = MagicMock()
    mock_device_registry.DeviceEntryType = SimpleNamespace(SERVICE="service")
    mock_device_registry.DeviceInfo = dict

    mock_sensor = MagicMock()
    mock_sensor.SensorDeviceClass = SimpleNamespace(DATE="date")
    mock_sensor.SensorEntity = object

    mock_binary_sensor = MagicMock()
    mock_binary_sensor.BinarySensorEntity = object

    mock_calendar = MagicMock()

    class MockCalendarEvent:
        def __init__(self, *, start, end, summary):
            self.start = start
            self.end = end
            self.summary = summary

    mock_calendar.CalendarEntity = object
    mock_calendar.CalendarEvent = MockCalendarEvent

    mock_entity = MagicMock()
    mock_entity.EntityCategory = SimpleNamespace(DIAGNOSTIC="diagnostic")

    mock_const = MagicMock()
    mock_const.Platform = SimpleNamespace(
        BINARY_SENSOR="binary_sensor",
        SENSOR="sensor",
        CALENDAR="calendar",
    )

    mock_update_coordinator = MagicMock()
    mock_update_coordinator.DataUpdateCoordinator = MockDataUpdateCoordinator
    mock_update_coordinator.UpdateFailed = MockUpdateFailed

    mocks = {
        "homeassistant": MagicMock(),
        "homeassistant.helpers": MagicMock(),
        "homeassistant.helpers.device_registry": mock_device_registry,
        "homeassistant.components": MagicMock(),
        "homeassistant.components.sensor": mock_sensor,
        "homeassistant.components.binary_sensor": mock_binary_sensor,
        "homeassistant.components.calendar": mock_calendar,
        "homeassistant.helpers.entity": mock_entity,
        "homeassistant.const": mock_const,
        "homeassistant.helpers.update_coordinator": mock_update_coordinator,
        "homeassistant.helpers.aiohttp_client": MagicMock(),
        "homeassistant.util": MagicMock(),
        "homeassistant.util.dt": MagicMock(),
        "homeassistant.config_entries": MagicMock(),
        "voluptuous": MagicMock(),
    }

    for name, mod in mocks.items():
        if name not in sys.modules:
            sys.modules[name] = mod


_setup_ha_mocks()


def _load_module(name, path):
    """Load a module from a file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Register bee_trash as a package so relative imports work
import importlib.util
_pkg_spec = importlib.util.spec_from_file_location(
    "bee_trash", COMPONENT_DIR / "__init__.py",
    submodule_search_locations=[str(COMPONENT_DIR)],
)
bee_trash_pkg = importlib.util.module_from_spec(_pkg_spec)
sys.modules["bee_trash"] = bee_trash_pkg

# Load const first (no relative imports)
bee_const = _load_module("bee_trash.const", COMPONENT_DIR / "const.py")
sys.modules["bee_trash.const"] = bee_const

# Load ics_parser (no relative imports)
bee_ics = _load_module("bee_trash.ics_parser", COMPONENT_DIR / "ics_parser.py")
sys.modules["bee_trash.ics_parser"] = bee_ics

# Now load __init__ (has relative import from .ics_parser)
bee_init = _load_module("bee_trash.__init__", COMPONENT_DIR / "__init__.py")
sys.modules["bee_trash.__init__"] = bee_init

CONF_BEZIRK = bee_const.CONF_BEZIRK
BEZIRKE = bee_const.BEZIRKE
ABFALLARTEN = bee_const.ABFALLARTEN
ICS_URL_TEMPLATE = bee_const.ICS_URL_TEMPLATE
UpdateFailed = bee_init.UpdateFailed
BEETrashCoordinator = bee_init.BEETrashCoordinator


TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
TOMORROW_STR = TOMORROW.strftime("%d.%m.%Y")
NEXT_WEEK = TODAY + timedelta(days=7)
NEXT_WEEK_STR = NEXT_WEEK.strftime("%d.%m.%Y")

SAMPLE_ICS = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test_1
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:{TOMORROW.strftime("%Y%m%d")}
DTEND;VALUE=DATE:{(TOMORROW + timedelta(days=1)).strftime("%Y%m%d")}
CATEGORIES:Restabfall (Graue Tonne), Gelber Sack (Gelbe Tonne)
SUMMARY:Grau,Gelb
END:VEVENT
BEGIN:VEVENT
UID:test_2
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:{NEXT_WEEK.strftime("%Y%m%d")}
DTEND;VALUE=DATE:{(NEXT_WEEK + timedelta(days=1)).strftime("%Y%m%d")}
CATEGORIES:Papier, Pappe, Karton (Blaue Tonne)
SUMMARY:Blau
END:VEVENT
BEGIN:VEVENT
UID:test_3
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:{(TODAY + timedelta(days=14)).strftime("%Y%m%d")}
DTEND;VALUE=DATE:{(TODAY + timedelta(days=15)).strftime("%Y%m%d")}
CATEGORIES:Restabfall (Graue Tonne), Gelber Sack (Gelbe Tonne)
SUMMARY:Grau,Gelb
END:VEVENT
END:VCALENDAR
"""

EMPTY_ICS = "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"


def _make_coordinator(bezirk="Altstadt"):
    """Create a real BEETrashCoordinator with mocked hass."""
    mock_hass = MagicMock()
    mock_entry = SimpleNamespace(
        entry_id="test_entry",
        title=bezirk,
        data={CONF_BEZIRK: bezirk},
    )
    return BEETrashCoordinator(mock_hass, mock_entry)


class TestCoordinatorFetchSuccess:
    """Tests for successful ICS fetch and parsing."""

    @pytest.mark.asyncio
    async def test_parses_ics_and_returns_data(self):
        """Successful fetch should return parsed data for all abfallarten."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                result = await coordinator._async_update_data()

        assert "Restabfall" in result
        assert "Papier" in result
        assert "Gelber Sack" in result

    @pytest.mark.asyncio
    async def test_data_shape_matches_expected_format(self):
        """Output should have next_date, is_tomorrow, all_dates keys."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                result = await coordinator._async_update_data()

        for abfallart, data in result.items():
            assert "next_date" in data
            assert "is_tomorrow" in data
            assert "all_dates" in data
            assert isinstance(data["next_date"], str)
            assert isinstance(data["is_tomorrow"], bool)
            assert isinstance(data["all_dates"], list)

    @pytest.mark.asyncio
    async def test_is_tomorrow_true_when_applicable(self):
        """Tomorrow's date should set is_tomorrow=True."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                result = await coordinator._async_update_data()

        assert result["Restabfall"]["is_tomorrow"] is True
        assert result["Gelber Sack"]["is_tomorrow"] is True
        assert result["Papier"]["is_tomorrow"] is False

    @pytest.mark.asyncio
    async def test_dates_are_sorted(self):
        """All dates should be sorted ascending."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                result = await coordinator._async_update_data()

        for abfallart, data in result.items():
            dates = data["all_dates"]
            assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_uses_correct_ics_url_for_district(self):
        """Should fetch from the correct district-specific ICS URL."""
        coordinator = _make_coordinator("Constantia")
        slug = BEZIRKE["Constantia"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                await coordinator._async_update_data()
            requested_urls = [str(k[1]) for k in mocked.requests.keys()]
            assert url in requested_urls


class TestCoordinatorFetchFailures:
    """Tests for coordinator failure scenarios."""

    @pytest.mark.asyncio
    async def test_http_404_raises_update_failed(self):
        """404 response should raise UpdateFailed."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=404)
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_http_500_raises_update_failed(self):
        """500 response should raise UpdateFailed."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=500)
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_empty_ics_raises_update_failed(self):
        """ICS with no VEVENTs should raise UpdateFailed."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=EMPTY_ICS)
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_unknown_bezirk_raises_update_failed(self):
        """Unknown district should raise UpdateFailed without HTTP call."""
        coordinator = _make_coordinator("NonExistent")

        with aioresponses() as mocked:
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
            # Verify no HTTP request was made
            assert len(mocked.requests) == 0

    @pytest.mark.asyncio
    async def test_network_error_raises_update_failed(self):
        """Connection failure should raise UpdateFailed."""
        coordinator = _make_coordinator("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        with aioresponses() as mocked:
            mocked.get(url, exception=ConnectionError("Connection refused"))
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()


class TestCoordinatorConfiguration:
    """Tests for coordinator configuration."""

    def test_update_interval_is_12_hours(self):
        """Coordinator should have 12-hour update interval."""
        coordinator = _make_coordinator()
        assert coordinator.update_interval == timedelta(hours=12)

    def test_coordinator_name_is_domain(self):
        """Coordinator name should match DOMAIN."""
        coordinator = _make_coordinator()
        assert coordinator.name == bee_const.DOMAIN

    def test_config_stores_bezirk(self):
        """Coordinator should store config entry data."""
        coordinator = _make_coordinator("Wolthusen")
        assert coordinator.config[CONF_BEZIRK] == "Wolthusen"
