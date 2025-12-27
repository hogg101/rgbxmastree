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

function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

let speedBounds = { min: 0.1, max: 200.0 };
let speedReady = false;

// Schedule blocks state (editable in UI before saving)
let scheduleBlocks = [];
let savedScheduleBlocks = [];  // Last saved state for comparison
const MAX_BLOCKS = 5;
const DAY_LABELS = ["M", "T", "W", "T", "F", "S", "S"];

// Deep compare two arrays of days (handles null = all days)
function daysEqual(a, b) {
  if (a === null && b === null) return true;
  if (a === null || b === null) return false;
  if (a.length !== b.length) return false;
  return a.every((d, i) => d === b[i]);
}

// Deep compare two schedule block arrays
function blocksEqual(current, saved) {
  if (current.length !== saved.length) return false;
  return current.every((block, i) => {
    const s = saved[i];
    return block.start_hhmm === s.start_hhmm &&
           block.end_hhmm === s.end_hhmm &&
           block.enabled === s.enabled &&
           daysEqual(block.days, s.days);
  });
}

// Check if current blocks differ from saved and update dirty state
function updateDirtyState() {
  const isDirty = !blocksEqual(scheduleBlocks, savedScheduleBlocks);
  renderScheduleBlocks(isDirty);
}

function speedPctToValue(pct, speedMin, speedMax) {
  // Exponential mapping: pct 0..100 -> speedMin..speedMax
  const p = clamp(Number(pct), 0, 100) / 100;
  const min = Number(speedMin);
  const max = Number(speedMax);
  if (!isFinite(min) || !isFinite(max) || min <= 0 || max <= 0 || max <= min) return 1.0;
  return min * Math.pow(max / min, p);
}

function speedValueToPct(speed, speedMin, speedMax) {
  // Inverse mapping: speed -> pct 0..100
  const v = Number(speed);
  const min = Number(speedMin);
  const max = Number(speedMax);
  if (!isFinite(v) || !isFinite(min) || !isFinite(max) || v <= 0 || min <= 0 || max <= 0 || max <= min) return 50;
  const p = Math.log(v / min) / Math.log(max / min);
  return clamp(p * 100, 0, 100);
}

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
  const inWindow = state.in_window_now ? "in schedule" : "out of schedule";
  $("statusLine").textContent = `${modeLabel} • ${running} • ${inWindow} • ${now.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}`;
}

// Schedule blocks UI rendering
function renderScheduleBlocks(isDirty) {
  const container = $("scheduleBlocks");
  container.innerHTML = "";
  
  scheduleBlocks.forEach((block, idx) => {
    const row = document.createElement("div");
    row.className = "schedule-block";
    
    // Enable toggle
    const enableBtn = document.createElement("button");
    enableBtn.type = "button";
    enableBtn.className = "btn btn-enable" + (block.enabled ? " active" : "");
    enableBtn.textContent = block.enabled ? "On" : "Off";
    enableBtn.addEventListener("click", () => {
      block.enabled = !block.enabled;
      updateDirtyState();
    });
    
    // Time inputs
    const startInput = document.createElement("input");
    startInput.type = "time";
    startInput.className = "time-input";
    startInput.value = block.start_hhmm;
    startInput.addEventListener("change", (e) => {
      block.start_hhmm = e.target.value;
      updateDirtyState();
    });
    
    const endInput = document.createElement("input");
    endInput.type = "time";
    endInput.className = "time-input";
    endInput.value = block.end_hhmm;
    endInput.addEventListener("change", (e) => {
      block.end_hhmm = e.target.value;
      updateDirtyState();
    });
    
    // Days chips
    const daysContainer = document.createElement("div");
    daysContainer.className = "days-chips";
    DAY_LABELS.forEach((label, dayIdx) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "day-chip";
      const isActive = block.days === null || block.days.includes(dayIdx);
      if (isActive) chip.classList.add("active");
      chip.textContent = label;
      chip.addEventListener("click", () => {
        if (block.days === null) {
          // Was "all days", now exclude this one
          block.days = [0, 1, 2, 3, 4, 5, 6].filter(d => d !== dayIdx);
        } else if (block.days.includes(dayIdx)) {
          // Remove this day
          block.days = block.days.filter(d => d !== dayIdx);
          // If all days are selected again, use null
          if (block.days.length === 0) {
            block.days = [];
          }
        } else {
          // Add this day
          block.days = [...block.days, dayIdx].sort((a, b) => a - b);
          // If all 7 days selected, use null
          if (block.days.length === 7) {
            block.days = null;
          }
        }
        updateDirtyState();
      });
      daysContainer.appendChild(chip);
    });
    
    // Delete button
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "btn btn-delete";
    deleteBtn.textContent = "×";
    deleteBtn.disabled = scheduleBlocks.length <= 1;
    deleteBtn.addEventListener("click", () => {
      if (scheduleBlocks.length > 1) {
        scheduleBlocks.splice(idx, 1);
        updateDirtyState();
      }
    });
    
    row.appendChild(enableBtn);
    row.appendChild(startInput);
    row.appendChild(endInput);
    row.appendChild(daysContainer);
    row.appendChild(deleteBtn);
    
    container.appendChild(row);
  });
  
  // Update add button state
  const addBtn = $("addBlock");
  if (addBtn) {
    addBtn.disabled = scheduleBlocks.length >= MAX_BLOCKS;
  }
  
  // Toggle dirty state on save button
  const saveBtn = $("saveSchedule");
  if (saveBtn) {
    if (isDirty) {
      saveBtn.classList.add("btn-dirty");
    } else {
      saveBtn.classList.remove("btn-dirty");
    }
  }
}

function addScheduleBlock() {
  if (scheduleBlocks.length >= MAX_BLOCKS) return;
  scheduleBlocks.push({
    start_hhmm: "07:30",
    end_hhmm: "23:00",
    days: null,
    enabled: true,
  });
  updateDirtyState();
}

async function saveScheduleBlocks() {
  try {
    await apiPost("/api/schedule", { blocks: scheduleBlocks });
    // Update saved state to match current after successful save
    savedScheduleBlocks = JSON.parse(JSON.stringify(scheduleBlocks));
    renderScheduleBlocks(false);  // Not dirty anymore
    await refresh();
  } catch (err) {
    alert(err.message);
  }
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
  const speedMin = state.program_speed_min ?? speedBounds.min;
  const speedMax = state.program_speed_max ?? speedBounds.max;
  speedBounds = { min: speedMin, max: speedMax };
  const speed = Number(state.program_speed ?? 1.0);
  const pct = speedValueToPct(speed, speedMin, speedMax);
  $("speedRange").value = String(Math.round(pct));
  $("speedLabel").textContent = `Speed: ${Math.round(pct)}% (${speed.toFixed(2)})`;
  $("speedRange").disabled = false;
  speedReady = true;

  // brightness
  const bodyPct = state.brightness?.body_pct ?? 50;
  const starPct = state.brightness?.star_pct ?? 50;
  if ($("bodyBrightnessRange")) $("bodyBrightnessRange").value = String(bodyPct);
  if ($("starBrightnessRange")) $("starBrightnessRange").value = String(starPct);
  setBrightnessLabels(bodyPct, starPct);

  // schedule blocks - only update from server if user hasn't made local changes
  const serverBlocks = (state.schedule_blocks || []).map(b => ({
    start_hhmm: b.start_hhmm || "07:30",
    end_hhmm: b.end_hhmm || "23:00",
    days: b.days,
    enabled: b.enabled !== false,
  }));
  const hasServerBlocks = serverBlocks.length > 0;
  const defaultBlocks = [{ start_hhmm: "07:30", end_hhmm: "23:00", days: null, enabled: true }];
  
  // Check if user has unsaved local changes
  const isDirty = !blocksEqual(scheduleBlocks, savedScheduleBlocks);
  
  if (!isDirty) {
    // No unsaved changes - sync with server
    scheduleBlocks = hasServerBlocks ? serverBlocks : defaultBlocks;
    savedScheduleBlocks = JSON.parse(JSON.stringify(scheduleBlocks));
    renderScheduleBlocks(false);
  }
  $("scheduleHint").textContent = state.in_window_now 
    ? "Currently within schedule window." 
    : "Currently outside schedule window.";

  // countdown
  $("countdownLine").textContent = fmtCountdown(state.countdown_until);

  setStatusLine(state);
}

function wire() {
  $("refreshBtn").addEventListener("click", () => refresh().catch(err => alert(err.message)));
  $("speedRange").disabled = true;
  if ($("speedLabel")) $("speedLabel").textContent = "Speed: loading…";

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
    if (!speedReady || $("speedRange").disabled) return;
    const speedMin = speedBounds.min;
    const speedMax = speedBounds.max;
    const pct = Number(e.target.value);
    const speed = speedPctToValue(pct, speedMin, speedMax);
    $("speedLabel").textContent = `Speed: ${Math.round(pct)}% (${speed.toFixed(2)})`;
  });
  $("speedRange").addEventListener("change", async (e) => {
    if (!speedReady || $("speedRange").disabled) return;
    const speedMin = speedBounds.min;
    const speedMax = speedBounds.max;
    const pct = Number(e.target.value);
    const speed = speedPctToValue(pct, speedMin, speedMax);
    await apiPost("/api/speed", { program_speed: speed });
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

  // Schedule block controls
  $("addBlock").addEventListener("click", addScheduleBlock);
  $("saveSchedule").addEventListener("click", saveScheduleBlocks);
}

wire();
refresh().catch(err => alert(err.message));
setInterval(() => refresh().catch(() => {}), 5000);
