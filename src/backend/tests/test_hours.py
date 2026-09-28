"""Real opening_hours evaluation at NYC local time boundaries."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from studyspot_api.spots.hours import SpotOpeningHours, hours_status_at

NYU = (40.73, -73.99)


def status(expression, instant):
    return hours_status_at(SpotOpeningHours(expression=expression), instant, *NYU)


def test_overnight_hours_cross_midnight():
    hours = "Fr 22:00-02:00"
    assert status(hours, datetime(2026, 10, 3, 3, 0, tzinfo=UTC)) == "open"
    assert status(hours, datetime(2026, 10, 3, 6, 0, tzinfo=UTC)) == "closed"


def test_holiday_exception_overrides_regular_hours():
    hours = "Mo-Su 09:00-17:00; PH off"
    assert status(hours, datetime(2026, 9, 7, 16, 0, tzinfo=UTC)) == "closed"


def test_daylight_saving_transition_uses_local_timezone():
    hours = "Su 00:00-04:00"
    assert status(hours, datetime(2026, 11, 1, 5, 30, tzinfo=UTC)) == "open"
    assert status(hours, datetime(2026, 11, 1, 6, 30, tzinfo=UTC)) == "open"


def test_unknown_and_invalid_hours_never_report_open():
    instant = datetime(2026, 9, 28, 14, 0, tzinfo=UTC)
    assert hours_status_at(None, instant, *NYU) == "unknown"
    assert status("24/7 unknown", instant) == "unknown"
    with pytest.raises(ValidationError):
        SpotOpeningHours(expression="not an opening hours expression")
