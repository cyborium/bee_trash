# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Shared test fixtures for bee_trash entity tests."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

import pytest


COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"


class DuplicateEntryError(Exception):
    """Raised when a config entry with the same unique ID already exists."""
    pass


class MockConfigFlow:
    """Mock Home Assistant ConfigFlow base class."""
    VERSION = 1
    def __init_subclass__(cls, domain=None, **kwargs):
        cls._domain = domain
        super().__init_subclass__(**kwargs)
    def __init__(self):
        self._hass = None
        self._flow_result = None
        self._unique_id = None
        self._existing_entries = []
    def async_show_form(self, *, step_id, data_schema=None, errors=None):
        self._flow_result = {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
        return self._flow_result
    def async_create_entry(self, *, title, data):
        self._flow_result = {"type": "create_entry", "title": title, "data": data}
        return self._flow_result
    async def async_set_unique_id(self, unique_id):
        self._unique_id = unique_id
    def _abort_if_unique_id_configured(self):
        if self._unique_id in self._existing_entries:
            raise DuplicateEntryError(f"Unique ID {self._unique_id} already configured")
    def _add_existing_entry(self, unique_id):
        self._existing_entries.append(unique_id)


class MockDataUpdateCoordinator:
    """Mock Home Assistant DataUpdateCoordinator."""
    def __init__(self, hass, logger, *, name, update_interval=None):
        self.hass = hass
        self.name = name
        self.update_interval = update_interval
        self.last_update_success = True
        self.data = None
    async def async_config_entry_first_refresh(self):
        pass
    async def async_request_refresh(self):
        pass
    def async_add_listener(self, callback):
        return lambda: None


class MockUpdateFailed(Exception):
    """Mock UpdateFailed exception."""
    pass


def _setup_ha_mocks():
    """Install mock Home Assistant modules at module import time."""
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

    mock_dt_util = MagicMock()
    mock_dt_util.now.return_value = MagicMock(
        replace=MagicMock(return_value=MagicMock(__lt__=lambda s, o: False))
    )

    mock_config_entries = MagicMock()
    mock_config_entries.ConfigFlow = MockConfigFlow
    mock_config_entries.Handlers = MagicMock()

    mock_event = MagicMock()
    mock_event.async_track_point_in_time = MagicMock()

    mock_aiohttp = MagicMock()
    mock_voluptuous = MagicMock()

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
        "homeassistant.helpers.aiohttp_client": mock_aiohttp,
        "homeassistant.helpers.update_coordinator": mock_update_coordinator,
        "homeassistant.util": MagicMock(),
        "homeassistant.util.dt": mock_dt_util,
        "homeassistant.config_entries": mock_config_entries,
        "homeassistant.helpers.event": mock_event,
        "voluptuous": mock_voluptuous,
    }

    for name, mod in mocks.items():
        if name not in sys.modules:
            sys.modules[name] = mod

    # Wire sub-module attributes on parent modules for 'from X import Y' style imports
    sys.modules["homeassistant"].config_entries = mock_config_entries
    sys.modules["homeassistant"].const = mock_const
    sys.modules["homeassistant.helpers"].device_registry = mock_device_registry
    sys.modules["homeassistant.helpers"].entity = mock_entity
    sys.modules["homeassistant.helpers"].aiohttp_client = mock_aiohttp
    sys.modules["homeassistant.helpers"].update_coordinator = mock_update_coordinator
    sys.modules["homeassistant.helpers"].event = mock_event
    sys.modules["homeassistant.util"].dt = mock_dt_util
    sys.modules["homeassistant.components"].sensor = mock_sensor
    sys.modules["homeassistant.components"].binary_sensor = mock_binary_sensor
    sys.modules["homeassistant.components"].calendar = mock_calendar


# Set up mocks immediately at module import time (before any test file imports)
_setup_ha_mocks()


def _load_module(name, path):
    """Load a module from a file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session", autouse=True)
def ha_mocks():
    """Install HA mocks before any test imports."""
    _setup_ha_mocks()


@pytest.fixture(scope="session")
def bee_const():
    """Load const module."""
    return _load_module("bee_trash.const", COMPONENT_DIR / "const.py")


@pytest.fixture(scope="session")
def bee_sensor(ha_mocks, bee_const):
    """Load sensor module."""
    return _load_module("bee_trash.sensor", COMPONENT_DIR / "sensor.py")


@pytest.fixture(scope="session")
def bee_binary_sensor(ha_mocks, bee_const):
    """Load binary_sensor module."""
    return _load_module("bee_trash.binary_sensor", COMPONENT_DIR / "binary_sensor.py")


@pytest.fixture(scope="session")
def bee_calendar(ha_mocks, bee_const):
    """Load calendar module."""
    return _load_module("bee_trash.calendar", COMPONENT_DIR / "calendar.py")


class MockCoordinator:
    """Minimal coordinator mock for entity property tests."""

    def __init__(self, data=None, last_update_success=True, entry=None):
        self.data = data or {}
        self.last_update_success = last_update_success
        self.entry = entry or SimpleNamespace(
            entry_id="test_entry_id",
            title="Altstadt",
        )
        self._listeners = []

    def async_add_listener(self, callback):
        self._listeners.append(callback)
        return lambda: None
