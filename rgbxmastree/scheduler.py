from __future__ import annotations

from datetime import datetime, time

from rgbxmastree.config import ScheduleBlock


def _time_in_window(now_t: time, start: time, end: time) -> bool:
    if start == end:
        # Treat as "always off" (zero-length window)
        return False
    if start < end:
        return start <= now_t < end
    # Crosses midnight, e.g. 22:00 -> 06:00
    return now_t >= start or now_t < end


def is_within_block(now: datetime, block: ScheduleBlock) -> bool:
    """Check if current time falls within a single schedule block."""
    if not block.enabled:
        return False
    if block.days is not None:
        if now.weekday() not in block.days:
            return False
    return _time_in_window(now.time(), block.start_time(), block.end_time())


def is_within_schedule(now: datetime, blocks: list[ScheduleBlock]) -> bool:
    """Check if current time falls within ANY enabled schedule block."""
    return any(is_within_block(now, block) for block in blocks)


