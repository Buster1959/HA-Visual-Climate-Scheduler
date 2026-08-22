class VisualClimateSchedulerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._configuration = null;
    this._roomId = null;
    this._days = null;
    this._message = "";
    this.shadowRoot.addEventListener("click", (event) => this._onClick(event));
    this.shadowRoot.addEventListener("change", (event) => this._onChange(event));
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
    } catch (error) {
      this._message = `Could not load schedules: ${error.message || error}`;
      this._render();
    }
  }

  _loadRoom(clearMessage = true) {
    const room = this._configuration?.rooms[this._roomId];
    this._days = room ? structuredClone(room.days) : null;
    if (clearMessage) this._message = "";
    this._render();
  }

  _onChange(event) {
    const target = event.target;
    if (target.dataset.action === "room") {
      this._roomId = target.value;
      this._loadRoom();
      return;
    }
    const { day, index, field } = target.dataset;
    if (!day || index === undefined || !field) return;
    const period = this._days[day][Number(index)];
    period[field] = field === "temperature" ? Number(target.value) : target.value;
    if (field === "name" && !period.friendly_name) period.friendly_name = this._slug(target.value);
  }

  _onClick(event) {
    const button = event.target.closest("button");
    if (!button || button.disabled) return;
    const { action, day, index } = button.dataset;
    if (action === "add") this._addPeriod(day);
    if (action === "remove") this._days[day].splice(Number(index), 1);
    if (action === "save") this._save();
    this._render();
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
      temperature: 20,
    });
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
      <div class="period-row">
        <input aria-label="${day} period name" data-day="${day}" data-index="${index}" data-field="name" value="${this._escape(period.name)}">
        <input aria-label="${day} period time" type="time" data-day="${day}" data-index="${index}" data-field="time" value="${this._escape(period.time)}">
        <input aria-label="${day} period temperature" type="number" step="0.1" data-day="${day}" data-index="${index}" data-field="temperature" value="${this._escape(period.temperature)}">
        <span>°</span><button class="icon" data-action="remove" data-day="${day}" data-index="${index}" title="Remove period">×</button>
      </div>`).join("");
    return `<section class="day-card"><h2>${day}</h2><div class="labels"><span>Name</span><span>Time</span><span>Target</span></div>${rows || '<p class="empty">No periods yet.</p>'}<button class="secondary" data-action="add" data-day="${day}" ${periods.length >= 4 ? "disabled" : ""}>+ Add period</button></section>`;
  }

  _render() {
    const rooms = this._configuration?.rooms || {};
    const options = Object.entries(rooms).map(([id, room]) => `<option value="${this._escape(id)}" ${id === this._roomId ? "selected" : ""}>${this._escape(room.name)} · ${room.climate_entity_ids.length} thermostat${room.climate_entity_ids.length === 1 ? "" : "s"}</option>`).join("");
    const editor = this._days ? `<div class="week">${Object.keys(this._days).map((day) => this._renderPeriods(day)).join("")}</div>` : `<div class="blank"><h2>No rooms or zones configured</h2><p>Open the integration’s Configure menu and add a room or zone before creating schedules.</p></div>`;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; min-height:100%; background:var(--primary-background-color); color:var(--primary-text-color); font-family:var(--primary-font-family, sans-serif); }
        main { max-width:1500px; margin:0 auto; padding:28px; }
        header { display:flex; justify-content:space-between; align-items:flex-end; gap:20px; flex-wrap:wrap; margin-bottom:22px; }
        h1 { margin:0; font-size:30px; } h2 { margin:0 0 12px; font-size:17px; text-transform:capitalize; }
        .subtitle, .empty { color:var(--secondary-text-color); margin:6px 0 0; }
        select, input { box-sizing:border-box; min-height:38px; border:1px solid var(--divider-color); border-radius:7px; background:var(--card-background-color); color:var(--primary-text-color); padding:6px 8px; font:inherit; }
        select { min-width:290px; } button { border:0; border-radius:7px; min-height:38px; padding:0 14px; background:var(--primary-color); color:var(--text-primary-color); font:inherit; cursor:pointer; } button.secondary { background:var(--secondary-background-color); color:var(--primary-text-color); width:100%; margin-top:10px; } button:disabled { opacity:.48; cursor:not-allowed; } button.icon { min-width:32px; padding:0; background:transparent; color:var(--error-color); font-size:24px; }
        .notice { margin:0 0 18px; padding:12px 14px; border-radius:8px; background:var(--info-color, #2196f3); color:white; }
        .week { display:grid; grid-template-columns:repeat(auto-fit, minmax(310px, 1fr)); gap:16px; }
        .day-card, .blank, .advanced { background:var(--card-background-color); box-shadow:var(--ha-card-box-shadow, 0 1px 3px #0002); border-radius:12px; padding:18px; }
        .labels, .period-row { display:grid; grid-template-columns:minmax(96px,1.5fr) 86px 78px 14px 32px; gap:7px; align-items:center; }
        .labels { color:var(--secondary-text-color); font-size:12px; margin-bottom:4px; padding:0 4px; }.period-row { margin:7px 0; }.period-row input:first-child { min-width:0; }
        .advanced { margin-top:22px; }.advanced button { margin:0 8px 8px 0; }.blank { text-align:center; padding:48px; }
        @media (max-width:600px) { main { padding:16px; } select { min-width:100%; } .period-row { grid-template-columns:1fr 78px 67px 12px 28px; gap:4px; } }
      </style>
      <main>
        <header><div><h1>Visual Climate Scheduler</h1><p class="subtitle">Seven independent daily schedules. Changes save immediately.</p></div><label>Scheduled space<br><select data-action="room">${options}</select></label></header>
        ${this._message ? `<p class="notice">${this._escape(this._message)}</p>` : ""}
        ${editor}
        <div class="advanced"><h2>Coming later</h2><button disabled>Apply to selected days</button><button disabled>Copy schedule</button><button disabled>Temporary override</button><button data-action="save" ${this._days ? "" : "disabled"}>Save schedule</button></div>
      </main>`;
  }
}

customElements.define("visual-climate-scheduler-panel", VisualClimateSchedulerPanel);
