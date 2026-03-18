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


def _current_per_student(df: pd.DataFrame) -> pd.DataFrame:
    """One row per student: the plan with the latest fecha_fin."""
    return df.loc[df.groupby("nombre")["fecha_fin"].idxmax()]


def get_metrics(df: pd.DataFrame) -> dict:
    """Return dashboard metrics dict."""
    if df.empty or "estado" not in df.columns:
        return {"activos": 0, "por_vencer": 0, "vencidos": 0, "ingresos_mes": 0.0}

    now = pd.Timestamp.now()
    this_month = df["fecha_registro"].dt.month == now.month
    this_year = df["fecha_registro"].dt.year == now.year

    current = _current_per_student(df)

    return {
        "activos": int((current["estado"] == "ACTIVO").sum()),
        "por_vencer": int((current["estado"] == "POR VENCER").sum()),
        "vencidos": int((current["estado"] == "VENCIDO").sum()),
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


def get_expiring_students(df: pd.DataFrame) -> pd.DataFrame:
    """Return POR VENCER students (one per student, most urgent first)."""
    if df.empty or "estado" not in df.columns:
        return pd.DataFrame(columns=["nombre", "telefono", "fecha_fin", "valor_pagado"])
    current = _current_per_student(df)
    expiring = current[current["estado"] == "POR VENCER"].copy()
    expiring = expiring.sort_values("fecha_fin", ascending=True)
    return expiring[["nombre", "telefono", "fecha_fin", "valor_pagado"]].reset_index(drop=True)


def get_expired_students(df: pd.DataFrame) -> pd.DataFrame:
    """Return VENCIDO students with dias_vencido (one per student, most recent first)."""
    if df.empty or "estado" not in df.columns:
        return pd.DataFrame(columns=["nombre", "telefono", "fecha_fin", "dias_vencido", "valor_pagado"])
    current = _current_per_student(df)
    expired = current[current["estado"] == "VENCIDO"].copy()
    today = pd.Timestamp.now().normalize()
    expired["dias_vencido"] = (today - expired["fecha_fin"]).dt.days
    expired = expired.sort_values("fecha_fin", ascending=False)
    return expired[["nombre", "telefono", "fecha_fin", "dias_vencido", "valor_pagado"]].reset_index(drop=True)


def get_projected_income(df: pd.DataFrame) -> tuple:
    """Return (projected_income, student_count) for students needing renewal."""
    if df.empty or "estado" not in df.columns:
        return (0.0, 0)
    current = _current_per_student(df)
    needs_renewal = current[current["estado"].isin(["POR VENCER", "VENCIDO"])]
    total = float(needs_renewal["valor_pagado"].sum())
    count = len(needs_renewal)
    return (total, count)


def format_whatsapp_url(telefono) -> str:
    """Build a wa.me URL from a Colombian phone number."""
    import re
    if telefono is None:
        return ""
    # Sheets may return numbers as float (e.g. 3001234567.0) — normalize to str
    if isinstance(telefono, (int, float)):
        telefono = str(int(telefono))
    if not isinstance(telefono, str) or not telefono.strip():
        return ""
    digits = re.sub(r"\D", "", telefono)
    if len(digits) == 10:
        digits = "57" + digits
    elif len(digits) == 12 and digits.startswith("57"):
        pass  # already has country code
    else:
        return ""
    return f"https://wa.me/{digits}"


def get_status_counts(df: pd.DataFrame) -> dict:
    """Return count per status, one entry per student (latest plan)."""
    base = {"ACTIVO": 0, "POR VENCER": 0, "VENCIDO": 0}
    if df.empty or "estado" not in df.columns:
        return base
    counts = _current_per_student(df)["estado"].value_counts().to_dict()
    return {k: int(counts.get(k, 0)) for k in base}
