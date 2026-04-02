# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Tests for the ICS parser module."""
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

import pytest

# Import icalendar first so it gets stdlib calendar before we add our path
import icalendar  # noqa: F401

PARSER_DIR = Path(__file__).parent.parent / "custom_components" / "bee_trash"
sys.path.insert(0, str(PARSER_DIR))

from ics_parser import parse_ics, _extract_date, _categories_to_text, _parse_ddmmyyyy  # noqa: E402

SAMPLE_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:test_1
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:20260205
DTEND;VALUE=DATE:20260206
CATEGORIES:Restabfall (Graue Tonne), Papier, Pappe, Karton (Blaue Tonne), Gelber Sack (Gelbe Tonne)
SUMMARY:Grau,Gelb,Blau
END:VEVENT
BEGIN:VEVENT
UID:test_2
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:20260219
DTEND;VALUE=DATE:20260220
CATEGORIES:Restabfall (Graue Tonne), Gelber Sack (Gelbe Tonne)
SUMMARY:Grau,Gelb
END:VEVENT
BEGIN:VEVENT
UID:test_3
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:20260305
DTEND;VALUE=DATE:20260306
CATEGORIES:Papier, Pappe, Karton (Blaue Tonne)
SUMMARY:Blau
END:VEVENT
END:VCALENDAR
"""

ABFALLARTEN = ["Restabfall", "Papier", "Gelber Sack"]


def _parse_ddmmyyyy(text: str) -> date:
    day, month, year = map(int, text.split("."))
    return date(year, month, day)


class TestParseIcs:
    """Tests for parse_ics function."""

    def test_parses_all_abfallarten(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        assert "Restabfall" in result
        assert "Papier" in result
        assert "Gelber Sack" in result

    def test_all_dates_count(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        assert len(result["Restabfall"]["all_dates"]) == 2
        assert len(result["Papier"]["all_dates"]) == 2
        assert len(result["Gelber Sack"]["all_dates"]) == 2

    def test_date_format(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        for abfallart, data in result.items():
            for d in data["all_dates"]:
                parts = d.split(".")
                assert len(parts) == 3
                assert len(parts[0]) == 2
                assert len(parts[1]) == 2
                assert len(parts[2]) == 4

    def test_dates_are_sorted(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        for abfallart, data in result.items():
            dates = data["all_dates"]
            assert dates == sorted(dates, key=_parse_ddmmyyyy)

    def test_next_date_is_first(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        for abfallart, data in result.items():
            assert data["next_date"] == data["all_dates"][0]

    def test_is_tomorrow_false_for_far_future(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        for abfallart, data in result.items():
            assert data["is_tomorrow"] is False

    def test_is_tomorrow_true_when_applicable(self):
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%d.%m.%Y")
        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test_tomorrow
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:{tomorrow.strftime("%Y%m%d")}
DTEND;VALUE=DATE:{(tomorrow + timedelta(days=1)).strftime("%Y%m%d")}
CATEGORIES:Restabfall (Graue Tonne)
SUMMARY:Grau
END:VEVENT
END:VCALENDAR
"""
        result = parse_ics(ics, ABFALLARTEN)
        assert result["Restabfall"]["is_tomorrow"] is True
        assert result["Restabfall"]["next_date"] == tomorrow_str

    def test_empty_ics_returns_empty(self):
        ics = "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"
        result = parse_ics(ics, ABFALLARTEN)
        assert result == {}

    def test_unknown_abfallart_not_included(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        assert "Bioabfall" not in result
        assert "Leichtverpackungen" not in result

    def test_missing_categories_skipped(self):
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test_no_cat
DTSTAMP:20251126T153102
DTSTART;VALUE=DATE:20260205
DTEND;VALUE=DATE:20260206
SUMMARY:Something
END:VEVENT
END:VCALENDAR
"""
        result = parse_ics(ics, ABFALLARTEN)
        assert result == {}

    def test_missing_dtstart_skipped(self):
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test_no_dt
CATEGORIES:Restabfall (Graue Tonne)
SUMMARY:Grau
END:VEVENT
END:VCALENDAR
"""
        result = parse_ics(ics, ABFALLARTEN)
        assert result == {}

    def test_output_shape_matches_coordinator_format(self):
        result = parse_ics(SAMPLE_ICS, ABFALLARTEN)
        for abfallart, data in result.items():
            assert "next_date" in data
            assert "is_tomorrow" in data
            assert "all_dates" in data
            assert isinstance(data["next_date"], str)
            assert isinstance(data["is_tomorrow"], bool)
            assert isinstance(data["all_dates"], list)


class TestExtractDate:
    """Tests for _extract_date helper."""

    def test_date_value_returns_date(self):
        """DTSTART with date value should return date directly."""
        from icalendar.prop import vDate
        dtstart = vDate(date(2026, 3, 15))
        assert _extract_date(dtstart) == date(2026, 3, 15)

    def test_datetime_value_returns_date(self):
        """DTSTART with datetime value should return .date()."""
        from icalendar.prop import vDDDTypes
        dt_val = datetime(2026, 3, 15, 10, 30, 0)
        dtstart = vDDDTypes(dt_val)
        assert _extract_date(dtstart) == date(2026, 3, 15)

    def test_unexpected_type_raises_typeerror(self):
        """Non-date/datetime value should raise TypeError."""
        class FakeDtstart:
            dt = "not-a-date"
        with pytest.raises(TypeError):
            _extract_date(FakeDtstart())


class TestCategoriesToText:
    """Tests for _categories_to_text helper."""

    def test_bytes_categories_decoded(self):
        """Bytes with to_ical method should be decoded."""
        from icalendar.prop import vCategory
        cat = vCategory("Restabfall (Graue Tonne)")
        result = _categories_to_text(cat)
        assert "Restabfall" in result

    def test_str_categories_returned_as_is(self):
        """String input should pass through unchanged."""
        assert _categories_to_text("Restabfall") == "Restabfall"

    def test_list_of_categories_joined(self):
        """List of categories should be joined with commas."""
        from icalendar.prop import vCategory
        cats = [vCategory("Restabfall"), vCategory("Papier")]
        result = _categories_to_text(cats)
        assert "Restabfall" in result
        assert "Papier" in result

    def test_list_with_non_category_items(self):
        """List with non-Category items should use str() fallback."""
        result = _categories_to_text(["Restabfall", "Papier"])
        assert "Restabfall" in result
        assert "Papier" in result

    def test_unknown_type_falls_back_to_str(self):
        """Unknown type should return str() of the value."""
        result = _categories_to_text(42)
        assert result == "42"


class TestParseDdmmyyyy:
    """Tests for _parse_ddmmyyyy helper."""

    def test_parses_valid_date(self):
        assert _parse_ddmmyyyy("15.03.2026") == date(2026, 3, 15)

    def test_parses_single_digit_day_month(self):
        assert _parse_ddmmyyyy("05.02.2026") == date(2026, 2, 5)
