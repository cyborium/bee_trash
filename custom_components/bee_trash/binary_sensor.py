# SPDX-License-Identifier: GPL-3.0-or-later
# Modified from aha_trash by soundstorm (https://github.com/soundstorm/aha_trash)
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Binary sensor platform for BEE Trash Pickup."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, ABFALLARTEN, MANUFACTURER

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BEETrashBinarySensor(coordinator, abfallart, entry.entry_id)
        for abfallart in ABFALLARTEN
    ]
    async_add_entities(entities)

class BEETrashBinarySensor(BinarySensorEntity):
    """BEE Trash binary sensor entity."""

    def __init__(self, coordinator, abfallart, entry_id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.abfallart = abfallart
        self._attr_unique_id = f"{entry_id}_{abfallart.lower()}"
        self._attr_name = f"{abfallart} Abholung morgen"

    @property
    def device_info(self):
        """Return device info to group entities under the address device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        data = self.coordinator.data.get(self.abfallart, {})
        return data.get("is_tomorrow", False)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data.get(self.abfallart, {})
        return {"next_date": data.get("next_date")}

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.abfallart in self.coordinator.data

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def icon(self):
        """Return the icon to use in the frontend, depending on state."""
        if self.is_on:
            icons = {
                "Restabfall": "mdi:trash-can",
                "Papier": "mdi:file-document",
                "Gelber Sack": "mdi:recycle",
            }
        else:
            icons = {
                "Restabfall": "mdi:trash-can-outline",
                "Papier": "mdi:file-document-outline",
                "Gelber Sack": "mdi:recycle-variant",
            }
        return icons.get(self.abfallart, "mdi:delete")

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
