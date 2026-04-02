# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 cyborium (https://github.com/cyborium/bee_trash)

"""Parse BEE Emden ICS calendar feeds into structured waste collection data."""
from datetime import date, datetime, timedelta

from icalendar import Calendar


def parse_ics(ics_text: str, abfallarten: list[str]) -> dict:
    """Parse ICS text and return waste collection data keyed by abfallart.

    Matches CATEGORIES entries against known abfallarten by substring search.
    Output shape matches the existing coordinator data format:
        {abfallart: {"next_date": str, "is_tomorrow": bool, "all_dates": [str]}}
    Dates are formatted as DD.MM.YYYY.
    """
    cal = Calendar.from_ical(ics_text)
    tomorrow = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")

    result: dict[str, dict] = {}

    for vevent in cal.walk("VEVENT"):
        dtstart = vevent.get("DTSTART")
        categories = vevent.get("CATEGORIES")
        if dtstart is None or categories is None:
            continue

        try:
            event_date = _extract_date(dtstart)
        except (ValueError, TypeError):
            continue

        date_str = event_date.strftime("%d.%m.%Y")
        cats_text = _categories_to_text(categories)

        for abfallart in abfallarten:
            if abfallart.lower() in cats_text.lower():
                if abfallart not in result:
                    result[abfallart] = {
                        "next_date": None,
                        "is_tomorrow": False,
                        "all_dates": [],
                    }
                result[abfallart]["all_dates"].append(date_str)

    for abfallart, data in result.items():
        data["all_dates"].sort(key=lambda d: _parse_ddmmyyyy(d))
        today_str = date.today().strftime("%d.%m.%Y")
        upcoming = [d for d in data["all_dates"] if d >= today_str]
        data["next_date"] = upcoming[0] if upcoming else None
        data["is_tomorrow"] = data["next_date"] == tomorrow

    return result


def _extract_date(dtstart) -> date:
    """Extract a date object from an icalendar DTSTART property."""
    val = dtstart.dt
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    raise TypeError(f"Unexpected DTSTART type: {type(val)}")


def _categories_to_text(categories) -> str:
    """Convert CATEGORIES property to a plain text string."""
    if hasattr(categories, "to_ical"):
        return categories.to_ical().decode("utf-8")
    if isinstance(categories, str):
        return categories
    if isinstance(categories, list):
        parts = []
        for cat in categories:
            if hasattr(cat, "to_ical"):
                parts.append(cat.to_ical().decode("utf-8"))
            else:
                parts.append(str(cat))
        return ",".join(parts)
    return str(categories)


def _parse_ddmmyyyy(text: str) -> date:
    """Parse DD.MM.YYYY string into a date object."""
    day, month, year = map(int, text.split("."))
    return date(year, month, day)
