# Dashboard Redesign — Action-First Layout

**Date**: 2026-03-17
**Status**: Draft

## Context

ControlFit's Dashboard currently shows 4 KPI cards and 2 charts but lacks actionable information. A personal trainer opening this daily needs to immediately see which students require attention (expiring soon or already expired) and be able to contact them via WhatsApp — without navigating to another page. The trainer also wants a projected income metric to help plan finances.

## Design Decision

**Approach A: Action-First Stacked Layout** — KPIs at top, action tables in the middle, trend charts at the bottom. Uses only native Streamlit components (no custom HTML).

## Layout Specification

```
┌──────────────────────────────────────────────────────────────┐
│  [Activos]  [Por Vencer]  [Vencidos]  [Ingresos Mes]  [Proy]│  ← 5 KPI cards
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  "⚠️ Próximos a Vencer"        "❌ Ya Vencidos"              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐  │
│  │ Nombre │Vence│WA│ $ │    │ Nombre │Venció│Días│WA│ $   │  │
│  │ Maria  │20/03│📱│150k│    │ Juan   │10/03 │ 7  │📱│120k │  │
│  │ Pedro  │22/03│📱│100k│    │ Ana    │05/03 │ 12 │📱│80k  │  │
│  └─────────────────────┘    └─────────────────────────────┘  │
│                                                              │
│  (Si ambas tablas vacías: "✅ ¡Todo al día! ...")            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [Ingresos por Mes - Barras]    [Estado de Alumnos - Donut]  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

On mobile (narrow screens), Streamlit auto-stacks columns vertically.

## Components

### 1. KPI Cards (Row 1) — 5 metrics

| # | Label | Source | Delta |
|---|-------|--------|-------|
| 1 | Alumnos Activos | `metrics["activos"]` | — |
| 2 | Por Vencer (7 días) | `metrics["por_vencer"]` | — |
| 3 | Vencidos | `metrics["vencidos"]` | — |
| 4 | Ingresos del Mes | `metrics["ingresos_mes"]` | COP formatted |
| 5 | Proyección Prox. Mes | `get_projected_income(df)` | "X por renovar" |

KPI #5 shows the sum of `valor_pagado` from all students whose status is POR VENCER or VENCIDO. The delta text shows the count of those students. Uses `delta_color="off"` since this is informational, not a positive/negative change.

### 2. Action Table: "Próximos a Vencer" (Left)

| Column | Source | Format |
|--------|--------|--------|
| Nombre | `nombre` | Text |
| Vence | `fecha_fin` | DD/MM/YYYY |
| WhatsApp | `telefono` → `wa.me/57...` | LinkColumn, display "Escribir" |
| Valor | `valor_pagado` | $ X.XXX (COP) |

Sorted by `fecha_fin` ascending (most urgent first). Yellow subheader.

### 3. Action Table: "Ya Vencidos" (Right)

| Column | Source | Format |
|--------|--------|--------|
| Nombre | `nombre` | Text |
| Venció | `fecha_fin` | DD/MM/YYYY |
| Días vencido | `(today - fecha_fin).days` | Integer |
| WhatsApp | `telefono` → `wa.me/57...` | LinkColumn, display "Escribir" |
| Valor | `valor_pagado` | $ X.XXX (COP) |

Sorted by `fecha_fin` descending (most recently expired first). Red subheader.

### 4. Empty State

If no students are POR VENCER and no students are VENCIDO, replace both tables with:
`st.success("✅ ¡Todo al día! No hay alumnos por vencer ni vencidos.")`

### 5. Charts (Row 3) — unchanged

- Left: Monthly income bar chart (Plotly, last 12 months)
- Right: Status distribution donut chart (Plotly)

Same implementation as current Dashboard.

## New Functions in `data/calculations.py`

### `get_expiring_students(df: pd.DataFrame) -> pd.DataFrame`
- Input: DataFrame with `estado` column (output of `compute_status`)
- Filters `_current_per_student(df)` to `estado == "POR VENCER"`
- Returns columns: `nombre, telefono, fecha_fin, valor_pagado`
- Sorted by `fecha_fin` ascending

### `get_expired_students(df: pd.DataFrame) -> pd.DataFrame`
- Input: DataFrame with `estado` column
- Filters `_current_per_student(df)` to `estado == "VENCIDO"`
- Adds `dias_vencido` column: `(today - fecha_fin).days`
- Returns columns: `nombre, telefono, fecha_fin, dias_vencido, valor_pagado`
- Sorted by `fecha_fin` descending (most recently expired first)

### `get_projected_income(df: pd.DataFrame) -> tuple[float, int]`
- Input: DataFrame with `estado` column
- Uses `_current_per_student(df)` filtered to `estado in ("POR VENCER", "VENCIDO")`
- Returns `(total_valor_pagado, count_students)` — the projected income if all renew at their last paid amount, plus the count for the delta display
- Returns `(0.0, 0)` for empty DataFrames

### `format_whatsapp_url(telefono: str) -> str`
- Strips non-digit characters from phone string
- If 10 digits: prepends "57" (Colombia country code)
- If 12 digits starting with "57": uses as-is
- Any other length: returns empty string (invalid phone)
- Returns `https://wa.me/{digits}` or empty string if invalid/empty
- Empty/invalid phones produce empty strings → UI shows empty cell (no broken link)

## WhatsApp Link Implementation

Use `st.column_config.LinkColumn` in the dataframe configuration:
- Display text: "Escribir"
- URL: generated by `format_whatsapp_url()` applied to each row's `telefono`
- The link column renders as a clickable hyperlink within `st.dataframe`

The WhatsApp URL column is computed as a new column in the DataFrame before passing to `st.dataframe`.

## Files to Modify

| File | Change |
|------|--------|
| `data/calculations.py` | Add `get_expiring_students`, `get_expired_students`, `get_projected_income`, `format_whatsapp_url` |
| `pages/1_Dashboard.py` | Rewrite layout: 5 KPIs → action tables → charts |
| `tests/test_calculations.py` | Add tests for all 4 new functions |

## Testing Plan

### New unit tests for `data/calculations.py`:

1. `get_expiring_students` — returns only POR VENCER students, sorted correctly
2. `get_expiring_students` — empty when no one is expiring
3. `get_expired_students` — returns only VENCIDO students with correct `dias_vencido`
4. `get_expired_students` — sorted by fecha_fin descending
5. `get_expired_students` — empty when no one is expired
6. `get_projected_income` — sums valor_pagado for POR VENCER + VENCIDO
7. `get_projected_income` — returns (0.0, 0) for empty DataFrame
8. `format_whatsapp_url` — 10-digit number gets 57 prefix
9. `format_whatsapp_url` — number with country code preserved
10. `format_whatsapp_url` — empty/invalid returns empty string

### Manual verification:
- Run `uv run streamlit run app.py` and verify:
  - 5 KPIs render correctly
  - Action tables show correct students with clickable WhatsApp links
  - "Días vencido" shows correct count
  - Empty state message appears when no students need attention
  - Charts render below the tables
  - Layout works on narrow browser window (simulating mobile)
