# ControlFit MVP — Design Spec
**Date:** 2026-03-16
**Status:** Approved

---

## Problem & Goal

Personal trainers manage their students using a physical notebook. They record student names, plan start/end dates, and payment amounts. The goal is to digitize this process with a minimal, practical app that answers three key questions at a glance:

1. How many active students do I have?
2. Who needs to renew soon?
3. How much income came in this month?

---

## Scope

This is an MVP — not a full CRM or ERP. It replaces the notebook with a smarter, filtered view of the same information.

**Known deferred features (not in MVP):**
- Delete records (accidental duplicates must be removed directly in Google Sheets)

---

## Data Model

**Google Sheet:** single sheet, one row per plan period (not per student). A student can have multiple rows over time (historical renewals).

| Field | Type | Notes |
|---|---|---|
| `id` | string | UUID, auto-generated on creation |
| `nombre` | string | Student name |
| `telefono` | string | WhatsApp number (optional) |
| `fecha_inicio` | string | Stored as DD/MM/YYYY |
| `fecha_fin` | string | Stored as DD/MM/YYYY |
| `valor_pagado` | float | In COP (Colombian Pesos) |
| `notas` | string | Free text, optional |
| `fecha_registro` | string | ISO datetime string, auto-generated on creation |

**Date handling:**
- `st.date_input()` returns a Python `date` object; serialize to string using `date.strftime("%d/%m/%Y")` before saving
- When reading from sheet, parse date columns with `pd.to_datetime(df["fecha_inicio"], format="%d/%m/%Y", dayfirst=True)` to get `datetime64` for calculations
- `fecha_registro` is stored as ISO format (`datetime.utcnow().isoformat()`) and parsed with `pd.to_datetime`

**Status logic** (computed dynamically, never stored):
- `VENCIDO` → `today > fecha_fin`
- `POR VENCER` → `today <= fecha_fin` AND `(fecha_fin - today) <= 7 days`
- `ACTIVO` → everything else (today >= fecha_inicio AND today <= fecha_fin, more than 7 days remaining)

**Income aggregation:** `valor_pagado` grouped by month of `fecha_registro` (cash-received basis — the month the record was entered, not the month the plan starts). This ensures the Dashboard "Ingresos del mes" reflects money actually received this month.

---

## Architecture

**Pattern:** Multi-page Streamlit app with separate data module.

```
controlfit/
├── app.py                      ← Entry point: login + session guard
├── pages/
│   ├── 1_Dashboard.py          ← Metrics + charts
│   ├── 2_Alumnos.py            ← Student table with status colors
│   └── 3_Gestion.py            ← Add / edit student forms
├── data/
│   ├── sheets.py               ← Google Sheets CRUD via gspread
│   └── calculations.py         ← Status, metrics, chart data
├── .streamlit/
│   └── secrets.toml            ← Google credentials + sheet_url + password (not committed)
├── .streamlit/secrets.toml.example  ← Template with all required keys
├── requirements.txt
└── README.md
```

---

## Module Contracts

### `data/sheets.py`

```python
get_data() -> pd.DataFrame
# Reads all rows from Google Sheet.
# Returns empty DataFrame with correct columns if sheet has no data rows.
# On gspread/network error: calls st.error() with user-friendly message and returns empty DataFrame.
# Columns: id, nombre, telefono, fecha_inicio, fecha_fin, valor_pagado, notas, fecha_registro
# fecha_inicio and fecha_fin are parsed to datetime64; valor_pagado to float.

append_record(record: dict) -> None
# Appends a new row to the sheet.
# On error: calls st.error() with message; does not raise.

update_record(record_id: str, record: dict) -> None
# Fetches all rows, finds the row whose 'id' column matches record_id (linear scan).
# If not found: calls st.error("Registro no encontrado") and returns without writing.
# If found: updates all fields in that row via gspread worksheet.update().
# On error: calls st.error() with message.
```

**Auth:** Uses `gspread.service_account_from_dict(st.secrets["gcp_service_account"])`.
**Sheet identification:** Opens sheet by URL via `client.open_by_url(st.secrets["sheet_url"])`, accesses first worksheet.

### `data/calculations.py`

```python
compute_status(df: pd.DataFrame) -> pd.DataFrame
# Adds 'estado' column: ACTIVO / POR VENCER / VENCIDO
# Input df must have fecha_fin as datetime64. Returns copy of df with estado column.
# Safe to call with empty DataFrame (returns empty df with estado column).

get_metrics(df: pd.DataFrame) -> dict
# Returns dict: {activos: int, por_vencer: int, vencidos: int, ingresos_mes: float}
# ingresos_mes = sum of valor_pagado where month(fecha_registro) == current month/year
# Safe to call with empty DataFrame (returns zeroed dict).

get_monthly_income(df: pd.DataFrame) -> pd.DataFrame
# Returns DataFrame with columns: mes (string "MMM YYYY"), ingresos (float)
# Covers last 12 months. Months with no income have 0 value (not omitted).
# Safe to call with empty DataFrame (returns 12 rows with 0 income).

get_status_counts(df: pd.DataFrame) -> dict
# Returns {ACTIVO: int, POR VENCER: int, VENCIDO: int}
# Safe to call with empty DataFrame (returns zeroed dict).
```

---

## Screens

### `app.py` — Login
- Full-page password input (`st.text_input(type="password")`)
- On success: set `st.session_state.authenticated = True`, call `st.rerun()`
- On failure: show `st.error("Contraseña incorrecta")`
- Password stored in `st.secrets["password"]`

**Auth guard pattern** (used in every page file):
```python
if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()
```

### `pages/1_Dashboard.py` — Dashboard
- Auth guard at top
- **4 st.metric cards** in a row:
  - Alumnos Activos
  - Por Vencer (próximos 7 días)
  - Vencidos
  - Ingresos del Mes (formatted as `$ {value:,.0f}` COP)
- **Bar chart** (Plotly): Monthly income — last 12 months, x-axis = "MMM YYYY"
- **Pie/donut chart** (Plotly): Status distribution (Activo / Por Vencer / Vencido)

### `pages/2_Alumnos.py` — Student Table
- Auth guard at top
- Filter selectbox: Todos / Activos / Por Vencer / Vencidos
- `st.dataframe` with Pandas Styler color coding:
  - ACTIVO → green background (`#d4edda`)
  - POR VENCER → yellow/orange background (`#fff3cd`)
  - VENCIDO → red background (`#f8d7da`)
- Columns shown: nombre, telefono, fecha_inicio (formatted DD/MM/YYYY), fecha_fin (formatted DD/MM/YYYY), valor_pagado, estado, notas

### `pages/3_Gestion.py` — Management
- Auth guard at top
- Two tabs (`st.tabs`): ["➕ Agregar Alumno", "✏️ Editar Alumno"]

**Tab 1 — Agregar Alumno:**
- Form fields: nombre*, teléfono, fecha_inicio* (date_input), fecha_fin* (date_input), valor_pagado* (number_input), notas
- Auto-generates: id (UUID4), fecha_registro (utcnow ISO string)
- Serialize dates to DD/MM/YYYY string before saving
- Button: "Guardar alumno"
- On success: `st.success("Alumno guardado exitosamente")`

**Tab 2 — Editar Alumno:**
- Dropdown built from all records, label format: `"nombre — DD/MM/YYYY → DD/MM/YYYY (id: {id[:8]})"` to disambiguate duplicates
- Pre-fills all form fields from selected record
- Button: "Guardar cambios"
- On success: `st.success("Registro actualizado exitosamente")`

---

## Secrets Configuration

**`.streamlit/secrets.toml`** (local, not committed to git):
```toml
password = "your_password_here"
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com"
```
**Note:** Copy all fields from the downloaded service account JSON file. Each key in the JSON becomes a key in the `[gcp_service_account]` TOML block.

---

## Locale & Formatting
- Country: Colombia
- Currency: COP (Colombian Pesos)
- Date format storage: DD/MM/YYYY (string)
- Date format display: DD/MM/YYYY
- Currency display: `$ 250.000` (Colombian notation, `.` as thousands separator)

---

## Dependencies
```
streamlit
gspread
pandas
plotly
google-auth
```

---

## README Sections Required
1. Prerequisites (Google Cloud Console, service account setup, enabling Google Sheets API)
2. Creating the Google Sheet (exact column headers, exact names to match)
3. Sharing the sheet with the service account email address
4. Setting up `.streamlit/secrets.toml` locally (copy from secrets.toml.example)
5. Running locally (`streamlit run app.py`)
6. Deploying to Streamlit Community Cloud (how to add secrets in the dashboard as TOML)

---

## Verification Plan
1. Run `streamlit run app.py` locally → login screen appears, not the dashboard
2. Enter wrong password → error message shown, no access
3. Enter correct password → redirected to Dashboard
4. Dashboard shows all 0 metrics on empty sheet (no errors thrown)
5. Go to Gestión → add a student with today as fecha_inicio, today+30 as fecha_fin → row appears in Google Sheet with UUID id
6. Go to Alumnos → row shows with ACTIVO status and green color
7. Go to Dashboard → Alumnos Activos = 1, Ingresos del Mes = payment amount
8. Go to Gestión → Editar tab → find the record in dropdown (with id suffix) → change nombre → save → Google Sheet reflects change
9. Add a record with `fecha_fin` = today+3 → appears as POR VENCER (yellow)
10. Add a record with `fecha_fin` = yesterday → appears as VENCIDO (red), not in active count
11. Ingresos por mes bar chart shows correct bar for current month
