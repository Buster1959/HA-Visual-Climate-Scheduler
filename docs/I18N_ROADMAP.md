# Internationalisation (i18n) Roadmap — HA Visual Climate Scheduler

**Goal:** make the integration fully multilingual — both the Home Assistant
config/options flow and the custom frontend panel — with English as the source
of truth and a low-friction path for adding new languages.

**Status at time of writing (v1.0.0):**

- Config/options flow: already internationalised. `strings.json` +
  `translations/en.json` exist and are complete (~30 keys). HA loads the right
  file automatically from the user's profile language.
- Frontend panel (`frontend/visual-climate-scheduler-panel.js`, 591 lines):
  **not** internationalised. ~40+ user-facing strings are hardcoded English
  literals. No localisation hook exists yet.

The panel already receives Home Assistant context through its `set hass(hass)`
setter (line 30), which means `hass.language` and `hass.locale.time_format` are
**already available inside the panel** — no extra plumbing is needed to *know*
the user's language or clock preference. This is what makes the recommended
approach below the simplest one.

---

## Recommended architecture

### Delivery mechanism: bundled per-language JSON dictionaries (client-side)

For a single-file, vanilla-JS, no-build-step panel, ship the translations *with*
the panel and select the active dictionary from `this.hass.language`, falling
back to English for any missing key. Do **not** build a Python websocket/HTTP
translation endpoint — it adds server plumbing, a fetch round-trip, and a cache
layer for zero benefit here, because the panel already has `hass.language` in
hand and the string catalogue is small enough to ship inline.

Two viable packaging options, in order of preference:

1. **Inline dictionaries in the panel JS** (simplest). One `const TRANSLATIONS = {
   en: {...}, de: {...}, ... }` object at the top of the file. Zero extra HTTP
   requests, zero static-path registration, guaranteed to load with the panel.
   Downside: the JS file grows; translators edit the same file.
2. **Separate JSON files served as static assets.** Put
   `frontend/translations/<lang>.json` next to the panel, register the folder as
   a static path (the panel folder is *already* registered as a static path in
   `panel.py`, so this is nearly free), and `fetch()` the matching file at panel
   init with an English fallback. Cleaner for translators/PRs; costs one small
   cached fetch.

**Recommendation:** start with option 1 (inline) to get the framework working
and prove the UX, then migrate to option 2 once more than ~3 languages exist and
external contributors want to submit translation PRs without touching JS.

### Language selection logic

```
lang = (this.hass.language || "en").toLowerCase();      // e.g. "de", "sv", "nb"
base = lang.split("-")[0];                                // "pt-br" -> "pt"
dict = TRANSLATIONS[lang] || TRANSLATIONS[base] || TRANSLATIONS.en;
t(key, params) => interpolate(dict[key] ?? TRANSLATIONS.en[key] ?? key, params);
```

Always fall back key-by-key to English so a partially-translated language never
shows blank strings.

---

## Workstream 1 — Config / options flow (small, mostly done)

The backend translation layer is complete for English. To add languages:

- Keep `strings.json` as the English source of truth (HA convention).
- Add one sibling file per language under `translations/`:
  `translations/de.json`, `fr.json`, `es.json`, `it.json`, `nl.json`,
  `sv.json`, `no.json`, `da.json`, `fi.json`.
- Each mirrors the exact key structure of `en.json`.
- `hassfest` (already wired in `.github/workflows/hassfest.yml`) validates these
  on every push — it will flag structural mismatches.

Effort: an afternoon once translations are in hand. No code changes.

---

## Workstream 2 — Frontend string extraction (the bulk of the work)

Every user-facing literal in the panel JS must move into the key-based catalogue
and be routed through `t(...)`. Categories found in the current file:

- **Toast / status messages** (lines ~55, 72, 178, 184, 213, 216, 223, 232,
  240, 242, 264, 466, 469, 476, 497) — several are interpolated with
  `${error.message}` or a room name, so the keys need parameter support.
- **Instructional text** (lines 171, 172, 385 "Drag to change time and target").
- **Buttons & labels** (lines 519 "Remove period", 538 "Clear all"/"Select
  all", 554 "Modify room or zone"/"Add a room or zone", "Cancel hold").
- **Empty-state messages** (538, 554 "No other rooms/zones are available", "No
  eligible climate thermostats are currently available").
- **Templated dynamic strings** — these need special care:
  - `` `Period ${number}` `` (line 310) → `t("period_label", {number})`
  - `` `${Day} applied to ${targetDays}. Save schedule to keep it.` ``
    (line 452) — the day-capitalisation and list join are locale-sensitive
    (see Workstream 4).
  - `` `Holding ${temp} until ${time}` `` / `` `Scheduled ${temp}` `` (line 526).

**Refactor steps:**

1. Add a `localize`/`t` helper method to the panel class and a `_dict` field
   resolved once in `set hass` (when `hass.language` first becomes available).
2. Define the English catalogue with stable, namespaced keys, e.g.
   `editor.clear_all`, `editor.remove_period`, `quick.hold_until`,
   `toast.saved`, `toast.not_saved`, `error.load_schedules`.
3. Replace each literal with a `t("key")` / `t("key", {param})` call.
4. Support `{placeholder}` interpolation in `t` (simple string replace).
5. Preserve the existing `_escape(...)` calls — translate *then* escape, never
   the reverse, so translated text is still HTML-safe.

Effort: 1–2 days for a clean pass (extraction + helper + wiring + English dict).

---

## Workstream 3 — Locale-aware formatting (easy to overlook, high UX value)

A climate scheduler has three inherently locale-sensitive surfaces. Two are not
"translation" but "formatting", and matter even for English users:

- **Time display (12h vs 24h).** The panel currently renders `HH:MM` via
  `padStart` (line 327) and uses `toLocaleTimeString` in one place (line 526,
  inconsistently). Standardise on `hass.locale.time_format` (values:
  `12`/`24`/`language`/`system`) so a US user sees `4:00 PM` and a UK/EU user
  sees `16:00`. Note the `<input type="time">` fields (line 517) are already
  localised by the browser — leave those alone; only format *display* text.
- **Day-of-week names & week start.** Days are currently object keys
  (`monday`…`sunday`) and capitalised ad hoc (line 452
  `day[0].toUpperCase()`). Render display labels via
  `new Intl.DateTimeFormat(hass.language, {weekday: "long"})` rather than
  translating seven strings by hand, and consider week-start ordering
  (Monday-first for most of Europe; the data model can stay Monday-keyed).
- **Temperature unit** — already handled via config (`temperature_unit`), no
  action needed beyond confirming `_formatTemperature` respects it.

Keep the internal data-model keys (`monday`, `period_1`, etc.) in English —
translate only what's *displayed*. This avoids migrating stored schedules.

Effort: a few hours; genuinely improves UX for all locales.

---

## Workstream 4 — Target languages

Agreed initial set: **Major European + Nordic.**

| Language   | Code   | Group          |
|------------|--------|----------------|
| German     | `de`   | Major European |
| French     | `fr`   | Major European |
| Spanish    | `es`   | Major European |
| Italian    | `it`   | Major European |
| Dutch      | `nl`   | Major European |
| Swedish    | `sv`   | Nordic         |
| Norwegian  | `nb`*  | Nordic         |
| Danish     | `da`   | Nordic         |
| Finnish    | `fi`   | Nordic         |

*Norwegian: HA generally uses `nb` (Bokmål). Provide `nb` and let the
`base`-fallback cover a bare `no`.

Each new language, once the framework exists, is just: translate the frontend
catalogue (~40 keys) + copy `en.json` → `<lang>.json` for the config flow.
Roughly 1–2 hours each, and well-suited to offloading to Crowdin/Lokalise or
community PRs (HA integrations commonly crowdsource this).

---

## Phased rollout

- **Phase 0 — Framework (English only).** Add `t()` helper, extract all frontend
  strings into the English catalogue, wire `hass.language` with English
  fallback, and fix time/day formatting via `hass.locale`. Ship with English
  only. This is the load-bearing work; nothing user-visible changes yet, but the
  integration is now translation-ready. *(Recommended first deliverable.)*
- **Phase 1 — First non-English languages.** Add German + French (largest HA
  communities) as both frontend dict entries and `translations/*.json` config
  files. Validates that the framework and fallbacks behave with real
  translations, including longer strings that may affect layout.
- **Phase 2 — Complete the set.** Add remaining European + Nordic languages.
- **Phase 3 — Open to contributors.** Migrate frontend dictionaries to separate
  JSON files (delivery option 2), document the "how to add a language" process
  in the repo, and optionally connect a translation-management service.

---

## Checklist / definition of done

- [ ] `t()` helper added to panel; resolves dict once from `hass.language`.
- [ ] All ~40 frontend literals extracted to namespaced keys; no bare
      user-facing English strings remain in the JS (except the English
      catalogue itself).
- [ ] Interpolated strings (`Period N`, error messages, hold/scheduled labels)
      use parameter substitution.
- [ ] Key-by-key English fallback verified (simulate a partial dictionary).
- [ ] Time display driven by `hass.locale.time_format`; `<input type=time>`
      left to the browser.
- [ ] Day labels rendered via `Intl.DateTimeFormat`, internal keys unchanged.
- [ ] Translation applied *before* `_escape()` (HTML-safety preserved).
- [ ] `translations/<lang>.json` added for each target language; `hassfest`
      passes.
- [ ] Manual smoke test: switch HA profile language, confirm both the config
      flow and the panel render translated + correctly formatted.

---

## Effort summary

| Workstream | Effort |
|---|---|
| Config-flow translations (per language) | ~an afternoon for the set |
| Frontend extraction + `t()` framework (Phase 0) | 1–2 days |
| Locale-aware time/day formatting | a few hours |
| Each additional language after framework | 1–2 hours |
