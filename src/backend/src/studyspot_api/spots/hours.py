"""Evaluation of OpenStreetMap opening_hours expressions."""

from datetime import datetime
from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from opening_hours import OpeningHours as OsmOpeningHours
from pydantic import BaseModel, field_validator

HoursStatus = Literal["open", "closed", "unknown"]


class SpotOpeningHours(BaseModel):
    """The source expression and local timezone for one study spot."""

    expression: str
    timezone: str = "America/New_York"

    @field_validator("expression")
    @classmethod
    def valid_expression(cls, value: str) -> str:
        expression = value.strip()
        if not expression:
            raise ValueError("opening_hours expression must not be blank")
        try:
            OsmOpeningHours(expression)
        except Exception as error:
            # The native binding raises ParserError, which its type stubs omit.
            raise ValueError("Invalid opening_hours expression") from error
        return expression

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Unknown IANA timezone") from error
        return value


@lru_cache(maxsize=2048)
def _parser(expression: str, timezone: str, latitude: float, longitude: float) -> OsmOpeningHours:
    return OsmOpeningHours(
        expression,
        timezone=ZoneInfo(timezone),
        country="US",
        coords=(latitude, longitude),
    )


def hours_status_at(
    hours: SpotOpeningHours | None,
    moment: datetime,
    latitude: float,
    longitude: float,
) -> HoursStatus:
    """Return the published hours status at an aware instant."""
    if hours is None:
        return "unknown"
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("moment must be timezone-aware")

    try:
        parser = _parser(hours.expression, hours.timezone, latitude, longitude)
        local_moment = moment.astimezone(ZoneInfo(hours.timezone))
        if parser.is_open(local_moment):
            return "open"
        if parser.is_unknown(local_moment):
            return "unknown"
        return "closed"
    except Exception:
        # Invalid source expressions must never be reported as definitely open.
        return "unknown"
