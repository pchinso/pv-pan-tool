# PV PAN Tool Desktop App - Phase 1.5 Pendings

## Overview

This document details the Phase 1.5 scope for the PV PAN Tool Desktop Application. It mirrors the structure and rigor of the main Development Roadmap and focuses on three areas: parser enhancements, database updates, and desktop UI features. The goals are to extract and persist Bifaciality Factor and IV Curve data from .PAN files, surface these in the app, and add a simple string-sizing tool.

## Goals

- Parse additional parameters from .PAN files: Bifaciality Factor and IV Curve data (when available).
- Persist the new parameters in the database with proper schema and migrations.
- Expose Bifaciality in the Search/Database table view as a column.
- Add a new IV Curve tab with plotting and export.
- Add a new Max Modules in String tab implementing a simple, transparent calculation.

## Scope (Phase 1.5)

- Parser: non-breaking extensions only; no behavioral changes to existing fields.
- Database: additive schema changes (new columns/tables, indexes); migration path included.
- Desktop UI: new tabs and minor table updates; reuse existing controllers where possible.
- Documentation and tests covering new features.

## Deliverables

- Updated parser capable of extracting Bifaciality Factor and IV Curve data.
- Database migration script(s) and updated models.
- UI updates: new tabs (IV Curve, String Sizing) and new column (Bifaciality Factor).
- Unit and integration tests for parsing, data access, and UI wiring.
- User documentation updates (docs/ and desktop_app resources).

---

## Parser Enhancements

### Parameters to Extract

#### Bifaciality Factor

- Definition: Ratio (0–1 or percentage) describing rear-to-front current capability. Used for bifacial modules; may be absent for monofacial.
- Expected .PAN keys (tolerant parsing): "Bifaciality", "BifacialityFactor", "BifIsc", "Bifacial_Factor" (case-insensitive; numeric). If percentage-like strings found (e.g., "70%"), convert to 0.70.
- Default/Absent: store NULL; do not infer.

#### IV Curve (if present)

- Accept either:
  - Discrete IV points at STC (e.g., a list of (V, I) pairs), or
  - Parameterized coefficients convertible to points (optional; if reliable).
- Minimum representation: store raw discrete points exactly as provided at STC. If both IV and PV points exist, store both; otherwise compute PV from IV as V×I at render-time.
- Multiple conditions: if NOCT or alternate irradiance/temperature curves exist, capture them as separate series with a label (e.g., "STC", "NOCT"). If only STC exists, store STC.

### Parsing Contract

- Inputs: path to .PAN file, text content.
- Outputs:
  - bifaciality_factor: float in [0, 1] or NULL.
  - iv_series: list of series; each series: { label: str, points: list[[float V, float I]] }.
- Validation:
  - Reject malformed numeric tokens; ignore non-numeric entries.
  - For IV points, require at least 4 monotonic non-negative points (V ≥ 0, I ≥ 0); otherwise skip series with a warning.
  - Max points per series: configurable (default 2000) to avoid memory blowups.
- Error handling: soft-fail with logged warnings; never abort module parsing due to optional fields.

### Implementation Notes

- Extend existing parser to scan candidate keys and blocks for IV data; use case-insensitive matching and trimming.
- Support both comma- and whitespace-separated point lists; allow either on single or multiple lines.
- Keep parser stateless per file; no cross-file assumptions.
- Unit tests: fixtures for files with/without bifaciality; files with valid/invalid IV series; boundary cases (percent strings, single-point lists, mixed separators).

---

## Database Updates

### Schema Additions

- Table pv_modules (additive columns):
  - bifaciality_factor REAL NULL
  - iv_curve_stc TEXT NULL  (JSON: { "points": [[V, I], ...] })
  - iv_curve_other TEXT NULL (JSON array of series: [{ "label": str, "points": [[V, I], ...] }]) — optional; may be omitted if creating a separate table.

Or (preferred for normalization on large datasets):

- New table iv_curves:
  - id INTEGER PRIMARY KEY
  - module_id INTEGER NOT NULL REFERENCES pv_modules(id) ON DELETE CASCADE
  - label TEXT NOT NULL DEFAULT 'STC'
  - points_json TEXT NOT NULL      -- JSON: [[V, I], ...]
  - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  - Index: (module_id, label)

Choose one approach based on current ORM/data-access patterns. If the codebase already uses JSON blobs on pv_modules, follow that for consistency; otherwise prefer the separate iv_curves table.

### Migration Plan

- Add new column(s)/table via migration script.
- Backfill: none required; values remain NULL until re-parse.
- Versioning: bump internal schema/version marker if applicable.

### Data Access

- Update models.py to include bifaciality_factor and IV curve accessors.
- Update database.py/controller to read/write new fields with transactions and parameterized queries.
- Add convenience methods:
  - get_iv_series(module_id) -> list[Series]
  - has_bifaciality(module_id) -> bool

---

## Desktop App Updates

### 1) Search/Database Table: Bifaciality Column

- Add "Bifaciality" column (display as % with one decimal; e.g., 70.0%).
- Sorting enabled; NULLs last.
- Tooltip: "Bifaciality Factor (rear/front current ratio)."
- Column visibility configurable in Settings if applicable.

### 2) New Tab: IV Curve

UI Layout

- Left: Module selector (single or multi-select) leveraging existing search results or a dropdown.
- Center: Matplotlib canvas with IV curve plot; optional PV curve overlay (secondary axis) per module.
- Right: Options panel: toggle PV curve, toggle points/lines, show markers, legend, export (PNG/PDF), series selection (STC/other).

Functionalities

- Plot 1–5 modules overlayed with distinct colors.
- Display key points if available (Voc, Isc, Vmp, Imp) as markers/annotations.
- Export chart to PNG/PDF with configured DPI; include legend.
- Handle missing IV data gracefully with inline notice and quick action: "Open Parser/Docs".

Performance/UX

- Debounce redraw on option changes.
- Limit points per series plotted (cap via settings; default 2000); downsample if needed.

### 3) New Tab: Max Modules in String (Simple Model)

Purpose

- Provide an engineering quick-check for the maximum number of modules per string constrained by inverter max DC input voltage under minimum ambient temperature.

Inputs

- Inverter max DC voltage (Vdc_max). Required.
- Minimum ambient temperature (T_min, °C). Required.
- Safety margin (% of voltage headroom). Optional; default 5%.
- Module selection (from database). Required.

Module Parameters Used

- Voc at STC (Voc_STC).
- Temperature coefficient of Voc (alpha_Voc, in %/°C or 1/°C). If stored as negative value in %/°C, convert using abs() and percent→fraction.

Model

```text
# Compute cold-corrected open-circuit voltage per module
Voc_cold = Voc_STC * (1 + |alpha_Voc| * (25 - T_min))

# Available voltage for sizing with margin
V_allow = Vdc_max * (1 - safety_margin)

# Max modules per string (integer)
N_max = floor(V_allow / Voc_cold)
```

- If alpha_Voc is missing, display a warning and allow user to enter a temporary override coefficient.

Outputs

- N_max with explanation: show intermediate values (Voc_cold, V_allow).
- Optionally compute N_min for MPPT minimum voltage if user supplies Vdc_min and temperature at max operating (out of scope by default; add as optional fields if trivial).

UX/Validation

- Validate positive voltages, sensible temperature ranges (-40 to +60 °C by default).
- Per-module summary table for multiple selections.
- Export results to CSV.

---

## Settings and Config (Optional)

- Charts & Export: default DPI, line width, marker size for IV plots.
- Performance: max points per series to plot; downsampling toggle.
- Search/Display: default visibility for the Bifaciality column.

---

## Testing Plan

- Parser
  - Bifaciality extraction: numeric, percentage string, absent.
  - IV extraction: valid series, malformed tokens, non-monotonic points (skipped with warning), large series truncation.
- Database
  - Migration up/down; NULL compatibility.
  - CRUD for iv_curves and bifaciality_factor.
- UI
  - Table shows bifaciality and sorts correctly.
  - IV tab renders with one/multiple modules; export works.
  - String sizing computes expected N_max across edge cases.

---

## Timeline (Phase 1.5)

Week 1

- Implement parser changes with tests; add schema/migrations.
- Wire data access in controllers.

Week 2

- Add Bifaciality column to table; implement IV Curve tab.
- Implement String Sizing tab with calculation and export.

Week 3

- Polish UX, add settings, documentation, and finalize tests.

---

## Acceptance Criteria

- Parser successfully extracts bifaciality and IV series from known sample .PAN files and leaves others unaffected.
- Database persists values without breaking existing queries; migrations run clean on an existing DB.
- Desktop app displays Bifaciality column, renders IV curves, and computes N_max with clear explanations.
- Tests cover the new features (parser, DB, UI wiring) and pass locally.
- Documentation updated to explain usage and assumptions.

---

## Risks & Notes

- .PAN variations: vendor-specific field names may require expanding key lists over time; parser should be defensive.
- IV data volume: very dense curves can bloat storage; cap points and/or store compressed JSON if needed.
- Temperature coefficients: sign and units vary; normalize carefully and make UI transparent about assumptions.
- Engineering caution: string sizing is a simplified model and must be labeled as guidance, not a certified design.
