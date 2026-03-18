import pandas as pd
import pytest
from datetime import datetime, timedelta
from data.calculations import (
    compute_status, get_metrics, get_monthly_income, get_status_counts,
    get_expiring_students, get_expired_students, get_projected_income,
    format_whatsapp_url, MESES_ES,
)

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
    columns = list(defaults.keys())
    records = [{**defaults, **r} for r in rows]
    df = pd.DataFrame(records, columns=columns)
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
        {"nombre": "A", "fecha_fin": TODAY + timedelta(days=20)},   # ACTIVO
        {"nombre": "B", "fecha_fin": TODAY + timedelta(days=3)},    # POR VENCER
        {"nombre": "C", "fecha_fin": TODAY - timedelta(days=5)},    # VENCIDO
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
        {"nombre": "A", "fecha_fin": TODAY + timedelta(days=20)},
        {"nombre": "B", "fecha_fin": TODAY + timedelta(days=20)},
        {"nombre": "C", "fecha_fin": TODAY + timedelta(days=3)},
        {"nombre": "D", "fecha_fin": TODAY - timedelta(days=1)},
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


# --- get_expiring_students ---

def test_get_expiring_students_returns_por_vencer():
    df = make_df([
        {"nombre": "Maria", "fecha_fin": TODAY + timedelta(days=5)},
        {"nombre": "Juan", "fecha_fin": TODAY + timedelta(days=20)},
        {"nombre": "Ana", "fecha_fin": TODAY - timedelta(days=3)},
    ])
    df = compute_status(df)
    result = get_expiring_students(df)
    assert len(result) == 1
    assert result.iloc[0]["nombre"] == "Maria"

def test_get_expiring_students_sorted_by_fecha_fin():
    df = make_df([
        {"nombre": "Maria", "fecha_fin": TODAY + timedelta(days=6)},
        {"nombre": "Pedro", "fecha_fin": TODAY + timedelta(days=2)},
    ])
    df = compute_status(df)
    result = get_expiring_students(df)
    assert result.iloc[0]["nombre"] == "Pedro"
    assert result.iloc[1]["nombre"] == "Maria"

def test_get_expiring_students_empty():
    df = make_df([
        {"nombre": "Juan", "fecha_fin": TODAY + timedelta(days=20)},
    ])
    df = compute_status(df)
    result = get_expiring_students(df)
    assert result.empty


# --- get_expired_students ---

def test_get_expired_students_returns_vencido():
    df = make_df([
        {"nombre": "Ana", "fecha_fin": TODAY - timedelta(days=5)},
        {"nombre": "Luis", "fecha_fin": TODAY + timedelta(days=20)},
    ])
    df = compute_status(df)
    result = get_expired_students(df)
    assert len(result) == 1
    assert result.iloc[0]["nombre"] == "Ana"
    assert result.iloc[0]["dias_vencido"] == 5

def test_get_expired_students_sorted_desc():
    df = make_df([
        {"nombre": "Ana", "fecha_fin": TODAY - timedelta(days=10)},
        {"nombre": "Carlos", "fecha_fin": TODAY - timedelta(days=2)},
    ])
    df = compute_status(df)
    result = get_expired_students(df)
    assert result.iloc[0]["nombre"] == "Carlos"
    assert result.iloc[1]["nombre"] == "Ana"

def test_get_expired_students_empty():
    df = make_df([
        {"nombre": "Juan", "fecha_fin": TODAY + timedelta(days=20)},
    ])
    df = compute_status(df)
    result = get_expired_students(df)
    assert result.empty


# --- get_projected_income ---

def test_get_projected_income_sums_por_vencer_and_vencido():
    df = make_df([
        {"nombre": "Maria", "fecha_fin": TODAY + timedelta(days=3), "valor_pagado": 100000.0},
        {"nombre": "Ana", "fecha_fin": TODAY - timedelta(days=5), "valor_pagado": 80000.0},
        {"nombre": "Luis", "fecha_fin": TODAY + timedelta(days=20), "valor_pagado": 150000.0},
    ])
    df = compute_status(df)
    total, count = get_projected_income(df)
    assert total == 180000.0
    assert count == 2

def test_get_projected_income_excludes_activo():
    df = make_df([
        {"nombre": "Luis", "fecha_fin": TODAY + timedelta(days=20), "valor_pagado": 150000.0},
    ])
    df = compute_status(df)
    total, count = get_projected_income(df)
    assert total == 0.0
    assert count == 0

def test_get_projected_income_empty():
    df = pd.DataFrame(columns=["id", "nombre", "telefono", "fecha_inicio", "fecha_fin",
                                "valor_pagado", "notas", "fecha_registro", "estado"])
    total, count = get_projected_income(df)
    assert total == 0.0
    assert count == 0


# --- format_whatsapp_url ---

def test_format_whatsapp_url_10_digits():
    assert format_whatsapp_url("3001234567") == "https://wa.me/573001234567"

def test_format_whatsapp_url_with_formatting():
    assert format_whatsapp_url("+57 300 123 4567") == "https://wa.me/573001234567"

def test_format_whatsapp_url_empty():
    assert format_whatsapp_url("") == ""

def test_format_whatsapp_url_float_from_sheets():
    # Sheets stores phone as number → pandas reads as float
    assert format_whatsapp_url(3001234567.0) == "https://wa.me/573001234567"

def test_format_whatsapp_url_none():
    assert format_whatsapp_url(None) == ""
