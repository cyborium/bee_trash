# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Integration tests for platform setup and entity wiring."""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock
import sys
from pathlib import Path

import pytest

# conftest.py already installed HA mocks at module import time.
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"


def _load_module(name, path):
    """Load a module from a file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Register bee_trash as a package (if not already done)
if "bee_trash" not in sys.modules:
    import importlib.util
    _pkg_spec = importlib.util.spec_from_file_location(
        "bee_trash", COMPONENT_DIR / "__init__.py",
        submodule_search_locations=[str(COMPONENT_DIR)],
    )
    bee_trash_pkg = importlib.util.module_from_spec(_pkg_spec)
    sys.modules["bee_trash"] = bee_trash_pkg

bee_const = _load_module("bee_trash.const", COMPONENT_DIR / "const.py")
sys.modules["bee_trash.const"] = bee_const

bee_ics = _load_module("bee_trash.ics_parser", COMPONENT_DIR / "ics_parser.py")
sys.modules["bee_trash.ics_parser"] = bee_ics

bee_init = _load_module("bee_trash.__init__", COMPONENT_DIR / "__init__.py")
sys.modules["bee_trash.__init__"] = bee_init

bee_sensor = _load_module("bee_trash.sensor", COMPONENT_DIR / "sensor.py")
sys.modules["bee_trash.sensor"] = bee_sensor

bee_binary_sensor = _load_module("bee_trash.binary_sensor", COMPONENT_DIR / "binary_sensor.py")
sys.modules["bee_trash.binary_sensor"] = bee_binary_sensor

bee_calendar = _load_module("bee_trash.calendar", COMPONENT_DIR / "calendar.py")
sys.modules["bee_trash.calendar"] = bee_calendar

DOMAIN = bee_const.DOMAIN
CONF_BEZIRK = bee_const.CONF_BEZIRK
ABFALLARTEN = bee_const.ABFALLARTEN


TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
NEXT_WEEK = TODAY + timedelta(days=7)

SAMPLE_COORDINATOR_DATA = {
    "Restabfall": {
        "next_date": TOMORROW.strftime("%d.%m.%Y"),
        "is_tomorrow": True,
        "all_dates": [
            TOMORROW.strftime("%d.%m.%Y"),
            NEXT_WEEK.strftime("%d.%m.%Y"),
        ],
    },
    "Papier": {
        "next_date": NEXT_WEEK.strftime("%d.%m.%Y"),
        "is_tomorrow": False,
        "all_dates": [NEXT_WEEK.strftime("%d.%m.%Y")],
    },
    "Gelber Sack": {
        "next_date": TOMORROW.strftime("%d.%m.%Y"),
        "is_tomorrow": True,
        "all_dates": [
            TOMORROW.strftime("%d.%m.%Y"),
            NEXT_WEEK.strftime("%d.%m.%Y"),
        ],
    },
}


def _make_hass_with_coordinator(coordinator):
    """Create a mock hass with coordinator stored in hass.data."""
    entry = SimpleNamespace(
        entry_id="test_entry_42",
        title="Altstadt",
        data={CONF_BEZIRK: "Altstadt"},
    )
    hass = MagicMock()
    hass.data = {DOMAIN: {entry.entry_id: coordinator}}
    return hass, entry


def _make_coordinator(data=None):
    """Create a MockCoordinator with the given data."""
    from tests.conftest import MockCoordinator
    return MockCoordinator(data=data or {})


class TestSensorPlatformSetup:
    """Tests for sensor platform async_setup_entry."""

    @pytest.mark.asyncio
    async def test_creates_one_sensor_per_abfallart(self):
        """Should create exactly one sensor entity for each waste type."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_sensor.async_setup_entry(hass, entry, added.extend)
        assert len(added) == len(ABFALLARTEN)

    @pytest.mark.asyncio
    async def test_sensor_unique_ids_match_abfallarten(self):
        """Each sensor's unique_id should contain the entry_id and abfallart slug."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_sensor.async_setup_entry(hass, entry, added.extend)
        unique_ids = {e._attr_unique_id for e in added}
        expected = {
            f"{entry.entry_id}_restabfall_date",
            f"{entry.entry_id}_papier_date",
            f"{entry.entry_id}_gelber_sack_date",
        }
        assert unique_ids == expected

    @pytest.mark.asyncio
    async def test_sensor_data_flows_to_native_value(self):
        """Sensor native_value should reflect coordinator data."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_sensor.async_setup_entry(hass, entry, added.extend)
        restabfall = [e for e in added if e.abfallart == "Restabfall"][0]
        assert restabfall.native_value == TOMORROW


class TestBinarySensorPlatformSetup:
    """Tests for binary_sensor platform async_setup_entry."""

    @pytest.mark.asyncio
    async def test_creates_one_binary_sensor_per_abfallart(self):
        """Should create exactly one binary sensor entity for each waste type."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_binary_sensor.async_setup_entry(hass, entry, added.extend)
        assert len(added) == len(ABFALLARTEN)

    @pytest.mark.asyncio
    async def test_binary_sensor_unique_ids_match_abfallarten(self):
        """Each binary sensor's unique_id should contain the entry_id and abfallart."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_binary_sensor.async_setup_entry(hass, entry, added.extend)
        unique_ids = {e._attr_unique_id for e in added}
        expected = {
            f"{entry.entry_id}_restabfall",
            f"{entry.entry_id}_papier",
            f"{entry.entry_id}_gelber sack",
        }
        assert unique_ids == expected

    @pytest.mark.asyncio
    async def test_binary_sensor_is_on_reflects_coordinator(self):
        """Binary sensor is_on should match coordinator's is_tomorrow."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_binary_sensor.async_setup_entry(hass, entry, added.extend)
        restabfall = [e for e in added if e.abfallart == "Restabfall"][0]
        papier = [e for e in added if e.abfallart == "Papier"][0]
        assert restabfall.is_on is True
        assert papier.is_on is False


class TestCalendarPlatformSetup:
    """Tests for calendar platform async_setup_entry."""

    @pytest.mark.asyncio
    async def test_creates_one_calendar_per_abfallart(self):
        """Should create exactly one calendar entity for each waste type."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_calendar.async_setup_entry(hass, entry, added.extend)
        assert len(added) == len(ABFALLARTEN)

    @pytest.mark.asyncio
    async def test_calendar_unique_ids_match_abfallarten(self):
        """Each calendar's unique_id should contain the coordinator entry_id and abfallart slug."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_calendar.async_setup_entry(hass, entry, added.extend)
        unique_ids = {e._attr_unique_id for e in added}
        cid = coordinator.entry.entry_id
        expected = {
            f"{cid}_restabfall_calendar",
            f"{cid}_papier_calendar",
            f"{cid}_gelber_sack_calendar",
        }
        assert unique_ids == expected

    @pytest.mark.asyncio
    async def test_calendar_event_returns_next_upcoming(self):
        """Calendar event property should return the next future event."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_calendar.async_setup_entry(hass, entry, added.extend)
        papier = [e for e in added if e.abfallart == "Papier"][0]
        event = papier.event
        assert event is not None
        assert event.start == NEXT_WEEK
        assert event.summary == "Papier (Altstadt)"

    @pytest.mark.asyncio
    async def test_calendar_get_events_in_range(self):
        """async_get_events should return events within the given date range."""
        coordinator = _make_coordinator(SAMPLE_COORDINATOR_DATA)
        hass, entry = _make_hass_with_coordinator(coordinator)
        added = []
        await bee_calendar.async_setup_entry(hass, entry, added.extend)
        restabfall = [e for e in added if e.abfallart == "Restabfall"][0]
        start = SimpleNamespace(date=lambda: TODAY)
        end = SimpleNamespace(date=lambda: TODAY + timedelta(days=10))
        events = await restabfall.async_get_events(hass, start, end)
        assert len(events) == 2
        assert all(e.summary == "Restabfall (Altstadt)" for e in events)
