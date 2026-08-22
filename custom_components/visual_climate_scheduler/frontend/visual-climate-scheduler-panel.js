class VisualClimateSchedulerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._configuration = null;
    this._roomId = null;
    this._days = null;
    this._sourceDay = null;
    this._selectedDays = new Set();
    this._selectedPeriod = null;
    this._drag = null;
    this._view = "schedule";
    this._quick = { rooms: [] };
    this._quickSelected = new Set();
    this._quickDuration = "2h";
    this._quickAction = null;
    this._quickExactTarget = "";
    this._message = "";
    this.shadowRoot.addEventListener("click", (event) => this._onClick(event));
    this.shadowRoot.addEventListener("change", (event) => this._onChange(event));
    this.shadowRoot.addEventListener("pointerdown", (event) => this._onPointerDown(event));
    this.shadowRoot.addEventListener("pointermove", (event) => this._onPointerMove(event));
    this.shadowRoot.addEventListener("pointerup", (event) => this._onPointerUp(event));
    this.shadowRoot.addEventListener("pointercancel", (event) => this._onPointerUp(event));
  }

  set hass(hass) {
    const firstConnection = !this._hass;
    this._hass = hass;
    if (firstConnection) this._load();
  }

  get hass() {
    return this._hass;
  }

  async _load() {
    if (!this._hass) return;
    try {
      this._configuration = await this._hass.callWS({
        type: "visual_climate_scheduler/get_configuration",
      });
      if (!this._roomId || !this._configuration.rooms[this._roomId]) {
        this._roomId = Object.keys(this._configuration.rooms)[0] || null;
      }
      this._loadRoom();
      await this._loadQuick(false);
    } catch (error) {
      this._message = `Could not load schedules: ${error.message || error}`;
      this._render();
    }
  }

  _loadRoom(clearMessage = true) {
    const room = this._configuration?.rooms[this._roomId];
    this._days = room ? structuredClone(room.days) : null;
    this._sourceDay = this._days ? Object.keys(this._days)[0] : null;
    this._selectedDays = new Set();
    this._selectedPeriod = null;
    if (clearMessage) this._message = "";
    this._render();
  }

  async _loadQuick(render = true) {
    try { this._quick = await this._hass.callWS({ type: "visual_climate_scheduler/get_quick_change" }); }
    catch (error) { this._message = `Could not load Quick Change: ${error.message || error}`; }
    if (render) this._render();
  }

  _onChange(event) {
    const target = event.target;
    if (target.dataset.action === "room") {
      this._roomId = target.value;
      this._loadRoom();
      return;
    }
    if (target.dataset.action === "source-day") {
      this._sourceDay = target.value;
      this._render();
      return;
    }
    if (target.dataset.action === "target-day") {
      if (target.checked) this._selectedDays.add(target.value);
      else this._selectedDays.delete(target.value);
      this._render();
      return;
    }
    if (target.dataset.action === "quick-room") {
      if (target.checked) this._quickSelected.add(target.value); else this._quickSelected.delete(target.value);
      this._syncQuickExactTarget();
      this._render(); return;
    }
    if (target.dataset.action === "quick-duration") { this._quickDuration = target.value; return; }
    if (target.dataset.action === "quick-temperature") { this._quickExactTarget = target.value; this._quickAction = { operation: "temperature", value: Number(target.value) }; return; }
    const { day, index, field } = target.dataset;
    if (!day || index === undefined || !field) return;
    const period = this._days[day][Number(index)];
    period[field] = field === "temperature" ? Number(target.value) : target.value;
    if (field === "name" && !period.friendly_name) period.friendly_name = this._slug(target.value);
  }

  async _onClick(event) {
    const button = event.target.closest("button");
    if (!button || button.disabled) return;
    const { action, day, index } = button.dataset;
    if (action === "view") { this._view = button.dataset.view; await this._loadQuick(false); this._render(); return; }
    if (action === "quick-all") { this._quickSelected = new Set(this._quick.rooms.map((room) => room.id)); this._syncQuickExactTarget(); this._render(); return; }
    if (action === "quick-delta") {
      const step = Number(button.dataset.value);
      if (this._quickAction?.operation === "delta") this._quickAction = { operation: "delta", value: this._quickAction.value + step };
      else if (this._quickAction?.operation === "temperature") this._quickAction = { operation: "temperature", value: this._quickAction.value + step };
      else this._quickAction = { operation: "delta", value: step };
      this._syncQuickExactTarget();
      this._render(); return;
    }
    if (action === "quick-apply") { await this._applyQuick(); return; }
    if (action === "quick-cancel") { await this._cancelQuick(button.dataset.roomId); return; }
    if (action === "timeline-point") {
      this._selectedPeriod = { day, index: Number(index) };
      this._render();
      return;
    }
    if (action === "add") this._addPeriod(day);
    if (action === "remove") this._days[day].splice(Number(index), 1);
    if (action === "apply") this._applyToSelectedDays();
    if (action === "save") { await this._save(); return; }
    this._render();
  }

  async _applyQuick() {
    if (!this._quickSelected.size) { this._message = "Choose one or more rooms/zones, or select Whole house."; this._render(); return; }
    if (!this._quickAction || !Number.isFinite(this._quickAction.value)) { this._message = "Choose +/− adjustment or enter an exact target temperature."; this._render(); return; }
    try {
      this._quick = await this._hass.callWS({ type: "visual_climate_scheduler/set_temporary_override", room_ids: [...this._quickSelected], duration: this._quickDuration, ...this._quickAction });
      this._quickAction = null;
      this._syncQuickExactTarget();
      this._message = "Temporary hold applied. It will automatically return to the schedule.";
    } catch (error) { this._message = `Not applied: ${error.message || error}`; }
    this._render();
  }

  async _cancelQuick(roomId) {
    this._quick = await this._hass.callWS({ type: "visual_climate_scheduler/clear_temporary_override", room_id: roomId });
    this._message = "Temporary hold cancelled; the scheduled target has resumed.";
    this._render();
  }

  _quickReferenceTarget() {
    if (this._quickSelected.size !== 1) return null;
    const room = this._quick.rooms.find((candidate) => this._quickSelected.has(candidate.id));
    return room?.effective_temperature ?? room?.scheduled_temperature ?? null;
  }

  _syncQuickExactTarget() {
    const reference = this._quickReferenceTarget();
    if (this._quickAction?.operation === "temperature") this._quickExactTarget = this._quickAction.value;
    else if (this._quickAction?.operation === "delta") this._quickExactTarget = reference === null ? "" : reference + this._quickAction.value;
    else this._quickExactTarget = reference ?? "";
  }

  _temperatureUnit() {
    return this._hass?.config?.unit_system?.temperature || "°C";
  }

  _temperatureBounds() {
    return this._temperatureUnit() === "°F"
      ? { defaultValue: 68 }
      : { defaultValue: 20 };
  }

  _formatTemperature(value) {
    return value === null || value === undefined || value === "" ? "—" : `${value}${this._temperatureUnit()}`;
  }

  _addPeriod(day) {
    if (this._days[day].length >= 4) return;
    const number = this._days[day].length + 1;
    const name = `Period ${number}`;
    this._days[day].push({
      id: `period-${Date.now()}-${number}`,
      friendly_name: this._slug(name),
      name,
      time: "12:00",
      temperature: this._temperatureBounds().defaultValue,
    });
  }

  _timeToMinutes(value) {
    const [hours, minutes] = value.split(":").map(Number);
    return (hours * 60) + minutes;
  }

  _timeFromMinutes(value) {
    const minutes = Math.max(0, Math.min(1439, value));
    return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
  }

  _temperatureRange(periods) {
    const bounds = this._temperatureBounds();
    const values = periods.map((period) => Number(period.temperature));
    const middle = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : bounds.defaultValue;
    let minimum = Math.floor(Math.min(...values, middle) - 2);
    let maximum = Math.ceil(Math.max(...values, middle) + 2);
    if (maximum - minimum < 6) {
      minimum = Math.floor(middle - 3);
      maximum = minimum + 6;
    }
    return { minimum, maximum };
  }

  _renderTimeline(day) {
    const periods = this._days[day];
    const { minimum, maximum } = this._temperatureRange(periods);
    const ordered = periods
      .map((period, index) => ({ period, index }))
      .sort((left, right) => left.period.time.localeCompare(right.period.time));
    const coordinates = ordered.map(({ period, index }) => ({
      index,
      time: this._timeToMinutes(period.time),
      x: (this._timeToMinutes(period.time) / 1440) * 100,
      y: ((maximum - Number(period.temperature)) / (maximum - minimum)) * 100,
      temperature: Number(period.temperature),
    }));
    let path = "";
    if (coordinates.length) {
      path = `M 0 ${coordinates[0].y.toFixed(2)}`;
      for (let index = 0; index < coordinates.length; index += 1) {
        const point = coordinates[index];
        path += ` H ${point.x.toFixed(2)}`;
        if (coordinates[index + 1]) path += ` V ${coordinates[index + 1].y.toFixed(2)}`;
      }
      path += ` H 100`;
    }
    const points = coordinates.map(({ index, x, y, temperature }) => `
      <button class="timeline-point" data-action="timeline-point" data-day="${day}" data-index="${index}" style="left:${x}%;top:${y}%" title="Drag to change time and target" aria-label="${this._escape(day)} ${this._escape(periods[index].name)}: ${periods[index].time}, ${this._formatTemperature(temperature)}">${this._formatTemperature(temperature)}</button>`).join("");
    return `<div class="visual-editor"><div class="timeline-title">Visual editor <span>Drag a point: left/right changes time; up/down changes target.</span></div><div class="timeline-shell"><div class="temperature-scale"><span>${this._formatTemperature(maximum)}</span><span>${this._formatTemperature(Math.round((minimum + maximum) / 2))}</span><span>${this._formatTemperature(minimum)}</span></div><div><div class="timeline-plot" data-timeline-day="${day}" data-temp-min="${minimum}" data-temp-max="${maximum}"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path d="${path}"/></svg>${points}</div><div class="time-scale"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div></div></div></div>`;
  }

  _onPointerDown(event) {
    const point = event.target.closest(".timeline-point");
    if (!point || !this._days) return;
    event.preventDefault();
    this._selectedPeriod = { day: point.dataset.day, index: Number(point.dataset.index) };
    this._drag = {
      point,
      day: point.dataset.day,
      index: Number(point.dataset.index),
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      moved: false,
    };
    point.setPointerCapture(event.pointerId);
  }

  _onPointerMove(event) {
    if (!this._drag || this._drag.pointerId !== event.pointerId) return;
    if (!this._drag.moved && Math.hypot(event.clientX - this._drag.startX, event.clientY - this._drag.startY) < 4) return;
    this._drag.moved = true;
    this._updateDrag(event);
  }

  _onPointerUp(event) {
    if (!this._drag || this._drag.pointerId !== event.pointerId) return;
    if (this._drag.moved) this._updateDrag(event);
    this._drag.point.releasePointerCapture?.(event.pointerId);
    const moved = this._drag.moved;
    this._drag = null;
    if (moved) this._render();
  }

  _updateDrag(event) {
    const { day, index, point } = this._drag;
    const plot = this.shadowRoot.querySelector(`[data-timeline-day="${day}"]`);
    if (!plot) return;
    const bounds = plot.getBoundingClientRect();
    const horizontal = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
    const vertical = Math.max(0, Math.min(1, (event.clientY - bounds.top) / bounds.height));
    const period = this._days[day][index];
    const minutes = Math.round((horizontal * 1440) / 15) * 15;
    const minimum = Number(plot.dataset.tempMin);
    const maximum = Number(plot.dataset.tempMax);
    period.time = this._timeFromMinutes(minutes);
    period.temperature = Math.round((maximum - (vertical * (maximum - minimum))) * 2) / 2;
    point.style.left = `${(minutes / 1440) * 100}%`;
    point.style.top = `${((maximum - period.temperature) / (maximum - minimum)) * 100}%`;
    point.textContent = this._formatTemperature(period.temperature);
    const timeField = this.shadowRoot.querySelector(`input[data-day="${day}"][data-index="${index}"][data-field="time"]`);
    const temperatureField = this.shadowRoot.querySelector(`input[data-day="${day}"][data-index="${index}"][data-field="temperature"]`);
    if (timeField) timeField.value = period.time;
    if (temperatureField) temperatureField.value = period.temperature;
  }

  _applyToSelectedDays() {
    const targetDays = [...this._selectedDays].filter((day) => day !== this._sourceDay);
    if (!this._sourceDay || !targetDays.length) {
      this._message = "Choose a source day and tick at least one different day to apply it to.";
      return;
    }
    for (const day of targetDays) this._days[day] = structuredClone(this._days[this._sourceDay]);
    this._message = `${this._sourceDay[0].toUpperCase()}${this._sourceDay.slice(1)} applied to ${targetDays.join(", ")}. Save schedule to keep it.`;
  }

  async _save() {
    for (const periods of Object.values(this._days)) {
      periods.sort((left, right) => left.time.localeCompare(right.time));
    }
    try {
      const configuration = await this._hass.callWS({
        type: "visual_climate_scheduler/update_room_days",
        room_id: this._roomId,
        days: this._days,
      });
      this._configuration = configuration;
      this._message = "Saved. The running schedule has been updated.";
      this._loadRoom(false);
    } catch (error) {
      this._message = `Not saved: ${error.message || error}`;
    }
    this._render();
  }

  _slug(value) {
    return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "period";
  }

  _escape(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
    })[character]);
  }

  _renderPeriods(day) {
    const periods = this._days[day];
    const rows = periods.map((period, index) => `
      <div class="period-row ${this._selectedPeriod?.day === day && this._selectedPeriod?.index === index ? "selected" : ""}">
        <input aria-label="${day} period name" data-day="${day}" data-index="${index}" data-field="name" value="${this._escape(period.name)}">
        <input aria-label="${day} period time" type="time" data-day="${day}" data-index="${index}" data-field="time" value="${this._escape(period.time)}">
        <input aria-label="${day} period temperature" type="number" step="0.1" data-day="${day}" data-index="${index}" data-field="temperature" value="${this._escape(period.temperature)}">
        <span>${this._temperatureUnit()}</span><button class="icon" data-action="remove" data-day="${day}" data-index="${index}" title="Remove period">×</button>
      </div>`).join("");
    return `<section class="day-card"><div class="day-heading"><h2>${day}</h2><label><input type="radio" name="source-day" data-action="source-day" value="${day}" ${this._sourceDay === day ? "checked" : ""}> Source</label><label><input type="checkbox" data-action="target-day" value="${day}" ${this._selectedDays.has(day) ? "checked" : ""}> Apply here</label></div>${this._renderTimeline(day)}<div class="labels"><span>Name</span><span>Time</span><span>Target</span></div>${rows || '<p class="empty">No periods yet.</p>'}<button class="secondary" data-action="add" data-day="${day}" ${periods.length >= 4 ? "disabled" : ""}>+ Add period</button></section>`;
  }

  _renderQuick() {
    const rooms = this._quick.rooms || [];
    const cards = rooms.map((room) => `<label class="quick-room"><input type="checkbox" data-action="quick-room" value="${this._escape(room.id)}" ${this._quickSelected.has(room.id) ? "checked" : ""}><span><b>${this._escape(room.name)}</b><small>${room.override ? `Holding ${this._formatTemperature(room.override.temperature)} until ${new Date(room.override.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : `Scheduled ${this._formatTemperature(room.scheduled_temperature)}`}</small></span>${room.override ? `<button data-action="quick-cancel" data-room-id="${this._escape(room.id)}">Cancel hold</button>` : ""}</label>`).join("");
    const unit = this._temperatureUnit();
    return `<section class="quick-page"><div class="quick-header"><div><h2>Quick Change</h2><p class="subtitle">Temporary changes only. Saved weekly schedules are not edited.</p></div><button class="secondary small" data-action="quick-all">Whole house</button></div><div class="quick-rooms">${cards || '<p class="empty">No rooms or zones configured.</p>'}</div><section class="quick-controls"><h2>Change</h2><div class="quick-actions"><button data-action="quick-delta" data-value="-1">−1 ${unit}</button><button data-action="quick-delta" data-value="1">+1 ${unit}</button><label>Exact target (${unit}) <input data-action="quick-temperature" type="number" step="0.5" placeholder="${this._temperatureBounds().defaultValue}" value="${this._escape(this._quickExactTarget)}"></label></div><div class="durations"><label><input type="radio" name="quick-duration" data-action="quick-duration" value="2h" ${this._quickDuration === "2h" ? "checked" : ""}> 2 hours</label><label><input type="radio" name="quick-duration" data-action="quick-duration" value="4h" ${this._quickDuration === "4h" ? "checked" : ""}> 4 hours</label><label><input type="radio" name="quick-duration" data-action="quick-duration" value="next_change" ${this._quickDuration === "next_change" ? "checked" : ""}> Until next change</label></div><button data-action="quick-apply">Apply temporary hold</button></section></section>`;
  }

  _render() {
    const rooms = this._configuration?.rooms || {};
    const brandIconUrl = this._hass?.hassUrl?.("/api/brands/integration/visual_climate_scheduler/icon.png") || "/api/brands/integration/visual_climate_scheduler/icon.png";
    const options = Object.entries(rooms).map(([id, room]) => `<option value="${this._escape(id)}" ${id === this._roomId ? "selected" : ""}>${this._escape(room.name)} · ${room.climate_entity_ids.length} thermostat${room.climate_entity_ids.length === 1 ? "" : "s"}</option>`).join("");
    const editor = this._days ? `<div class="week">${Object.keys(this._days).map((day) => this._renderPeriods(day)).join("")}</div>` : `<div class="blank"><h2>No rooms or zones configured</h2><p>Open the integration’s Configure menu and add a room or zone before creating schedules.</p></div>`;
    const content = this._view === "quick" ? this._renderQuick() : `${editor}<div class="advanced"><h2>Apply schedule</h2><p class="subtitle">Choose one Source day, tick Apply here on the destination days, then save.</p><button data-action="apply" ${this._days ? "" : "disabled"}>Apply to selected days</button><button data-action="view" data-view="quick">Quick Change</button><button data-action="save" ${this._days ? "" : "disabled"}>Save schedule</button></div>`;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; min-height:100%; background:var(--primary-background-color); color:var(--primary-text-color); font-family:var(--primary-font-family, sans-serif); }
        main { max-width:1500px; margin:0 auto; padding:28px; }
        header { display:flex; justify-content:space-between; align-items:flex-end; gap:20px; flex-wrap:wrap; margin-bottom:22px; }.title { display:flex; align-items:center; gap:12px; }.brand-icon { width:46px; height:46px; object-fit:contain; flex:none; }
        h1 { margin:0; font-size:30px; } h2 { margin:0 0 12px; font-size:17px; text-transform:capitalize; }
        .subtitle, .empty { color:var(--secondary-text-color); margin:6px 0 0; }
        select, input { box-sizing:border-box; min-height:38px; border:1px solid var(--divider-color); border-radius:7px; background:var(--card-background-color); color:var(--primary-text-color); padding:6px 8px; font:inherit; }
        select { min-width:290px; } button { border:0; border-radius:7px; min-height:38px; padding:0 14px; background:var(--primary-color); color:var(--text-primary-color); font:inherit; cursor:pointer; } button.secondary { background:var(--secondary-background-color); color:var(--primary-text-color); width:100%; margin-top:10px; } button:disabled { opacity:.48; cursor:not-allowed; } button.icon { min-width:32px; padding:0; background:transparent; color:var(--error-color); font-size:24px; }
        .notice { margin:0 0 18px; padding:12px 14px; border-radius:8px; background:var(--info-color, #2196f3); color:white; }
        .week { display:grid; grid-template-columns:repeat(auto-fit, minmax(310px, 1fr)); gap:16px; }
        .day-card, .blank, .advanced { background:var(--card-background-color); box-shadow:var(--ha-card-box-shadow, 0 1px 3px #0002); border-radius:12px; padding:18px; }.day-heading { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px; }.day-heading h2 { margin:0 auto 0 0; }.day-heading label { display:flex; align-items:center; gap:4px; color:var(--secondary-text-color); font-size:13px; white-space:nowrap; }.day-heading input { min-height:auto; }
        .visual-editor { margin:0 0 14px; }.timeline-title { display:flex; justify-content:space-between; gap:8px; align-items:baseline; color:var(--primary-text-color); font-size:13px; font-weight:700; }.timeline-title span { color:var(--secondary-text-color); font-size:11px; font-weight:400; text-align:right; }.timeline-shell { display:grid; grid-template-columns:30px 1fr; gap:6px; margin-top:8px; }.temperature-scale { height:130px; display:flex; flex-direction:column; justify-content:space-between; align-items:flex-end; color:var(--secondary-text-color); font-size:10px; padding:1px 0; }.timeline-plot { height:130px; position:relative; overflow:visible; border-left:1px solid var(--divider-color); border-bottom:1px solid var(--divider-color); background:repeating-linear-gradient(90deg, transparent 0, transparent calc(25% - 1px), var(--divider-color) calc(25% - 1px), var(--divider-color) 25%), repeating-linear-gradient(0deg, transparent 0, transparent calc(25% - 1px), var(--divider-color) calc(25% - 1px), var(--divider-color) 25%); }.timeline-plot svg { position:absolute; inset:0; width:100%; height:100%; overflow:visible; pointer-events:none; }.timeline-plot path { fill:none; stroke:var(--primary-color); stroke-width:2; vector-effect:non-scaling-stroke; }.timeline-point { position:absolute; transform:translate(-50%, -50%); z-index:2; width:31px; min-width:31px; min-height:31px; height:31px; padding:0; border:2px solid var(--card-background-color); border-radius:50%; background:var(--primary-color); color:var(--text-primary-color); box-shadow:0 0 0 1px var(--primary-color); font-size:10px; font-weight:700; touch-action:none; cursor:grab; }.timeline-point:active { cursor:grabbing; }.time-scale { display:flex; justify-content:space-between; color:var(--secondary-text-color); font-size:10px; margin-top:4px; }.labels, .period-row { display:grid; grid-template-columns:minmax(96px,1.5fr) 86px 78px 14px 32px; gap:7px; align-items:center; }
        .labels { color:var(--secondary-text-color); font-size:12px; margin-bottom:4px; padding:0 4px; }.period-row { margin:7px 0; border-radius:6px; }.period-row.selected { outline:2px solid var(--primary-color); outline-offset:2px; }.period-row input:first-child { min-width:0; }
        .advanced { margin-top:22px; }.advanced button { margin:0 8px 8px 0; }.blank { text-align:center; padding:48px; }.view-tabs { display:flex; gap:8px; margin:0 0 18px; }.view-tabs button.active { outline:3px solid var(--primary-color); outline-offset:2px; }.quick-page { display:grid; gap:16px; }.quick-header { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; }.quick-header h2 { margin:0; }.small { width:auto !important; }.quick-rooms { display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:12px; }.quick-room, .quick-controls { background:var(--card-background-color); box-shadow:var(--ha-card-box-shadow, 0 1px 3px #0002); border-radius:12px; padding:15px; }.quick-room { display:flex; gap:10px; align-items:center; }.quick-room input { min-height:auto; }.quick-room span { display:grid; gap:3px; flex:1; }.quick-room small { color:var(--secondary-text-color); }.quick-room button { background:var(--secondary-background-color); color:var(--primary-text-color); min-height:32px; padding:0 9px; }.quick-controls { max-width:760px; }.quick-actions, .durations { display:flex; gap:9px; flex-wrap:wrap; align-items:end; }.quick-actions label { display:grid; gap:4px; font-size:12px; }.quick-actions input { width:92px; }.durations label { display:flex; align-items:center; gap:4px; }.durations input { min-height:auto; }.quick-controls > button { margin-top:16px; }
        @media (max-width:600px) { main { padding:16px; } select { min-width:100%; } .timeline-title { display:block; }.timeline-title span { display:block; text-align:left; margin-top:3px; }.period-row { grid-template-columns:1fr 78px 67px 12px 28px; gap:4px; } }
      </style>
      <main>
        <header><div class="title"><img class="brand-icon" src="${brandIconUrl}" alt=""><div><h1>Visual Climate Scheduler</h1><p class="subtitle">Seven independent daily schedules. Changes save immediately.</p></div></div>${this._view === "schedule" ? `<label>Scheduled space<br><select data-action="room">${options}</select></label>` : ""}</header>
        ${this._message ? `<p class="notice">${this._escape(this._message)}</p>` : ""}
        <nav class="view-tabs"><button class="${this._view === "schedule" ? "active" : ""}" data-action="view" data-view="schedule">Schedule</button><button class="${this._view === "quick" ? "active" : ""}" data-action="view" data-view="quick">Quick Change</button></nav>
        ${content}
      </main>`;
  }
}

customElements.define("visual-climate-scheduler-panel", VisualClimateSchedulerPanel);
