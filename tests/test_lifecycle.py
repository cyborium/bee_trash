# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""End-to-end lifecycle tests: config entry → coordinator fetch → entity setup → unload."""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from pathlib import Path

import pytest
from aioresponses import aioresponses
from aiohttp import ClientSession

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"


def _load_module(name, path):
    """Load a module from a file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
BEZIRKE = bee_const.BEZIRKE
ABFALLARTEN = bee_const.ABFALLARTEN
ICS_URL_TEMPLATE = bee_const.ICS_URL_TEMPLATE
PLATFORMS = bee_init.PLATFORMS
BEETrashCoordinator = bee_init.BEETrashCoordinator
UpdateFailed = bee_init.UpdateFailed


TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
NEXT_WEEK = TODAY + timedelta(days=7)

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


def _make_hass():
    """Create a mock hass with config entry plumbing."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


def _make_entry(bezirk="Altstadt"):
    """Create a mock config entry."""
    return SimpleNamespace(
        entry_id="test_lifecycle_entry",
        title=bezirk,
        data={CONF_BEZIRK: bezirk},
    )


async def _setup_with_real_fetch(hass, entry):
    """Run async_setup_entry, letting coordinator do a real ICS fetch via aioresponses."""
    return await bee_init.async_setup_entry(hass, entry)


async def _setup_platforms(hass, entry):
    """Manually run platform setup_entry for all platforms and collect entities."""
    all_entities = []
    for platform_module in [bee_sensor, bee_binary_sensor, bee_calendar]:
        added = []
        await platform_module.async_setup_entry(hass, entry, added.extend)
        all_entities.extend(added)
    return all_entities


class TestFullLifecycle:
    """Tests for the complete entry → fetch → entity lifecycle."""

    @pytest.mark.asyncio
    async def test_coordinator_fetches_ics_and_entities_reflect_data(self):
        """Coordinator should fetch real ICS data and entities should reflect it."""
        hass = _make_hass()
        entry = _make_entry("Altstadt")
        slug = BEZIRKE["Altstadt"]
        url = ICS_URL_TEMPLATE.format(slug=slug)

        coordinator = BEETrashCoordinator(hass, entry)

        with aioresponses() as mocked:
            mocked.get(url, status=200, body=SAMPLE_ICS)
            with patch.object(bee_init, "async_get_clientsession", return_value=ClientSession()):
                data = await coordinator._async_update_data()

        coordinator.data = data
        coordinator.last_update_success = True
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        assert "Restabfall" in coordinator.data
        assert "Papier" in coordinator.data
        assert "Gelber Sack" in coordinator.data

        entities = await _setup_platforms(hass, entry)
        assert len(entities) == len(ABFALLARTEN) * len(PLATFORMS)

        restabfall_sensor = [
            e for e in entities
            if hasattr(e, "abfallart") and e.abfallart == "Restabfall"
            and hasattr(e, "native_value")
        ][0]
        assert restabfall_sensor.native_value == TOMORROW

        restabfall_binary = [
            e for e in entities
            if hasattr(e, "abfallart") and e.abfallart == "Restabfall"
            and hasattr(e, "is_on")
        ][0]
        assert restabfall_binary.is_on is True

        papier_calendar = [
            e for e in entities
            if hasattr(e, "abfallart") and e.abfallart == "Papier"
            and hasattr(e, "event")
        ][0]
        event = papier_calendar.event
        assert event is not None
        assert event.start == NEXT_WEEK

    @pytest.mark.asyncio
    async def test_unload_cleans_up_hass_data(self):
        """Unload should remove the entry from hass.data and unload platforms."""
        hass = _make_hass()
        entry = _make_entry("Altstadt")
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()

        result = await bee_init.async_unload_entry(hass, entry)

        assert result is True
        assert entry.entry_id not in hass.data[DOMAIN]
        hass.config_entries.async_unload_platforms.assert_called_once_with(entry, PLATFORMS)
