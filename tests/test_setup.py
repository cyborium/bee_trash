# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Tests for async_setup_entry and async_unload_entry."""
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock, patch
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

DOMAIN = bee_const.DOMAIN
CONF_BEZIRK = bee_const.CONF_BEZIRK
PLATFORMS = bee_init.PLATFORMS
BEETrashCoordinator = bee_init.BEETrashCoordinator


def _make_hass():
    """Create a mock hass object."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


def _make_entry(bezirk="Altstadt"):
    """Create a mock config entry."""
    return SimpleNamespace(
        entry_id="test_entry_id",
        title=bezirk,
        data={CONF_BEZIRK: bezirk},
    )


class TestSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_stores_coordinator_in_hass_data(self):
        """Coordinator should be stored in hass.data[DOMAIN][entry_id]."""
        hass = _make_hass()
        entry = _make_entry()
        result = await bee_init.async_setup_entry(hass, entry)
        assert result is True
        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        assert isinstance(hass.data[DOMAIN][entry.entry_id], BEETrashCoordinator)

    @pytest.mark.asyncio
    async def test_calls_first_refresh_on_coordinator(self):
        """Coordinator async_config_entry_first_refresh should be called."""
        hass = _make_hass()
        entry = _make_entry()
        with patch.object(BEETrashCoordinator, "async_config_entry_first_refresh", new_callable=AsyncMock) as mock_refresh:
            await bee_init.async_setup_entry(hass, entry)
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_forwards_to_platforms(self):
        """Should forward entry setup to all platforms."""
        hass = _make_hass()
        entry = _make_entry()
        await bee_init.async_setup_entry(hass, entry)
        hass.config_entries.async_forward_entry_setups.assert_called_once_with(entry, PLATFORMS)

    @pytest.mark.asyncio
    async def test_schedules_daily_update(self):
        """Should call async_track_point_in_time for daily scheduling."""
        from tests.conftest import MockDataUpdateCoordinator
        hass = _make_hass()
        entry = _make_entry()
        mock_event = sys.modules["homeassistant.helpers.event"]
        mock_event.async_track_point_in_time.reset_mock()
        await bee_init.async_setup_entry(hass, entry)
        mock_event.async_track_point_in_time.assert_called_once()


class TestUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.mark.asyncio
    async def test_removes_entry_from_hass_data(self):
        """Entry should be removed from hass.data after unload."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()
        result = await bee_init.async_unload_entry(hass, entry)
        assert result is True
        assert entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unloads_platforms(self):
        """Should call async_unload_platforms with correct platforms."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()
        await bee_init.async_unload_entry(hass, entry)
        hass.config_entries.async_unload_platforms.assert_called_once_with(entry, PLATFORMS)

    @pytest.mark.asyncio
    async def test_returns_unload_result(self):
        """Should return the result from async_unload_platforms."""
        hass = _make_hass()
        entry = _make_entry()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()
        hass.config_entries.async_unload_platforms.return_value = False
        result = await bee_init.async_unload_entry(hass, entry)
        assert result is False
