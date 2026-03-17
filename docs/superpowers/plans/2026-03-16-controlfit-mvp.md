# ControlFit MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Streamlit app for personal trainers to manage student plans using Google Sheets as a database.

**Architecture:** Multi-page Streamlit app (`app.py` + `pages/`) with a `data/` module that separates Google Sheets I/O (`sheets.py`) from pure business logic (`calculations.py`). Authentication via a single password stored in `st.secrets`.

**Tech Stack:** Python 3.11+, Streamlit, gspread, pandas, plotly, pytest (tests only)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Create | All runtime dependencies |
| `.streamlit/secrets.toml.example` | Create | Template for secrets setup |
| `.gitignore` | Modify | Ignore secrets.toml |
| `data/__init__.py` | Create | Empty, marks package |
| `data/calculations.py` | Create | Pure status/metric/chart logic |
| `data/sheets.py` | Create | gspread CRUD, error handling |
| `app.py` | Modify | Login screen + session guard |
| `pages/1_Dashboard.py` | Create | 4 metrics + 2 Plotly charts |
| `pages/2_Alumnos.py` | Create | Filtered table with color coding |
| `pages/3_Gestion.py` | Create | Add + edit student forms |
| `README.md` | Modify | Setup + deployment instructions |
| `tests/__init__.py` | Create | Empty |
| `tests/test_calculations.py` | Create | Full unit tests for calculations.py |
| `tests/test_sheets.py` | Create | Unit tests for sheets.py with mocked gspread |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/secrets.toml.example`
- Modify: `.gitignore`
- Create: `data/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.32.0
gspread>=6.0.0
pandas>=2.0.0
plotly>=5.18.0
pytest>=8.0.0
```

- [ ] **Step 2: Create .streamlit/secrets.toml.example**

```toml
# Copy this file to .streamlit/secrets.toml and fill in your values.
# NEVER commit secrets.toml to git.

password = "your_password_here"
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com"
```

- [ ] **Step 3: Update .gitignore to protect secrets**

Add these lines to existing `.gitignore`:
```
.streamlit/secrets.toml
.env
__pycache__/
.pytest_cache/
```

- [ ] **Step 4: Create empty package init files**

Create `data/__init__.py` — empty file.
Create `tests/__init__.py` — empty file.

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .streamlit/secrets.toml.example .gitignore data/__init__.py tests/__init__.py
git commit -m "chore: project setup, dependencies, secrets template"
```

---

## Task 2: data/calculations.py (TDD)

**Files:**
- Create: `tests/test_calculations.py`
- Create: `data/calculations.py`

### Step 2a — Write all failing tests first

- [ ] **Step 1: Create tests/test_calculations.py**

```python
import pandas as pd
import pytest
from datetime import datetime, timedelta
from data.calculations import compute_status, get_metrics, get_monthly_income, get_status_counts, MESES_ES

TODAY = pd.Timestamp.now().normalize()

def make_df(rows):
    """Helper: build a minimal DataFrame from a list of dicts."""
    defaults = {
        "id": "abc123",
        "nombre": "Test",
        "telefono": "",
        "fecha_inicio": TODAY - timedelta(days=30),
        "fecha_fin": TODAY + timedelta(days=30),
        "valor_pagado": 100000.0,
        "notas": "",
        "fecha_registro": pd.Timestamp.now(),
    }
    records = [{**defaults, **r} for r in rows]
    df = pd.DataFrame(records)
    df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"])
    df["fecha_fin"] = pd.to_datetime(df["fecha_fin"])
    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"])
    df["valor_pagado"] = df["valor_pagado"].astype(float)
    return df


# --- compute_status ---

def test_compute_status_activo():
    df = make_df([{"fecha_fin": TODAY + timedelta(days=20)}])
    result = compute_status(df)
    assert result.iloc[0]["estado"] == "ACTIVO"

def test_compute_status_por_vencer():
    df = make_df([{"fecha_fin": TODAY + timedelta(days=5)}])
    result = compute_status(df)
    assert result.iloc[0]["estado"] == "POR VENCER"

def test_compute_status_vencido():
    df = make_df([{"fecha_fin": TODAY - timedelta(days=1)}])
    result = compute_status(df)
    assert result.iloc[0]["estado"] == "VENCIDO"

def test_compute_status_boundary_7_days():
    # exactly 7 days remaining → POR VENCER
    df = make_df([{"fecha_fin": TODAY + timedelta(days=7)}])
    result = compute_status(df)
    assert result.iloc[0]["estado"] == "POR VENCER"

def test_compute_status_boundary_8_days():
    # 8 days remaining → ACTIVO
    df = make_df([{"fecha_fin": TODAY + timedelta(days=8)}])
    result = compute_status(df)
    assert result.iloc[0]["estado"] == "ACTIVO"

def test_compute_status_empty_df():
    df = pd.DataFrame(columns=["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
                                "valor_pagado", "notas", "fecha_registro"])
    result = compute_status(df)
    assert "estado" in result.columns
    assert len(result) == 0


# --- get_metrics ---

def test_get_metrics_counts():
    df = make_df([
        {"fecha_fin": TODAY + timedelta(days=20)},   # ACTIVO
        {"fecha_fin": TODAY + timedelta(days=3)},    # POR VENCER
        {"fecha_fin": TODAY - timedelta(days=5)},    # VENCIDO
    ])
    df = compute_status(df)
    metrics = get_metrics(df)
    assert metrics["activos"] == 1
    assert metrics["por_vencer"] == 1
    assert metrics["vencidos"] == 1

def test_get_metrics_ingresos_mes():
    now = pd.Timestamp.now()
    last_month = now - pd.DateOffset(months=1)
    df = make_df([
        {"valor_pagado": 200000.0, "fecha_registro": now},         # this month
        {"valor_pagado": 100000.0, "fecha_registro": last_month},  # last month
    ])
    df = compute_status(df)
    metrics = get_metrics(df)
    assert metrics["ingresos_mes"] == 200000.0

def test_get_metrics_empty():
    df = pd.DataFrame(columns=["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
                                "valor_pagado", "notas", "fecha_registro", "estado"])
    metrics = get_metrics(df)
    assert metrics == {"activos": 0, "por_vencer": 0, "vencidos": 0, "ingresos_mes": 0.0}


# --- get_monthly_income ---

def test_get_monthly_income_returns_12_months():
    df = make_df([])  # empty — no income
    result = get_monthly_income(df)
    assert len(result) == 12
    assert list(result.columns) == ["mes", "ingresos"]

def test_get_monthly_income_zero_fill():
    df = make_df([])
    result = get_monthly_income(df)
    assert (result["ingresos"] == 0.0).all()

def test_get_monthly_income_aggregates_current_month():
    now = pd.Timestamp.now()
    df = make_df([
        {"valor_pagado": 150000.0, "fecha_registro": now},
        {"valor_pagado": 50000.0, "fecha_registro": now},
    ])
    result = get_monthly_income(df)
    current_month_label = f"{MESES_ES[now.month]} {now.year}"
    row = result[result["mes"] == current_month_label]
    assert not row.empty
    assert row.iloc[0]["ingresos"] == 200000.0


# --- get_status_counts ---

def test_get_status_counts():
    df = make_df([
        {"fecha_fin": TODAY + timedelta(days=20)},
        {"fecha_fin": TODAY + timedelta(days=20)},
        {"fecha_fin": TODAY + timedelta(days=3)},
        {"fecha_fin": TODAY - timedelta(days=1)},
    ])
    df = compute_status(df)
    counts = get_status_counts(df)
    assert counts["ACTIVO"] == 2
    assert counts["POR VENCER"] == 1
    assert counts["VENCIDO"] == 1

def test_get_status_counts_empty():
    df = pd.DataFrame(columns=["estado"])
    counts = get_status_counts(df)
    assert counts == {"ACTIVO": 0, "POR VENCER": 0, "VENCIDO": 0}
```

- [ ] **Step 2: Run tests to confirm all fail**

```bash
pytest tests/test_calculations.py -v
```

Expected: all tests FAIL with `ModuleNotFoundError` or `ImportError`

### Step 2b — Implement calculations.py

- [ ] **Step 3: Create data/calculations.py**

```python
import numpy as np
import pandas as pd

MESES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

EMPTY_COLUMNS = ["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
                 "valor_pagado", "notas", "fecha_registro"]


def compute_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'estado' column: ACTIVO / POR VENCER / VENCIDO."""
    if df.empty:
        result = df.copy()
        result["estado"] = pd.Series(dtype=str)
        return result

    today = pd.Timestamp.now().normalize()
    df = df.copy()
    days_remaining = (df["fecha_fin"] - today).dt.days

    conditions = [days_remaining < 0, days_remaining <= 7]
    choices = ["VENCIDO", "POR VENCER"]
    df["estado"] = pd.Categorical(
        np.select(conditions, choices, default="ACTIVO"),
        categories=["ACTIVO", "POR VENCER", "VENCIDO"],
    )
    return df


def get_metrics(df: pd.DataFrame) -> dict:
    """Return dashboard metrics dict."""
    if df.empty or "estado" not in df.columns:
        return {"activos": 0, "por_vencer": 0, "vencidos": 0, "ingresos_mes": 0.0}

    now = pd.Timestamp.now()
    this_month = df["fecha_registro"].dt.month == now.month
    this_year = df["fecha_registro"].dt.year == now.year

    return {
        "activos": int((df["estado"] == "ACTIVO").sum()),
        "por_vencer": int((df["estado"] == "POR VENCER").sum()),
        "vencidos": int((df["estado"] == "VENCIDO").sum()),
        "ingresos_mes": float(df.loc[this_month & this_year, "valor_pagado"].sum()),
    }


def get_monthly_income(df: pd.DataFrame) -> pd.DataFrame:
    """Return last 12 months of income, zero-filled."""
    now = pd.Timestamp.now()
    months = pd.date_range(end=now, periods=12, freq="MS")
    labels = [f"{MESES_ES[m.month]} {m.year}" for m in months]

    if df.empty:
        return pd.DataFrame({"mes": labels, "ingresos": [0.0] * 12})

    df = df.copy()
    df["mes_key"] = df["fecha_registro"].dt.to_period("M")

    result = []
    for m in months:
        period = m.to_period("M")
        total = df.loc[df["mes_key"] == period, "valor_pagado"].sum()
        label = f"{MESES_ES[m.month]} {m.year}"
        result.append({"mes": label, "ingresos": float(total)})

    return pd.DataFrame(result)


def get_status_counts(df: pd.DataFrame) -> dict:
    """Return count per status."""
    base = {"ACTIVO": 0, "POR VENCER": 0, "VENCIDO": 0}
    if df.empty or "estado" not in df.columns:
        return base
    counts = df["estado"].value_counts().to_dict()
    return {k: int(counts.get(k, 0)) for k in base}
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pytest tests/test_calculations.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add data/calculations.py tests/test_calculations.py
git commit -m "feat: add calculations module with full test coverage"
```

---

## Task 3: data/sheets.py (TDD)

**Files:**
- Create: `tests/test_sheets.py`
- Create: `data/sheets.py`

- [ ] **Step 1: Create tests/test_sheets.py**

```python
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from data.sheets import get_data, append_record, update_record, COLUMNS

SAMPLE_RECORDS = [
    {
        "id": "uuid-001",
        "nombre": "Juan Perez",
        "telefono": "3001234567",
        "fecha_inicio": "01/01/2026",
        "fecha_fin": "31/01/2026",
        "valor_pagado": 150000.0,
        "notas": "",
        "fecha_registro": "2026-01-01T10:00:00",
    }
]


def mock_worksheet(records=None):
    ws = MagicMock()
    ws.get_all_records.return_value = records if records is not None else []
    return ws


# --- get_data ---

def test_get_data_returns_dataframe():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["nombre"] == "Juan Perez"

def test_get_data_parses_dates():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_inicio"])
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_fin"])

def test_get_data_parses_valor_pagado():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet(SAMPLE_RECORDS)):
        df = get_data()
    assert df["valor_pagado"].dtype == float

def test_get_data_empty_sheet_returns_empty_df():
    with patch("data.sheets._get_worksheet", return_value=mock_worksheet([])):
        df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == COLUMNS

def test_get_data_on_error_returns_empty_df():
    ws = MagicMock()
    ws.get_all_records.side_effect = Exception("Network error")
    with patch("data.sheets._get_worksheet", return_value=ws):
        with patch("streamlit.error") as mock_error:
            df = get_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    mock_error.assert_called_once()


# --- append_record ---

def test_append_record_calls_append_row():
    ws = mock_worksheet()
    record = {
        "id": "uuid-new",
        "nombre": "Ana Lopez",
        "telefono": "",
        "fecha_inicio": "01/03/2026",
        "fecha_fin": "31/03/2026",
        "valor_pagado": 200000.0,
        "notas": "",
        "fecha_registro": "2026-03-01T09:00:00",
    }
    with patch("data.sheets._get_worksheet", return_value=ws):
        append_record(record)
    ws.append_row.assert_called_once()
    call_args = ws.append_row.call_args[0][0]
    assert call_args[0] == "uuid-new"
    assert call_args[1] == "Ana Lopez"


# --- update_record ---

def test_update_record_updates_correct_row():
    ws = mock_worksheet(SAMPLE_RECORDS)
    # gspread rows are 1-indexed, row 1 = header, row 2 = first data row
    ws.find.return_value = MagicMock(row=2)
    with patch("data.sheets._get_worksheet", return_value=ws):
        update_record("uuid-001", {**SAMPLE_RECORDS[0], "nombre": "Juan Actualizado"})
    ws.update.assert_called_once()

def test_update_record_not_found_shows_error():
    ws = mock_worksheet([])
    ws.find.side_effect = Exception("Not found")
    with patch("data.sheets._get_worksheet", return_value=ws):
        with patch("streamlit.error") as mock_error:
            update_record("nonexistent-id", {})
    mock_error.assert_called_once()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_sheets.py -v
```

Expected: FAIL with ImportError

- [ ] **Step 3: Create data/sheets.py**

```python
import pandas as pd
import streamlit as st
import gspread

COLUMNS = ["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
           "valor_pagado", "notas", "fecha_registro"]


def _get_worksheet():
    """Return the first worksheet of the configured Google Sheet."""
    client = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    sheet = client.open_by_url(st.secrets["sheet_url"])
    return sheet.sheet1


def get_data() -> pd.DataFrame:
    """Read all rows from Google Sheet. Returns empty DataFrame on error."""
    empty = pd.DataFrame(columns=COLUMNS)
    try:
        ws = _get_worksheet()
        records = ws.get_all_records()
        if not records:
            return empty
        df = pd.DataFrame(records)
        df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], format="%d/%m/%Y", dayfirst=True)
        df["fecha_fin"] = pd.to_datetime(df["fecha_fin"], format="%d/%m/%Y", dayfirst=True)
        df["valor_pagado"] = pd.to_numeric(df["valor_pagado"], errors="coerce").fillna(0.0)
        df["fecha_registro"] = pd.to_datetime(df["fecha_registro"])
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return empty


def append_record(record: dict) -> None:
    """Append a new row to the sheet."""
    try:
        ws = _get_worksheet()
        row = [record.get(col, "") for col in COLUMNS]
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"Error al guardar el registro: {e}")


def update_record(record_id: str, record: dict) -> None:
    """Find row by id and update all fields."""
    try:
        ws = _get_worksheet()
        cell = ws.find(record_id, in_column=1)
        if cell is None:
            st.error("Registro no encontrado. Puede haber sido eliminado de Google Sheets.")
            return
        row_values = [record.get(col, "") for col in COLUMNS]
        ws.update(f"A{cell.row}", [row_values])
    except Exception as e:
        st.error(f"Error al actualizar el registro: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sheets.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add data/sheets.py tests/test_sheets.py
git commit -m "feat: add sheets module with gspread integration and tests"
```

---

## Task 4: app.py — Login Screen

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace app.py with login implementation**

```python
import streamlit as st

st.set_page_config(
    page_title="ControlFit",
    page_icon="💪",
    layout="centered",
)

if st.session_state.get("authenticated"):
    st.switch_page("pages/1_Dashboard.py")

st.title("💪 ControlFit")
st.subheader("Ingresa tu contraseña para continuar")

with st.form("login_form"):
    password = st.text_input("Contraseña", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Ingresar", use_container_width=True)

if submitted:
    if password == st.secrets["password"]:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.error("Contraseña incorrecta. Intenta de nuevo.")
```

- [ ] **Step 2: Create a local .streamlit/secrets.toml for testing**

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:
```toml
password = "test123"
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_REAL_SHEET_ID/edit"
# Add gcp_service_account block with your real credentials
```

- [ ] **Step 3: Run the app and verify login works**

```bash
streamlit run app.py
```

Manual checks:
- Login page appears (not dashboard)
- Wrong password shows error
- Correct password redirects to Dashboard page (even if it shows an error about missing sheet data — that's fine)

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add login screen with session-based auth"
```

---

## Task 5: pages/1_Dashboard.py

**Files:**
- Create: `pages/1_Dashboard.py`

- [ ] **Step 1: Create pages/1_Dashboard.py**

```python
import streamlit as st
import plotly.express as px
from data.sheets import get_data
from data.calculations import compute_status, get_metrics, get_monthly_income, get_status_counts

st.set_page_config(page_title="Dashboard — ControlFit", page_icon="📊", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

st.title("📊 Dashboard")

df_raw = get_data()
df = compute_status(df_raw) if not df_raw.empty else df_raw
metrics = get_metrics(df)

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Alumnos Activos", metrics["activos"])
col2.metric("Por Vencer (7 días)", metrics["por_vencer"])
col3.metric("Vencidos", metrics["vencidos"])

ingresos_fmt = f"$ {metrics['ingresos_mes']:,.0f}".replace(",", ".")
col4.metric("Ingresos del Mes", ingresos_fmt)

st.divider()

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Ingresos por Mes")
    income_df = get_monthly_income(df_raw)
    fig_bar = px.bar(
        income_df,
        x="mes",
        y="ingresos",
        labels={"mes": "Mes", "ingresos": "Ingresos (COP)"},
        color_discrete_sequence=["#2196F3"],
    )
    fig_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.subheader("Estado de Alumnos")
    counts = get_status_counts(df)
    if sum(counts.values()) > 0:
        fig_pie = px.pie(
            names=list(counts.keys()),
            values=list(counts.values()),
            color=list(counts.keys()),
            color_discrete_map={
                "ACTIVO": "#28a745",
                "POR VENCER": "#ffc107",
                "VENCIDO": "#dc3545",
            },
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay alumnos registrados aún.")
```

- [ ] **Step 2: Verify dashboard in browser**

Open the app, log in, and check:
- 4 metric cards appear (all 0 on empty sheet)
- Bar chart shows 12 months (all 0)
- Pie chart shows info message when empty
- No errors thrown

- [ ] **Step 3: Commit**

```bash
git add pages/1_Dashboard.py
git commit -m "feat: add dashboard with metrics and Plotly charts"
```

---

## Task 6: pages/2_Alumnos.py

**Files:**
- Create: `pages/2_Alumnos.py`

- [ ] **Step 1: Create pages/2_Alumnos.py**

```python
import streamlit as st
import pandas as pd
from data.sheets import get_data
from data.calculations import compute_status

st.set_page_config(page_title="Alumnos — ControlFit", page_icon="👥", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

st.title("👥 Alumnos")

df_raw = get_data()

if df_raw.empty:
    st.info("No hay alumnos registrados. Ve a Gestión para agregar el primero.")
    st.stop()

df = compute_status(df_raw)

# --- Filter ---
estados = ["Todos", "ACTIVO", "POR VENCER", "VENCIDO"]
filtro = st.selectbox("Filtrar por estado", estados)

if filtro != "Todos":
    df = df[df["estado"] == filtro]

if df.empty:
    st.info(f"No hay alumnos con estado {filtro}.")
    st.stop()

# --- Prepare display ---
display = df[["nombre", "telefono", "fecha_inicio", "fecha_fin", "valor_pagado", "estado", "notas"]].copy()
display["fecha_inicio"] = display["fecha_inicio"].dt.strftime("%d/%m/%Y")
display["fecha_fin"] = display["fecha_fin"].dt.strftime("%d/%m/%Y")
display["valor_pagado"] = display["valor_pagado"].apply(lambda x: f"$ {x:,.0f}".replace(",", "."))

# --- Color styling ---
COLOR_MAP = {
    "ACTIVO": "background-color: #d4edda",
    "POR VENCER": "background-color: #fff3cd",
    "VENCIDO": "background-color: #f8d7da",
}

def style_row(row):
    color = COLOR_MAP.get(row["estado"], "")
    return [color] * len(row)

styled = display.style.apply(style_row, axis=1)

st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption(f"Mostrando {len(df)} registro(s).")
```

- [ ] **Step 2: Add a test record in Google Sheet and verify**

Add one row manually to the Google Sheet with:
- fecha_inicio = today - 10 days (DD/MM/YYYY)
- fecha_fin = today + 20 days
- valor_pagado = 150000

Then verify:
- Row appears in green (ACTIVO)
- Filter by ACTIVO shows it, filter by VENCIDO hides it

- [ ] **Step 3: Commit**

```bash
git add pages/2_Alumnos.py
git commit -m "feat: add student table with status color coding"
```

---

## Task 7: pages/3_Gestion.py

**Files:**
- Create: `pages/3_Gestion.py`

- [ ] **Step 1: Create pages/3_Gestion.py**

```python
import streamlit as st
import uuid
from datetime import datetime, date
from data.sheets import get_data, append_record, update_record

st.set_page_config(page_title="Gestión — ControlFit", page_icon="⚙️", layout="centered")

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

st.title("⚙️ Gestión de Alumnos")

tab_add, tab_edit = st.tabs(["➕ Agregar Alumno", "✏️ Editar Alumno"])


# ──────────────── TAB 1: AGREGAR ────────────────

with tab_add:
    st.subheader("Nuevo Alumno")

    with st.form("form_agregar", clear_on_submit=True):
        nombre = st.text_input("Nombre *", placeholder="Ej: Juan Pérez")
        telefono = st.text_input("Teléfono / WhatsApp", placeholder="Ej: 3001234567")
        col1, col2 = st.columns(2)
        fecha_inicio = col1.date_input("Fecha de inicio *", value=date.today())
        fecha_fin = col2.date_input("Fecha de fin *", value=date.today())
        valor_pagado = st.number_input("Valor pagado (COP) *", min_value=0.0, step=1000.0, format="%.0f")
        notas = st.text_area("Notas", placeholder="Objetivo, lesiones, observaciones...")
        submitted = st.form_submit_button("Guardar alumno", use_container_width=True)

    if submitted:
        if not nombre.strip():
            st.error("El nombre es obligatorio.")
        elif fecha_fin < fecha_inicio:
            st.error("La fecha de fin no puede ser anterior a la fecha de inicio.")
        else:
            record = {
                "id": str(uuid.uuid4()),
                "nombre": nombre.strip(),
                "telefono": telefono.strip(),
                "fecha_inicio": fecha_inicio.strftime("%d/%m/%Y"),
                "fecha_fin": fecha_fin.strftime("%d/%m/%Y"),
                "valor_pagado": float(valor_pagado),
                "notas": notas.strip(),
                "fecha_registro": datetime.utcnow().isoformat(),
            }
            append_record(record)
            st.success(f"✅ Alumno **{nombre}** guardado exitosamente.")


# ──────────────── TAB 2: EDITAR ────────────────

with tab_edit:
    st.subheader("Editar Registro Existente")

    df = get_data()

    if df.empty:
        st.info("No hay registros para editar.")
    else:
        # Build dropdown labels with id suffix to disambiguate
        df["_label"] = (
            df["nombre"] + " — "
            + df["fecha_inicio"].dt.strftime("%d/%m/%Y") + " → "
            + df["fecha_fin"].dt.strftime("%d/%m/%Y")
            + " (id: " + df["id"].str[:8] + ")"
        )
        label_to_id = dict(zip(df["_label"], df["id"]))
        selected_label = st.selectbox("Selecciona un registro", list(label_to_id.keys()))
        selected_id = label_to_id[selected_label]
        row = df[df["id"] == selected_id].iloc[0]

        with st.form("form_editar"):
            nombre_e = st.text_input("Nombre *", value=row["nombre"])
            telefono_e = st.text_input("Teléfono / WhatsApp", value=row["telefono"])
            col1, col2 = st.columns(2)
            fecha_inicio_e = col1.date_input("Fecha de inicio *", value=row["fecha_inicio"].date())
            fecha_fin_e = col2.date_input("Fecha de fin *", value=row["fecha_fin"].date())
            valor_e = st.number_input("Valor pagado (COP) *", value=float(row["valor_pagado"]),
                                      min_value=0.0, step=1000.0, format="%.0f")
            notas_e = st.text_area("Notas", value=row["notas"])
            save = st.form_submit_button("Guardar cambios", use_container_width=True)

        if save:
            if not nombre_e.strip():
                st.error("El nombre es obligatorio.")
            elif fecha_fin_e < fecha_inicio_e:
                st.error("La fecha de fin no puede ser anterior a la fecha de inicio.")
            else:
                updated = {
                    "id": selected_id,
                    "nombre": nombre_e.strip(),
                    "telefono": telefono_e.strip(),
                    "fecha_inicio": fecha_inicio_e.strftime("%d/%m/%Y"),
                    "fecha_fin": fecha_fin_e.strftime("%d/%m/%Y"),
                    "valor_pagado": float(valor_e),
                    "notas": notas_e.strip(),
                    "fecha_registro": row["fecha_registro"].isoformat(),
                }
                update_record(selected_id, updated)
                st.success("✅ Registro actualizado exitosamente.")
```

- [ ] **Step 2: Verify add flow**

- Go to Gestión → Agregar Alumno
- Add a student → verify row appears in Google Sheet
- Leave nombre empty → verify validation error
- Set fecha_fin before fecha_inicio → verify validation error

- [ ] **Step 3: Verify edit flow**

- Go to Gestión → Editar Alumno
- Select the added record from dropdown
- Change the name → Save → verify change in Google Sheet

- [ ] **Step 4: Commit**

```bash
git add pages/3_Gestion.py
git commit -m "feat: add student management forms (add + edit)"
```

---

## Task 8: README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md with full setup guide**

````markdown
# ControlFit 💪

La forma más simple de controlar alumnos de entrenamiento personal.

Digitaliza tu libreta: ve quién está activo, quién renueva pronto y cuánto ingresó este mes.

---

## Requisitos previos

- Python 3.11+
- Cuenta de Google
- Acceso a [Google Cloud Console](https://console.cloud.google.com/)

---

## 1. Crear la hoja de Google Sheets

1. Crea una nueva hoja en [Google Sheets](https://sheets.google.com)
2. En la primera fila, agrega exactamente estos encabezados (respeta mayúsculas y guiones bajos):

```
id | nombre | telefono | fecha_inicio | fecha_fin | valor_pagado | notas | fecha_registro
```

3. Copia la URL de la hoja (la necesitarás más adelante)

---

## 2. Configurar credenciales de Google

### 2a. Crear proyecto y habilitar APIs

1. Ve a [Google Cloud Console](https://console.cloud.google.com/) → Nuevo proyecto
2. En el menú, ve a **APIs y Servicios → Biblioteca**
3. Busca y habilita: **Google Sheets API** y **Google Drive API**

### 2b. Crear cuenta de servicio

1. Ve a **APIs y Servicios → Credenciales → Crear credenciales → Cuenta de servicio**
2. Dale un nombre, haz clic en Crear
3. En la cuenta creada, ve a la pestaña **Claves → Agregar clave → JSON**
4. Descarga el archivo JSON — guárdalo de forma segura

### 2c. Compartir la hoja con la cuenta de servicio

1. Abre el JSON descargado y copia el valor de `client_email` (termina en `.iam.gserviceaccount.com`)
2. Ve a tu Google Sheet → Compartir → pega ese email → rol **Editor** → Listo

---

## 3. Configurar secrets locales

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml` y completa:

- `password`: la contraseña que usarás para entrar a la app
- `sheet_url`: la URL de tu Google Sheet
- `[gcp_service_account]`: copia **todos** los campos del JSON descargado como claves TOML

---

## 4. Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501` e ingresa la contraseña configurada.

---

## 5. Desplegar en Streamlit Community Cloud

1. Sube el proyecto a GitHub (asegúrate de que `.streamlit/secrets.toml` esté en `.gitignore`)
2. Ve a [share.streamlit.io](https://share.streamlit.io) → New app
3. Selecciona tu repositorio y `app.py` como archivo principal
4. Ve a **Advanced settings → Secrets** y pega el contenido de tu `secrets.toml`
5. Haz clic en Deploy

---

## Estructura del proyecto

```
controlfit/
├── app.py                  ← Login y punto de entrada
├── pages/
│   ├── 1_Dashboard.py      ← Métricas e ingresos
│   ├── 2_Alumnos.py        ← Tabla con estados
│   └── 3_Gestion.py        ← Agregar y editar alumnos
├── data/
│   ├── sheets.py           ← Conexión con Google Sheets
│   └── calculations.py     ← Lógica de estados y métricas
├── tests/                  ← Tests unitarios
└── requirements.txt
```

---

## Nota sobre eliminar registros

En esta versión MVP, los registros se eliminan directamente en Google Sheets. Simplemente borra la fila correspondiente.
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add full setup and deployment guide"
```

---

## Task 9: Run All Tests + Final Verification

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 2: Run complete manual verification checklist**

From the spec:
1. `streamlit run app.py` → login screen appears, not dashboard
2. Wrong password → error message, no access
3. Correct password → redirected to Dashboard
4. Dashboard shows 0 metrics on empty sheet (no errors)
5. Gestión → add student with today as start, today+30 as end → row in Google Sheet with UUID
6. Alumnos → row shows ACTIVO (green)
7. Dashboard → Activos = 1, Ingresos = payment amount
8. Gestión → edit record → change saved in Google Sheet
9. Add record with fecha_fin = today+3 → POR VENCER (yellow)
10. Add record with fecha_fin = yesterday → VENCIDO (red)
11. Bar chart shows correct bar for current month

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: ControlFit MVP complete"
```
