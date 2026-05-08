const CARD_TYPE = "school-schedule-card";
const DEFAULT_CONFIG = {
  mode: "today",
  title: "",
  show_title: true,
};
const SUPPORTED_MODES = new Set(["today", "table", "cards", "card"]);

class SchoolScheduleCard extends HTMLElement {
  static getStubConfig(hass) {
    const entity = Object.keys(hass?.states || {}).find((entityId) =>
      entityId.startsWith("sensor.stundenplan_")
    );
    const title =
      hass?.localize?.("component.stundenplan.common.card_title") || "";

    return {
      entity,
      mode: DEFAULT_CONFIG.mode,
      title,
    };
  }

  setConfig(config) {
    if (!config?.entity) {
      throw new Error("entity is required");
    }

    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return this.config?.mode === "table" ? 5 : 3;
  }

  localize(key, fallback = "", vars = {}) {
    const value = this._hass?.localize?.(`component.stundenplan.${key}`, vars) || fallback;
    return Object.entries(vars).reduce((text, [name, val]) => String(text).replace(`{${name}}`, val), value);
  }

  navigate() {
    const tap = this.config?.tap_action;
    if (tap?.action === "navigate" && tap.navigation_path) {
      history.pushState(null, "", tap.navigation_path);
      window.dispatchEvent(new Event("location-changed"));
    }
  }

  render() {
    if (!this.config || !this._hass) {
      return;
    }

    const state = this._hass.states[this.config.entity];
    if (!state) {
      this.innerHTML = `<ha-card><div class="card-content">${this.escape(this.localize("common.entity_not_found"))}: ${this.escape(this.config.entity)}</div></ha-card>`;
      return;
    }

    const mode = this.config.mode || "today";
    const clickable = this.config.tap_action?.action === "navigate";
    const title = this.config.title || this.localize("common.card_title");
    this.innerHTML = `
      <ha-card class="${clickable ? "clickable" : ""}" ${clickable ? 'role="button" tabindex="0"' : ""}>
        ${this.config.show_title !== false && title ? `<div class="card-header">${this.escape(title)}</div>` : ""}
        <div class="card-content">
          ${mode === "today" ? this.renderToday(state) : ""}
          ${mode === "table" ? this.renderTable(state) : ""}
          ${(mode === "cards" || mode === "card") ? this.renderCards(state) : ""}
          ${!SUPPORTED_MODES.has(mode) ? `<div class="free">${this.escape(this.localize("common.unknown_mode"))}: ${this.escape(mode)}</div>` : ""}
        </div>
      </ha-card>
      <style>
        ha-card.clickable { cursor: pointer; }
        .headline { font-size: 1.1rem; font-weight: 650; margin-bottom: 4px; }
        .subline { color: var(--secondary-text-color); margin-bottom: 14px; }
        .free { padding: 12px; border-radius: 8px; background: var(--secondary-background-color); }
        .lesson-list { display: flex; flex-direction: column; gap: 9px; }
        .lesson { display: flex; align-items: center; min-height: 32px; }
        .lesson-pill,
        .cell-pill {
          --subject-color: var(--primary-color);
          display: inline-flex;
          align-items: center;
          gap: 8px;
          max-width: 100%;
          border-radius: 999px;
          background: color-mix(in srgb, var(--subject-color) 32%, var(--card-background-color));
          color: var(--primary-text-color);
          border: 0;
          box-shadow: none;
          overflow: hidden;
        }
        .lesson-pill { padding: 4px 10px 4px 4px; }
        .cell-pill { padding: 3px 9px 3px 3px; }
        .lesson-icon-circle {
          width: 28px;
          height: 28px;
          min-width: 28px;
          border-radius: 50%;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: var(--subject-color);
          overflow: hidden;
          flex: 0 0 auto;
        }
        .lesson-icon-circle ha-icon {
          --mdc-icon-size: 18px;
          width: 18px;
          height: 18px;
          color: white;
          display: block;
          line-height: 1;
          transform: scale(0.98);
          transform-origin: center;
        }
        .lesson-name {
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .empty { color: var(--secondary-text-color); font-style: italic; }
        .table-wrap { overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; min-width: 620px; }
        th, td { border: 0; border-bottom: 1px solid var(--divider-color); padding: 8px; vertical-align: middle; }
        th { text-align: left; font-weight: 650; color: var(--primary-text-color); background: transparent; }
        td.time { white-space: nowrap; color: var(--secondary-text-color); font-size: 0.9rem; width: 120px; }
        .cell-subject { display: flex; align-items: center; max-width: 100%; }
        .cell-subject .cell-pill { max-width: 100%; }
        .cell-subject .lesson-icon-circle { width: 22px; height: 22px; min-width: 22px; }
        .cell-subject .lesson-icon-circle ha-icon { --mdc-icon-size: 15px; width: 15px; height: 15px; transform: scale(1.05); }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
        .day-card { border: 1px solid var(--divider-color); border-radius: 8px; padding: 12px; background: var(--card-background-color); }
        .day-header { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
        .day-title { font-weight: 750; }
        .badge { color: var(--secondary-text-color); font-size: 0.9rem; white-space: nowrap; text-align: right; }
        @media (max-width: 600px) {
          table { min-width: 520px; }
          th, td { padding: 6px; }
          .cards { grid-template-columns: 1fr; }
          .cell-pill { padding-right: 7px; }
        }
      </style>
    `;

    if (clickable) {
      const card = this.querySelector("ha-card");
      card?.addEventListener("click", () => this.navigate());
      card?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this.navigate();
        }
      });
    }
  }

  renderToday(state) {
    const a = state.attributes || {};
    const weekday = a.weekday_name || this.localize("common.today");
    if (a.is_free_day) {
      return `<div class="headline">${this.escape(weekday)}</div><div class="free">${this.escape(this.localize("common.free_day"))}${a.free_reason ? `: ${this.escape(a.free_reason)}` : ""}</div>`;
    }
    if (!a.is_school_day || !a.lessons?.length) {
      return `<div class="headline">${this.escape(weekday)}</div><div class="free">${this.escape(this.localize("common.no_lessons"))}</div>`;
    }
    return `
      <div class="headline">${this.escape(weekday)}</div>
      <div class="subline">${this.escape(this.localize("common.school_end"))}: ${this.escape(a.school_end || "-")}</div>
      <div class="lesson-list">${a.lessons.map((lesson) => this.renderLesson(lesson, false)).join("")}</div>
    `;
  }

  renderTable(state) {
    const a = state.attributes || {};
    const lessonTimes = a.lesson_times || [];
    const schoolDays = a.school_days || [];
    const days = a.days || {};
    const maxRows = Number(a.lesson_count || lessonTimes.length || 0);
    if (!maxRows || !schoolDays.length) return `<div class="free">${this.escape(this.localize("common.missing_schedule_data"))}</div>`;
    return `
      <div class="table-wrap">
        <table>
          <thead><tr><th>${this.escape(this.localize("common.time"))}</th>${schoolDays.map((day) => `<th>${this.escape(days[day]?.name || a.weekday_names?.[day] || day)}</th>`).join("")}</tr></thead>
          <tbody>
            ${Array.from({ length: maxRows }, (_, i) => `
              <tr>
                <td class="time">${this.escape(lessonTimes[i]?.start || "")} - ${this.escape(lessonTimes[i]?.end || "")}</td>
                ${schoolDays.map((day) => {
                  const gridLesson = days[day]?.lesson_grid?.[i];
                  const foundLesson = (days[day]?.lessons || []).find((l) => Number(l.hour) === i + 1);
                  const lesson = gridLesson || foundLesson;
                  return `<td>${lesson ? this.renderLesson(lesson, true) : `<span class="empty">-</span>`}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  renderCards(state) {
    const a = state.attributes || {};
    const schoolDays = a.school_days || [];
    const days = a.days || {};
    if (!schoolDays.length) return `<div class="free">${this.escape(this.localize("common.no_school_days"))}</div>`;
    return `
      <div class="cards">
        ${schoolDays.map((day) => {
          const d = days[day] || {};
          const lessons = d.lessons || [];
          return `
            <div class="day-card">
              <div class="day-header"><div class="day-title">${this.escape(d.name || a.weekday_names?.[day] || day)}</div><div class="badge">${this.escape(this.localize("common.school_end"))}: ${this.escape(d.school_end || "-")}</div></div>
              <div class="lesson-list">${lessons.length ? lessons.map((lesson) => this.renderLesson(lesson, false)).join("") : `<span class="empty">${this.escape(this.localize("common.no_lessons"))}</span>`}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  renderLesson(lesson, compact) {
    const color = lesson.color || "var(--primary-color)";
    const icon = this.escape(lesson.icon || "mdi:book-open-page-variant");
    const subject = this.escape(lesson.subject || "");
    return `
      <div class="${compact ? "cell-subject" : "lesson"}">
        <span class="${compact ? "cell-pill" : "lesson-pill"}" style="--subject-color:${this.cssValue(color)}">
          <span class="lesson-icon-circle">
            <ha-icon icon="${icon}"></ha-icon>
          </span>
          <span class="lesson-name">${subject}</span>
        </span>
      </div>
    `;
  }

  escape(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;");
  }

  cssValue(value) {
    return String(value ?? "").replace(/[;"'<>]/g, "");
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, SchoolScheduleCard);
}

const globalHass = document.querySelector("home-assistant")?.hass;
const cardName =
  globalHass?.localize?.("component.stundenplan.card.name") || CARD_TYPE;
const cardDescription =
  globalHass?.localize?.("component.stundenplan.card.description") || CARD_TYPE;

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: cardName,
    description: cardDescription
  });
}
