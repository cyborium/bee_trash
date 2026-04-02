# SPDX-License-Identifier: GPL-3.0-or-later
# Modified from aha_trash by soundstorm (https://github.com/soundstorm/aha_trash)
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Config flow for BEE Trash Pickup integration."""
import logging

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_BEZIRK, BEZIRKE

_LOGGER = logging.getLogger(__name__)


class BEETrashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BEE Trash Pickup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step: show district selector."""
        errors = {}

        if user_input is not None:
            bezirk = user_input[CONF_BEZIRK]
            await self.async_set_unique_id(bezirk)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=bezirk,
                data={CONF_BEZIRK: bezirk},
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_BEZIRK): vol.In(list(BEZIRKE.keys())),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
