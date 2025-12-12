from __future__ import annotations

from datetime import datetime, time

from rgbxmastree.config import Schedule


def _time_in_window(now_t: time, start: time, end: time) -> bool:
    if start == end:
        # Treat as "always off" (zero-length window)
        return False
    if start < end:
        return start <= now_t < end
    # Crosses midnight, e.g. 22:00 -> 06:00
    return now_t >= start or now_t < end


def is_within_schedule(now: datetime, schedule: Schedule) -> bool:
    if schedule.days is not None:
        if now.weekday() not in schedule.days:
            return False
    return _time_in_window(now.time(), schedule.start_time(), schedule.end_time())


