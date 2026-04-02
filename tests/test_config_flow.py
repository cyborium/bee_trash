# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Tests for BEETrashConfigFlow."""
from types import SimpleNamespace
from unittest.mock import MagicMock
import sys
from pathlib import Path

import pytest

# conftest.py already installed HA mocks at module import time.
# We just need to load the bee_trash modules.
COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"


def _load_module(name, path):
    """Load a module from a file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Register bee_trash as a package (if not already done by another test file)
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

bee_config_flow = _load_module("bee_trash.config_flow", COMPONENT_DIR / "config_flow.py")
sys.modules["bee_trash.config_flow"] = bee_config_flow

BEETrashConfigFlow = bee_config_flow.BEETrashConfigFlow
CONF_BEZIRK = bee_const.CONF_BEZIRK
BEZIRKE = bee_const.BEZIRKE


def _make_flow(existing_entries=None):
    """Create a config flow instance."""
    flow = BEETrashConfigFlow()
    if existing_entries:
        for entry in existing_entries:
            flow._add_existing_entry(entry)
    return flow


class TestConfigFlowForm:
    """Tests for config flow form display."""

    @pytest.mark.asyncio
    async def test_user_step_shows_form(self):
        """Initial step with no input should show district selector form."""
        flow = _make_flow()
        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_form_has_no_errors_initially(self):
        """Form should have empty errors dict on first display."""
        flow = _make_flow()
        result = await flow.async_step_user()
        assert result["errors"] == {}


class TestConfigFlowEntryCreation:
    """Tests for config flow entry creation."""

    @pytest.mark.asyncio
    async def test_valid_district_creates_entry(self):
        """Valid district selection should create config entry."""
        flow = _make_flow()
        result = await flow.async_step_user(user_input={CONF_BEZIRK: "Altstadt"})
        assert result["type"] == "create_entry"
        assert result["title"] == "Altstadt"
        assert result["data"] == {CONF_BEZIRK: "Altstadt"}

    @pytest.mark.asyncio
    async def test_entry_uses_bezirk_as_unique_id(self):
        """Selected bezirk should be set as unique ID."""
        flow = _make_flow()
        await flow.async_step_user(user_input={CONF_BEZIRK: "Wolthusen"})
        assert flow._unique_id == "Wolthusen"

    @pytest.mark.asyncio
    async def test_different_districts_create_entries(self):
        """Different districts should create separate entries."""
        flow = _make_flow()
        result1 = await flow.async_step_user(user_input={CONF_BEZIRK: "Altstadt"})
        result2 = await flow.async_step_user(user_input={CONF_BEZIRK: "Hafen"})
        assert result1["title"] == "Altstadt"
        assert result2["title"] == "Hafen"


class TestConfigFlowVersion:
    """Tests for config flow version."""

    def test_flow_version_is_one(self):
        """Config flow should declare VERSION = 1."""
        assert BEETrashConfigFlow.VERSION == 1


class TestConfigFlowDuplicateRejection:
    """Tests for duplicate config entry rejection."""

    @pytest.mark.asyncio
    async def test_duplicate_bezirk_raises_error(self):
        """Same district configured twice should raise DuplicateEntryError."""
        from conftest import DuplicateEntryError
        flow = _make_flow(existing_entries=["Altstadt"])
        with pytest.raises(DuplicateEntryError):
            await flow.async_step_user(user_input={CONF_BEZIRK: "Altstadt"})

    @pytest.mark.asyncio
    async def test_different_bezirk_succeeds_when_one_exists(self):
        """Different district should succeed when another is already configured."""
        flow = _make_flow(existing_entries=["Altstadt"])
        result = await flow.async_step_user(user_input={CONF_BEZIRK: "Hafen"})
        assert result["type"] == "create_entry"
        assert result["title"] == "Hafen"
