from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime, time, timedelta
from typing import Literal


Mode = Literal["manual_on", "manual_off", "auto"]


def _parse_hhmm(s: str) -> time:
    parts = s.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time '{s}', expected HH:MM")
    hh = int(parts[0])
    mm = int(parts[1])
    return time(hour=hh, minute=mm)


def _fmt_hhmm(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"


@dataclass
class ScheduleBlock:
    start_hhmm: str = "07:30"
    end_hhmm: str = "23:00"
    # days: 0=Mon ... 6=Sun. None means every day.
    days: list[int] | None = None
    enabled: bool = True

    def start_time(self) -> time:
        return _parse_hhmm(self.start_hhmm)

    def end_time(self) -> time:
        return _parse_hhmm(self.end_hhmm)


MAX_SCHEDULE_BLOCKS = 5


@dataclass
class AppConfig:
    mode: Mode = "auto"
    program_id: str = "rgb_cycle"
    program_speed: float = 1.0
    # Brightness controls (0..100 percent). Mapped to APA102 0..31 bits by controller.
    body_brightness_pct: int = 50
    star_brightness_pct: int = 50
    schedule_blocks: list[ScheduleBlock] = field(default_factory=lambda: [ScheduleBlock()])
    # ISO 8601 local time string (no timezone) or None
    countdown_until: str | None = None

    def countdown_until_dt(self) -> datetime | None:
        if not self.countdown_until:
            return None
        # Accept either "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DDTHH:MM:SS.sss"
        return datetime.fromisoformat(self.countdown_until)

    def set_countdown_minutes(self, minutes: int, now: datetime) -> None:
        until = now.replace(microsecond=0) + timedelta(minutes=minutes)
        self.countdown_until = until.isoformat()

    def clear_countdown(self) -> None:
        self.countdown_until = None


def load_config(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return AppConfig()

    blocks_raw = raw.get("schedule_blocks") or []
    schedule_blocks: list[ScheduleBlock] = []
    for b in blocks_raw[:MAX_SCHEDULE_BLOCKS]:
        if isinstance(b, dict):
            schedule_blocks.append(ScheduleBlock(
                start_hhmm=b.get("start_hhmm", "07:30"),
                end_hhmm=b.get("end_hhmm", "23:00"),
                days=b.get("days"),
                enabled=b.get("enabled", True),
            ))
    if not schedule_blocks:
        schedule_blocks = [ScheduleBlock()]

    cfg = AppConfig(
        mode=raw.get("mode", "auto"),
        program_id=raw.get("program_id", "rgb_cycle"),
        program_speed=float(raw.get("program_speed", 1.0)),
        body_brightness_pct=int(raw.get("body_brightness_pct", 50)),
        star_brightness_pct=int(raw.get("star_brightness_pct", 50)),
        schedule_blocks=schedule_blocks,
        countdown_until=raw.get("countdown_until"),
    )
    return cfg


def save_config(path: str, cfg: AppConfig) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = asdict(cfg)

    # #region agent log
    import json as json_module
    with open('/Users/james/Github/rgbxmastree/.cursor/debug.log', 'a') as f:
        f.write(json_module.dumps({"location":"config.py:save_config:before","message":"Before formatting","data":{"schedule_blocks":data.get("schedule_blocks")},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"E"})+'\n')
    # #endregion

    # Ensure schedule_blocks format stays HH:MM even if we later store parsed values.
    for block in data.get("schedule_blocks", []):
        block["start_hhmm"] = _fmt_hhmm(_parse_hhmm(block.get("start_hhmm", "07:30")))
        block["end_hhmm"] = _fmt_hhmm(_parse_hhmm(block.get("end_hhmm", "23:00")))

    # Clamp brightness to sane bounds before persisting (defensive against manual edits).
    data["body_brightness_pct"] = max(0, min(100, int(data.get("body_brightness_pct", 50))))
    data["star_brightness_pct"] = max(0, min(100, int(data.get("star_brightness_pct", 50))))

    fd, tmp_path = tempfile.mkstemp(prefix="rgbxmastree_", suffix=".json", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass


