# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Tests for sensor, binary_sensor, and calendar entity properties."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest


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


TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
YESTERDAY = TODAY - timedelta(days=1)
NEXT_WEEK = TODAY + timedelta(days=7)

TOMORROW_STR = TOMORROW.strftime("%d.%m.%Y")
NEXT_WEEK_STR = NEXT_WEEK.strftime("%d.%m.%Y")
YESTERDAY_STR = YESTERDAY.strftime("%d.%m.%Y")

ABFALLARTEN = ["Restabfall", "Papier", "Gelber Sack"]


def _make_coordinator(data=None, last_update_success=True):
    """Create a MockCoordinator with the given data."""
    entry = SimpleNamespace(entry_id="test_entry", title="Altstadt")
    return MockCoordinator(data=data, last_update_success=last_update_success, entry=entry)


def _make_sensor_data(abfallart, next_date=None, is_tomorrow=False, all_dates=None):
    """Build coordinator data dict for a single abfallart."""
    return {
        abfallart: {
            "next_date": next_date,
            "is_tomorrow": is_tomorrow,
            "all_dates": all_dates or [],
        }
    }


def _make_full_data():
    """Build coordinator data for all three abfallarten."""
    return {
        "Restabfall": {
            "next_date": TOMORROW_STR,
            "is_tomorrow": True,
            "all_dates": [TOMORROW_STR, NEXT_WEEK_STR],
        },
        "Papier": {
            "next_date": NEXT_WEEK_STR,
            "is_tomorrow": False,
            "all_dates": [NEXT_WEEK_STR],
        },
        "Gelber Sack": {
            "next_date": TOMORROW_STR,
            "is_tomorrow": True,
            "all_dates": [TOMORROW_STR],
        },
    }


class TestBEETrashDateSensorNativeValue:
    """Tests for BEETrashDateSensor.native_value."""

    def test_valid_date_returns_date_object(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date="15.03.2026")
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        result = sensor.native_value
        assert result == date(2026, 3, 15)

    def test_missing_next_date_returns_none(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_sensor_data("Restabfall"))
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.native_value is None

    def test_empty_string_returns_none(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date="")
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.native_value is None

    def test_malformed_date_returns_none(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date="not-a-date")
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.native_value is None

    def test_abfallart_not_in_data_returns_none(self, bee_sensor):
        coordinator = _make_coordinator(data={})
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.native_value is None


class TestBEETrashDateSensorIcon:
    """Tests for BEETrashDateSensor.icon."""

    def test_tomorrow_filled_icons(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.icon == "mdi:trash-can"

    def test_not_tomorrow_outline_icons(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=NEXT_WEEK_STR, is_tomorrow=False)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.icon == "mdi:trash-can-outline"

    def test_papier_tomorrow_icon(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Papier", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Papier", "entry1")
        assert sensor.icon == "mdi:file-document"

    def test_papier_not_tomorrow_icon(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Papier", next_date=NEXT_WEEK_STR, is_tomorrow=False)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Papier", "entry1")
        assert sensor.icon == "mdi:file-document-outline"

    def test_gelber_sack_tomorrow_icon(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Gelber Sack", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Gelber Sack", "entry1")
        assert sensor.icon == "mdi:recycle"

    def test_gelber_sack_not_tomorrow_icon(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Gelber Sack", next_date=NEXT_WEEK_STR, is_tomorrow=False)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Gelber Sack", "entry1")
        assert sensor.icon == "mdi:recycle-variant"

    def test_unknown_abfallart_fallback_icon(self, bee_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Unknown", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Unknown", "entry1")
        assert sensor.icon == "mdi:delete"

    def test_missing_is_tomorrow_defaults_to_false(self, bee_sensor):
        coordinator = _make_coordinator(
            data={"Restabfall": {"next_date": NEXT_WEEK_STR}}
        )
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.icon == "mdi:trash-can-outline"


class TestBEETrashDateSensorAvailable:
    """Tests for BEETrashDateSensor.available."""

    def test_available_when_success_and_data_present(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is True

    def test_unavailable_when_update_failed(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data(), last_update_success=False)
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is False

    def test_unavailable_when_abfallart_missing(self, bee_sensor):
        coordinator = _make_coordinator(data={"Papier": {"next_date": NEXT_WEEK_STR}})
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is False


class TestBEETrashDateSensorDeviceInfo:
    """Tests for BEETrashDateSensor.device_info."""

    def test_device_info_groups_under_entry(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        info = sensor.device_info
        assert info["identifiers"] == {("bee_trash", "test_entry")}
        assert info["name"] == "Altstadt"
        assert info["manufacturer"] == "BEE Emden"


class TestBEETrashDateSensorAttributes:
    """Tests for BEETrashDateSensor static attributes."""

    def test_unique_id_format(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_unique_id == "entry1_restabfall_date"

    def test_name_format(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_name == "Restabfall nächste Abholung"

    def test_device_class_is_date(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_device_class == "date"

    def test_entity_category_diagnostic(self, bee_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_sensor.BEETrashDateSensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_entity_category == "diagnostic"


class TestBEETrashBinarySensorIsOn:
    """Tests for BEETrashBinarySensor.is_on."""

    def test_on_when_tomorrow(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is True

    def test_off_when_not_tomorrow(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=NEXT_WEEK_STR, is_tomorrow=False)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is False

    def test_off_when_missing_data(self, bee_binary_sensor):
        coordinator = _make_coordinator(data={})
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is False

    def test_off_when_is_tomorrow_key_missing(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data={"Restabfall": {"next_date": TOMORROW_STR}}
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is False


class TestBEETrashBinarySensorAttributes:
    """Tests for BEETrashBinarySensor extra_state_attributes."""

    def test_extra_state_attributes_contains_next_date(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.extra_state_attributes == {"next_date": TOMORROW_STR}

    def test_extra_state_attributes_empty_when_no_data(self, bee_binary_sensor):
        coordinator = _make_coordinator(data={})
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.extra_state_attributes == {"next_date": None}


class TestBEETrashBinarySensorIcon:
    """Tests for BEETrashBinarySensor.icon."""

    def test_filled_icon_when_on(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is True
        assert sensor.icon == "mdi:trash-can"

    def test_outline_icon_when_off(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", next_date=NEXT_WEEK_STR, is_tomorrow=False)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.is_on is False
        assert sensor.icon == "mdi:trash-can-outline"

    def test_gelber_sack_icon_when_on(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Gelber Sack", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Gelber Sack", "entry1")
        assert sensor.icon == "mdi:recycle"

    def test_unknown_abfallart_fallback(self, bee_binary_sensor):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Unknown", next_date=TOMORROW_STR, is_tomorrow=True)
        )
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Unknown", "entry1")
        assert sensor.icon == "mdi:delete"


class TestBEETrashBinarySensorAvailable:
    """Tests for BEETrashBinarySensor.available."""

    def test_available_when_success_and_data_present(self, bee_binary_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is True

    def test_unavailable_when_update_failed(self, bee_binary_sensor):
        coordinator = _make_coordinator(data=_make_full_data(), last_update_success=False)
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is False

    def test_unavailable_when_abfallart_missing(self, bee_binary_sensor):
        coordinator = _make_coordinator(data={"Papier": {"next_date": NEXT_WEEK_STR}})
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.available is False

    def test_should_poll_is_false(self, bee_binary_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor.should_poll is False


class TestBEETrashBinarySensorStaticAttrs:
    """Tests for BEETrashBinarySensor static attributes."""

    def test_unique_id_format(self, bee_binary_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_unique_id == "entry1_restabfall"

    def test_name_format(self, bee_binary_sensor):
        coordinator = _make_coordinator(data=_make_full_data())
        sensor = bee_binary_sensor.BEETrashBinarySensor(coordinator, "Restabfall", "entry1")
        assert sensor._attr_name == "Restabfall Abholung morgen"


class TestBEETrashCalendarGetDates:
    """Tests for BEETrashCalendar._get_dates."""

    def test_parses_all_dates(self, bee_calendar):
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=["05.02.2026", "19.02.2026", "05.03.2026"],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        dates = cal._get_dates()
        assert dates == [date(2026, 2, 5), date(2026, 2, 19), date(2026, 3, 5)]

    def test_skips_malformed_dates(self, bee_calendar):
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=["05.02.2026", "not-a-date", "05.03.2026"],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        dates = cal._get_dates()
        assert dates == [date(2026, 2, 5), date(2026, 3, 5)]

    def test_empty_all_dates_returns_empty_list(self, bee_calendar):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", all_dates=[])
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal._get_dates() == []

    def test_missing_all_dates_key_returns_empty_list(self, bee_calendar):
        coordinator = _make_coordinator(data={"Restabfall": {}})
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal._get_dates() == []


class TestBEETrashCalendarEvent:
    """Tests for BEETrashCalendar.event (next upcoming event)."""

    def test_returns_next_future_event(self, bee_calendar):
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=[YESTERDAY_STR, TOMORROW_STR, NEXT_WEEK_STR],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        event = cal.event
        assert event is not None
        assert event.start == TOMORROW
        assert event.summary == "Restabfall (Altstadt)"

    def test_returns_none_when_all_dates_in_past(self, bee_calendar):
        past = TODAY - timedelta(days=30)
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=[past.strftime("%d.%m.%Y")],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal.event is None

    def test_returns_none_when_no_dates(self, bee_calendar):
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", all_dates=[])
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal.event is None

    def test_today_is_included_as_upcoming(self, bee_calendar):
        today_str = TODAY.strftime("%d.%m.%Y")
        coordinator = _make_coordinator(
            data=_make_sensor_data("Restabfall", all_dates=[today_str])
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        event = cal.event
        assert event is not None
        assert event.start == TODAY


class TestBEETrashCalendarGetEvents:
    """Tests for BEETrashCalendar.async_get_events."""

    @pytest.mark.asyncio
    async def test_returns_events_in_range(self, bee_calendar):
        d1 = TODAY + timedelta(days=1)
        d2 = TODAY + timedelta(days=5)
        d3 = TODAY + timedelta(days=10)
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=[d1.strftime("%d.%m.%Y"), d2.strftime("%d.%m.%Y"), d3.strftime("%d.%m.%Y")],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        events = await cal.async_get_events(None, datetime(d1.year, d1.month, d1.day), datetime(d3.year, d3.month, d3.day))
        assert len(events) == 2
        assert events[0].start == d1
        assert events[1].start == d2

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_events_in_range(self, bee_calendar):
        past = TODAY - timedelta(days=10)
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=[past.strftime("%d.%m.%Y")],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        events = await cal.async_get_events(None, datetime(TODAY.year, TODAY.month, TODAY.day), datetime((TODAY + timedelta(days=7)).year, (TODAY + timedelta(days=7)).month, (TODAY + timedelta(days=7)).day))
        assert events == []

    @pytest.mark.asyncio
    async def test_end_date_is_exclusive(self, bee_calendar):
        d1 = TODAY + timedelta(days=1)
        coordinator = _make_coordinator(
            data=_make_sensor_data(
                "Restabfall",
                all_dates=[d1.strftime("%d.%m.%Y")],
            )
        )
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        events = await cal.async_get_events(None, datetime(TODAY.year, TODAY.month, TODAY.day), datetime(d1.year, d1.month, d1.day))
        assert events == []


class TestBEETrashCalendarAvailable:
    """Tests for BEETrashCalendar.available."""

    def test_available_when_success_and_data_present(self, bee_calendar):
        coordinator = _make_coordinator(data=_make_full_data())
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal.available is True

    def test_unavailable_when_update_failed(self, bee_calendar):
        coordinator = _make_coordinator(data=_make_full_data(), last_update_success=False)
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal.available is False

    def test_unavailable_when_abfallart_missing(self, bee_calendar):
        coordinator = _make_coordinator(data={"Papier": {"next_date": NEXT_WEEK_STR}})
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal.available is False


class TestBEETrashCalendarDeviceInfo:
    """Tests for BEETrashCalendar.device_info."""

    def test_device_info_groups_under_entry(self, bee_calendar):
        coordinator = _make_coordinator(data=_make_full_data())
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        info = cal.device_info
        assert info["identifiers"] == {("bee_trash", "test_entry")}
        assert info["name"] == "Altstadt"
        assert info["manufacturer"] == "BEE Emden"


class TestBEETrashCalendarAttributes:
    """Tests for BEETrashCalendar static attributes."""

    def test_unique_id_format(self, bee_calendar):
        coordinator = _make_coordinator(data=_make_full_data())
        cal = bee_calendar.BEETrashCalendar(coordinator, "Restabfall")
        assert cal._attr_unique_id == "test_entry_restabfall_calendar"

    def test_name_is_abfallart(self, bee_calendar):
        coordinator = _make_coordinator(data=_make_full_data())
        cal = bee_calendar.BEETrashCalendar(coordinator, "Gelber Sack")
        assert cal._attr_name == "Gelber Sack"
