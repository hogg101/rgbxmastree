from __future__ import annotations

import threading
import time
from dataclasses import replace
from datetime import datetime
from typing import Callable

from rgbxmastree.config import AppConfig, load_config, save_config
from rgbxmastree.hardware.tree import RGBXmasTree
from rgbxmastree.programs import PROGRAMS
from rgbxmastree.scheduler import is_within_schedule


class TreeController:
    """
    Owns the hardware driver, runs one program at a time, and enforces on/off policy.
    """

    def __init__(self, config_path: str):
        self._config_path = config_path
        self._lock = threading.RLock()
        self._cfg = load_config(config_path)

        self._tree: RGBXmasTree | None = None
        self._runner_thread: threading.Thread | None = None
        self._runner_stop = threading.Event()
        self._runner_program_id: str | None = None

        self._supervisor_stop = threading.Event()
        self._supervisor_thread = threading.Thread(target=self._supervise_loop, name="rgbxmastree-supervisor", daemon=True)
        self._supervisor_thread.start()

    # ----- config/state -----

    def get_config(self) -> AppConfig:
        with self._lock:
            return replace(self._cfg)

    def get_runtime_state(self) -> dict:
        with self._lock:
            runner_alive = bool(self._runner_thread and self._runner_thread.is_alive())
            return {
                "program_running": runner_alive,
                "program_id": self._runner_program_id,
            }

    def update_config(self, mutate: Callable[[AppConfig], None]) -> AppConfig:
        with self._lock:
            cfg = replace(self._cfg)
            mutate(cfg)
            self._cfg = cfg
            save_config(self._config_path, cfg)
            return replace(cfg)

    # ----- policy -----

    def _desired_on(self, now: datetime, cfg: AppConfig) -> bool:
        if cfg.mode == "manual_on":
            return True
        if cfg.mode == "manual_off":
            return False

        # auto mode:
        in_window = is_within_schedule(now, cfg.schedule)
        until = cfg.countdown_until_dt()
        countdown_on = bool(until and until > now)
        return in_window or countdown_on

    # ----- hardware/program control -----

    def _ensure_tree(self) -> RGBXmasTree:
        if self._tree is None:
            self._tree = RGBXmasTree()
        return self._tree

    def _start_program(self, program_id: str, speed: float) -> None:
        spec = PROGRAMS.get(program_id)
        if spec is None:
            spec = PROGRAMS["rgb_cycle"]
            program_id = spec.id

        tree = self._ensure_tree()

        self._runner_stop.clear()
        self._runner_program_id = program_id

        def _run():
            try:
                spec.runner(tree, self._runner_stop, speed)
            except Exception:
                # If a program crashes, supervisor may restart it if we still want "on".
                pass

        self._runner_thread = threading.Thread(target=_run, name=f"rgbxmastree-program-{program_id}", daemon=True)
        self._runner_thread.start()

    def _stop_program(self) -> None:
        self._runner_stop.set()
        t = self._runner_thread
        if t is not None and t.is_alive():
            t.join(timeout=2.0)
        self._runner_thread = None
        self._runner_program_id = None
        self._runner_stop.clear()

    def _power_off(self) -> None:
        if self._tree is None:
            return
        try:
            self._tree.off()
        except Exception:
            pass

    def _supervise_loop(self) -> None:
        """
        Background loop that enforces desired power state and keeps the program running.
        """
        while not self._supervisor_stop.is_set():
            with self._lock:
                cfg = self._cfg
            now = datetime.now()
            want_on = self._desired_on(now, cfg)

            with self._lock:
                if not want_on:
                    self._stop_program()
                    self._power_off()
                else:
                    # Ensure correct program is running
                    if self._runner_thread is None or not self._runner_thread.is_alive():
                        self._start_program(cfg.program_id, cfg.program_speed)
                    elif self._runner_program_id != cfg.program_id:
                        self._stop_program()
                        self._start_program(cfg.program_id, cfg.program_speed)

            time.sleep(0.25)

    def close(self) -> None:
        self._supervisor_stop.set()
        if self._supervisor_thread.is_alive():
            self._supervisor_thread.join(timeout=2.0)
        with self._lock:
            self._stop_program()
            self._power_off()
            try:
                if self._tree is not None:
                    self._tree.close()
            except Exception:
                pass
            self._tree = None


