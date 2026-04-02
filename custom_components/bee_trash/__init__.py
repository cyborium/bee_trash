# SPDX-License-Identifier: GPL-3.0-or-later
# Modified from aha_trash by soundstorm (https://github.com/soundstorm/aha_trash)
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""The BEE Trash Pickup integration."""
import logging
from datetime import timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util
from homeassistant.const import Platform

from .const import DOMAIN, CONF_BEZIRK, BEZIRKE, ABFALLARTEN, ICS_URL_TEMPLATE
from .ics_parser import parse_ics

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass, entry):
    """Set up BEE Trash Pickup from a config entry."""
    coordinator = BEETrashCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Schedule daily update at 7 AM local time
    def async_schedule_daily_update():
        now = dt_util.now()
        next_update = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if next_update < now:
            next_update += timedelta(days=1)

        async def async_daily_refresh(_):
            """Refresh data and reschedule."""
            await coordinator.async_request_refresh()
            async_schedule_daily_update()

        async_track_point_in_time(hass, async_daily_refresh, next_update)

    async_schedule_daily_update()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class BEETrashCoordinator(DataUpdateCoordinator):
    """BEE Trash data update coordinator."""

    def __init__(self, hass, entry):
        """Initialize coordinator."""
        self.config = entry.data
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=12),
        )

    async def _async_update_data(self):
        """Fetch data from ICS feed."""
        bezirk = self.config[CONF_BEZIRK]
        slug = BEZIRKE.get(bezirk)
        if not slug:
            raise UpdateFailed(f"Unknown bezirk: {bezirk}")

        url = ICS_URL_TEMPLATE.format(slug=slug)
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Error response {resp.status}")
                ics_text = await resp.text()
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Fetch failed: {err}")

        result = parse_ics(ics_text, ABFALLARTEN)
        if not result:
            raise UpdateFailed("No trash data parsed from ICS")
        return result
