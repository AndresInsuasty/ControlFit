# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ControlFit** is a Spanish-language Streamlit web app for personal trainers to manage student training plans using Google Sheets as a database. It answers three core business questions: how many active students, who renews soon, and how much income came in this month.

## Commands

```bash
# Install dependencies (creates .venv automatically)
uv sync --dev

# Run the app
uv run streamlit run app.py

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_calculations.py -v
uv run pytest tests/test_sheets.py -v
```

No build step — Streamlit runs as interpreted Python. No linter is configured.

## Architecture

**Entry point:** `app.py` — password login screen. Sets `st.session_state.authenticated`. Every page must guard with `if not st.session_state.get("authenticated"): st.stop()`.

**Pages** (Streamlit multi-page routing via `pages/` directory):
- `1_Dashboard.py` — 4 KPI metric cards + 2 Plotly charts (monthly income bar, status distribution donut)
- `2_Alumnos.py` — filterable student table with color-coded status rows (green/yellow/red)
- `3_Gestion.py` — add/edit student forms with two tabs

**Data layer** (strict I/O vs. logic separation):
- `data/sheets.py` — Google Sheets CRUD: `get_data()`, `append_record(record)`, `update_record(id, record)`. Returns empty DataFrame on error.
- `data/calculations.py` — pure business logic with no I/O: `compute_status(df)`, `get_metrics(df)`, `get_monthly_income(df)`, `get_status_counts(df)`. All functions are unit-testable without mocking.

## Data Model

Google Sheets columns (in order): `id | nombre | telefono | fecha_inicio | fecha_fin | valor_pagado | notas | fecha_registro`

One row per plan period (a student can have multiple rows). Status is never stored — always computed dynamically by `compute_status()`:
- **VENCIDO**: `fecha_fin < today`
- **POR VENCER**: `0 <= (fecha_fin - today) <= 7 days`
- **ACTIVO**: everything else

Dates stored as `DD/MM/YYYY` strings (Colombian locale). `valor_pagado` is COP (Colombian Pesos). `fecha_registro` is ISO 8601 (auto-generated on record creation).

## Credentials & Secrets

Requires `.streamlit/secrets.toml` (not committed — use `.streamlit/secrets.toml.example` as template):

```toml
password = "..."
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key = "..."
client_email = "..."
# ... other GCP service account fields
```

Google Sheet must be shared with the service account email (Editor role). Required GCP APIs: Google Sheets API and Google Drive API.

## Testing

21 unit tests total. `test_sheets.py` mocks gspread — no real API calls. `test_calculations.py` covers status boundary conditions (exactly 7 days, 8 days), monthly income aggregation, and empty DataFrame edge cases.

## Key Design Decisions

- **No delete in app** — records removed directly in Google Sheets (MVP scope)
- **Single shared password** — not per-user auth
- **Income metric** uses `fecha_registro` month (cash-received basis), not plan start date
- **Status computed at runtime** — never stale
