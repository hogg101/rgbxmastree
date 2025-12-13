async function apiGet(path) {
  const res = await fetch(path, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`GET ${path} ${res.status}`);
  return await res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} ${res.status}: ${text}`);
  }
  return await res.json();
}

function $(id) { return document.getElementById(id); }

function setBrightnessLabels(bodyPct, starPct) {
  if ($("bodyBrightnessLabel")) $("bodyBrightnessLabel").textContent = `Body: ${Number(bodyPct).toFixed(0)}%`;
  if ($("starBrightnessLabel")) $("starBrightnessLabel").textContent = `Star: ${Number(starPct).toFixed(0)}%`;
}

function setActiveMode(mode) {
  const on = $("modeOn"), off = $("modeOff"), auto = $("modeAuto");
  [on, off, auto].forEach(b => b.classList.remove("active", "good", "danger"));
  if (mode === "manual_on") { on.classList.add("active", "good"); }
  if (mode === "manual_off") { off.classList.add("active", "danger"); }
  if (mode === "auto") { auto.classList.add("active"); }
}

function fmtCountdown(untilIso) {
  if (!untilIso) return "No countdown set.";
  const until = new Date(untilIso);
  const now = new Date();
  const ms = until.getTime() - now.getTime();
  if (ms <= 0) return "Countdown expired.";
  const mins = Math.ceil(ms / 60000);
  if (mins < 60) return `On for ~${mins} min more (until ${until.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}).`;
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return `On for ~${hrs}h ${rem}m more (until ${until.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}).`;
}

function setStatusLine(state) {
  const now = new Date(state.now);
  const modeLabel = state.mode === "manual_on" ? "On" : state.mode === "manual_off" ? "Off" : "Auto";
  const running = state.runtime?.program_running ? `Running: ${state.runtime.program_id ?? ""}` : "Stopped";
  const inWindow = state.schedule?.in_window_now ? "in schedule" : "out of schedule";
  $("statusLine").textContent = `${modeLabel} • ${running} • ${inWindow} • ${now.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}`;
}

async function refresh() {
  const state = await apiGet("/api/state");

  // programs
  const sel = $("programSelect");
  if (sel.options.length === 0) {
    for (const p of state.programs) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name;
      sel.appendChild(opt);
    }
  }
  sel.value = state.program_id;

  // mode buttons
  setActiveMode(state.mode);

  // speed
  $("speedRange").value = String(state.program_speed ?? 1.0);
  $("speedLabel").textContent = `Speed: ${Number(state.program_speed ?? 1.0).toFixed(1)}`;

  // brightness
  const bodyPct = state.brightness?.body_pct ?? 50;
  const starPct = state.brightness?.star_pct ?? 50;
  if ($("bodyBrightnessRange")) $("bodyBrightnessRange").value = String(bodyPct);
  if ($("starBrightnessRange")) $("starBrightnessRange").value = String(starPct);
  setBrightnessLabels(bodyPct, starPct);

  // schedule
  $("startTime").value = state.schedule?.start_hhmm ?? "07:30";
  $("endTime").value = state.schedule?.end_hhmm ?? "23:00";
  $("scheduleHint").textContent = state.schedule?.in_window_now ? "Currently within schedule window." : "Currently outside schedule window.";

  // countdown
  $("countdownLine").textContent = fmtCountdown(state.countdown_until);

  setStatusLine(state);
}

function wire() {
  $("refreshBtn").addEventListener("click", () => refresh().catch(err => alert(err.message)));

  $("modeOn").addEventListener("click", async () => {
    await apiPost("/api/mode", { mode: "manual_on" });
    await refresh();
  });
  $("modeOff").addEventListener("click", async () => {
    await apiPost("/api/mode", { mode: "manual_off" });
    await refresh();
  });
  $("modeAuto").addEventListener("click", async () => {
    await apiPost("/api/mode", { mode: "auto" });
    await refresh();
  });

  $("programSelect").addEventListener("change", async (e) => {
    await apiPost("/api/program", { program_id: e.target.value });
    await refresh();
  });

  $("speedRange").addEventListener("input", (e) => {
    $("speedLabel").textContent = `Speed: ${Number(e.target.value).toFixed(1)}`;
  });
  $("speedRange").addEventListener("change", async (e) => {
    await apiPost("/api/speed", { program_speed: Number(e.target.value) });
    await refresh();
  });

  // brightness sliders
  if ($("bodyBrightnessRange")) {
    $("bodyBrightnessRange").addEventListener("input", (e) => {
      const body = Number(e.target.value);
      const star = Number($("starBrightnessRange")?.value ?? 50);
      setBrightnessLabels(body, star);
    });
    $("bodyBrightnessRange").addEventListener("change", async (e) => {
      await apiPost("/api/brightness", { body_pct: Number(e.target.value) });
      await refresh();
    });
  }
  if ($("starBrightnessRange")) {
    $("starBrightnessRange").addEventListener("input", (e) => {
      const star = Number(e.target.value);
      const body = Number($("bodyBrightnessRange")?.value ?? 50);
      setBrightnessLabels(body, star);
    });
    $("starBrightnessRange").addEventListener("change", async (e) => {
      await apiPost("/api/brightness", { star_pct: Number(e.target.value) });
      await refresh();
    });
  }

  for (const btn of document.querySelectorAll("button[data-min]")) {
    btn.addEventListener("click", async () => {
      const minutes = Number(btn.getAttribute("data-min"));
      await apiPost("/api/countdown", { minutes });
      await refresh();
    });
  }

  $("countdownClear").addEventListener("click", async () => {
    await apiPost("/api/countdown", { clear: true });
    await refresh();
  });

  $("saveSchedule").addEventListener("click", async () => {
    const start_hhmm = $("startTime").value;
    const end_hhmm = $("endTime").value;
    await apiPost("/api/schedule", { start_hhmm, end_hhmm, days: null });
    await refresh();
  });
}

wire();
refresh().catch(err => alert(err.message));
setInterval(() => refresh().catch(() => {}), 5000);


