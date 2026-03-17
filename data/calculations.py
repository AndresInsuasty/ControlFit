import numpy as np
import pandas as pd

MESES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}


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
