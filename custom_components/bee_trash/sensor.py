# SPDX-License-Identifier: GPL-3.0-or-later
# Modified from aha_trash by soundstorm (https://github.com/soundstorm/aha_trash)
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Sensor platform for BEE Trash Pickup – next pickup dates."""
from datetime import date as dt_date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, ABFALLARTEN, MANUFACTURER

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BEETrashDateSensor(coordinator, abfallart, entry.entry_id)
        for abfallart in ABFALLARTEN
    ]
    async_add_entities(entities)

class BEETrashDateSensor(SensorEntity):
    """Sensor showing the next pickup date for a trash type."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, abfallart, entry_id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.abfallart = abfallart
        self._attr_unique_id = f"{entry_id}_{abfallart.lower().replace(' ', '_')}_date"
        self._attr_name = f"{abfallart} nächste Abholung"

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
    def native_value(self):
        """Return the next pickup date as date object."""
        data = self.coordinator.data.get(self.abfallart, {})
        next_date_str = data.get("next_date")
        if not next_date_str:
            return None
        try:
            day, month, year = map(int, next_date_str.split("."))
            return dt_date(year, month, day)
        except ValueError:
            return None

    @property
    def icon(self):
        """Dynamic icon"""
        is_tomorrow = self.coordinator.data.get(self.abfallart, {}).get("is_tomorrow", False)
        if is_tomorrow:
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

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.abfallart in self.coordinator.data

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
