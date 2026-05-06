"""Utils for handling time."""

from datetime import datetime

import pytz


def seconds_to_formated_hours(seconds: int) -> str:
    """Convert seconds to a formated time"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'


def now() -> str:
    """Return current datetime with UTC 0"""
    return str(datetime.now(pytz.utc).isoformat())
