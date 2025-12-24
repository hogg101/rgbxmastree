from __future__ import annotations

from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from rgbxmastree.config import ScheduleBlock, MAX_SCHEDULE_BLOCKS
from rgbxmastree.controller import TreeController
from rgbxmastree.programs import PROGRAMS
from rgbxmastree.scheduler import is_within_schedule


def create_app(config_path: str) -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    controller = TreeController(config_path=config_path)
    app.extensions["rgbxmastree_controller"] = controller
    SPEED_MIN = 0.1
    SPEED_MAX = 200.0

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/")
    def index():
        return send_from_directory(app.template_folder, "index.html")

    @app.get("/api/state")
    def api_state():
        cfg = controller.get_config()
        now = datetime.now()
        return jsonify(
            {
                "now": now.isoformat(timespec="seconds"),
                "mode": cfg.mode,
                "program_id": cfg.program_id,
                "program_speed": cfg.program_speed,
                "program_speed_min": SPEED_MIN,
                "program_speed_max": SPEED_MAX,
                "brightness": {
                    "body_pct": cfg.body_brightness_pct,
                    "star_pct": cfg.star_brightness_pct,
                },
                "schedule_blocks": [
                    {
                        "start_hhmm": b.start_hhmm,
                        "end_hhmm": b.end_hhmm,
                        "days": b.days,
                        "enabled": b.enabled,
                    }
                    for b in cfg.schedule_blocks
                ],
                "in_window_now": is_within_schedule(now, cfg.schedule_blocks),
                "countdown_until": cfg.countdown_until,
                "programs": [
                    {"id": p.id, "name": p.name, "default_speed": p.default_speed}
                    for p in PROGRAMS.values()
                ],
                "runtime": controller.get_runtime_state(),
            }
        )

    @app.post("/api/mode")
    def api_mode():
        data = request.get_json(force=True, silent=True) or {}
        mode = data.get("mode")
        if mode not in ("manual_on", "manual_off", "auto"):
            return jsonify({"error": "invalid mode"}), 400

        cfg = controller.update_config(lambda c: setattr(c, "mode", mode))
        return jsonify({"ok": True, "mode": cfg.mode})

    @app.post("/api/program")
    def api_program():
        data = request.get_json(force=True, silent=True) or {}
        program_id = data.get("program_id")
        if program_id not in PROGRAMS:
            return jsonify({"error": "invalid program_id"}), 400

        def _mut(c):
            c.program_id = program_id
            if "program_speed" in data:
                c.program_speed = float(data["program_speed"])

        cfg = controller.update_config(_mut)
        return jsonify({"ok": True, "program_id": cfg.program_id, "program_speed": cfg.program_speed})

    @app.post("/api/speed")
    def api_speed():
        data = request.get_json(force=True, silent=True) or {}
        try:
            speed = float(data.get("program_speed"))
        except Exception:
            return jsonify({"error": "invalid program_speed"}), 400
        speed = max(SPEED_MIN, min(SPEED_MAX, speed))
        cfg = controller.update_config(lambda c: setattr(c, "program_speed", speed))
        return jsonify({"ok": True, "program_speed": cfg.program_speed})

    @app.post("/api/countdown")
    def api_countdown():
        data = request.get_json(force=True, silent=True) or {}
        now = datetime.now()

        if data.get("clear"):
            cfg = controller.update_config(lambda c: c.clear_countdown())
            return jsonify({"ok": True, "countdown_until": cfg.countdown_until})

        try:
            minutes = int(data.get("minutes"))
        except Exception:
            return jsonify({"error": "invalid minutes"}), 400
        minutes = max(1, min(24 * 60, minutes))

        def _mut(c):
            c.set_countdown_minutes(minutes, now=now)

        cfg = controller.update_config(_mut)
        return jsonify({"ok": True, "countdown_until": cfg.countdown_until})

    @app.post("/api/schedule")
    def api_schedule():
        data = request.get_json(force=True, silent=True) or {}
        blocks_raw = data.get("blocks")
        # #region agent log
        import json as json_module
        try:
            with open('/tmp/rgbxmastree_debug.log', 'a') as f:
                f.write(json_module.dumps({"location":"app.py:api_schedule:entry","message":"API schedule called","data":{"blocks_raw":blocks_raw},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"B,E"})+'\n')
        except: pass
        # #endregion
        if not isinstance(blocks_raw, list):
            return jsonify({"error": "blocks must be a list"}), 400
        if len(blocks_raw) > MAX_SCHEDULE_BLOCKS:
            return jsonify({"error": f"max {MAX_SCHEDULE_BLOCKS} blocks allowed"}), 400
        if len(blocks_raw) == 0:
            return jsonify({"error": "at least one block required"}), 400

        # Validate each block
        schedule_blocks: list[ScheduleBlock] = []
        for i, b in enumerate(blocks_raw):
            if not isinstance(b, dict):
                return jsonify({"error": f"block {i} must be an object"}), 400
            start_hhmm = b.get("start_hhmm")
            end_hhmm = b.get("end_hhmm")
            if not isinstance(start_hhmm, str) or not isinstance(end_hhmm, str):
                return jsonify({"error": f"block {i}: start_hhmm/end_hhmm required"}), 400
            days = b.get("days")
            if days is not None and not (isinstance(days, list) and all(isinstance(d, int) for d in days)):
                return jsonify({"error": f"block {i}: days must be list[int] or null"}), 400
            enabled = b.get("enabled", True)
            if not isinstance(enabled, bool):
                return jsonify({"error": f"block {i}: enabled must be boolean"}), 400
            schedule_blocks.append(ScheduleBlock(
                start_hhmm=start_hhmm,
                end_hhmm=end_hhmm,
                days=days,
                enabled=enabled,
            ))

        def _mut(c):
            c.schedule_blocks = schedule_blocks

        cfg = controller.update_config(_mut)
        # #region agent log
        import json as json_module
        try:
            with open('/tmp/rgbxmastree_debug.log', 'a') as f:
                f.write(json_module.dumps({"location":"app.py:api_schedule:success","message":"Config updated","data":{"saved_blocks":[{"start_hhmm":b.start_hhmm,"end_hhmm":b.end_hhmm,"days":b.days,"enabled":b.enabled} for b in cfg.schedule_blocks]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"E"})+'\n')
        except: pass
        # #endregion
        return jsonify({
            "ok": True,
            "schedule_blocks": [
                {
                    "start_hhmm": b.start_hhmm,
                    "end_hhmm": b.end_hhmm,
                    "days": b.days,
                    "enabled": b.enabled,
                }
                for b in cfg.schedule_blocks
            ],
        })

    @app.post("/api/brightness")
    def api_brightness():
        data = request.get_json(force=True, silent=True) or {}

        def _parse_pct(key: str) -> int | None:
            if key not in data:
                return None
            try:
                v = int(float(data.get(key)))
            except Exception:
                raise ValueError(f"invalid {key}")
            return max(0, min(100, v))

        try:
            body_pct = _parse_pct("body_pct")
            star_pct = _parse_pct("star_pct")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        def _mut(c):
            if body_pct is not None:
                c.body_brightness_pct = body_pct
            if star_pct is not None:
                c.star_brightness_pct = star_pct

        cfg = controller.update_config(_mut)
        return jsonify(
            {
                "ok": True,
                "brightness": {"body_pct": cfg.body_brightness_pct, "star_pct": cfg.star_brightness_pct},
            }
        )

    @app.teardown_appcontext
    def _teardown(_exc):
        # In production this runs on each request; controller is long-lived.
        # We keep it alive for the life of the process; shutdown handled by atexit.
        return None

    return app


