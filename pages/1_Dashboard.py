import streamlit as st
import plotly.express as px
from data.sheets import get_data
from data.calculations import (
    compute_status,
    format_whatsapp_url,
    get_expired_students,
    get_expiring_students,
    get_metrics,
    get_monthly_income,
    get_projected_income,
    get_status_counts,
)

st.set_page_config(page_title="Dashboard — ControlFit", page_icon="📊", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

st.title("📊 Dashboard")

df_raw = get_data()
df = compute_status(df_raw) if not df_raw.empty else df_raw
metrics = get_metrics(df)

# --- KPI Metrics (5 cards) ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Alumnos Activos", metrics["activos"])
col2.metric("Por Vencer (7 días)", metrics["por_vencer"])
col3.metric("Vencidos", metrics["vencidos"])

ingresos_fmt = f"$ {metrics['ingresos_mes']:,.0f}".replace(",", ".")
col4.metric("Ingresos del Mes", ingresos_fmt)

projected, renewal_count = get_projected_income(df)
proj_fmt = f"$ {projected:,.0f}".replace(",", ".")
col5.metric(
    "Proyección Prox. Mes",
    proj_fmt,
    delta=f"{renewal_count} por renovar",
    delta_color="off",
)

st.divider()

# --- Action Tables ---
expiring_df = get_expiring_students(df)
expired_df = get_expired_students(df)

if expiring_df.empty and expired_df.empty:
    st.success("✅ ¡Todo al día! No hay alumnos por vencer ni vencidos.")
else:
    table_col1, table_col2 = st.columns(2)

    with table_col1:
        st.subheader("⚠️ Próximos a Vencer")
        if expiring_df.empty:
            st.info("No hay alumnos próximos a vencer.")
        else:
            display_exp = expiring_df.copy()
            display_exp["fecha_fin"] = display_exp["fecha_fin"].dt.strftime("%d/%m/%Y")
            display_exp["whatsapp_url"] = display_exp["telefono"].apply(format_whatsapp_url)
            display_exp["valor_pagado"] = display_exp["valor_pagado"].apply(
                lambda v: f"$ {v:,.0f}".replace(",", ".")
            )
            st.dataframe(
                display_exp[["nombre", "fecha_fin", "whatsapp_url", "valor_pagado"]],
                column_config={
                    "nombre": st.column_config.TextColumn("Nombre"),
                    "fecha_fin": st.column_config.TextColumn("Vence"),
                    "whatsapp_url": st.column_config.LinkColumn("WhatsApp", display_text="Escribir"),
                    "valor_pagado": st.column_config.TextColumn("Valor"),
                },
                hide_index=True,
                use_container_width=True,
            )

    with table_col2:
        st.subheader("❌ Ya Vencidos")
        if expired_df.empty:
            st.info("No hay alumnos vencidos.")
        else:
            display_venc = expired_df.copy()
            display_venc["fecha_fin"] = display_venc["fecha_fin"].dt.strftime("%d/%m/%Y")
            display_venc["whatsapp_url"] = display_venc["telefono"].apply(format_whatsapp_url)
            display_venc["valor_pagado"] = display_venc["valor_pagado"].apply(
                lambda v: f"$ {v:,.0f}".replace(",", ".")
            )
            st.dataframe(
                display_venc[["nombre", "fecha_fin", "dias_vencido", "whatsapp_url", "valor_pagado"]],
                column_config={
                    "nombre": st.column_config.TextColumn("Nombre"),
                    "fecha_fin": st.column_config.TextColumn("Venció"),
                    "dias_vencido": st.column_config.NumberColumn("Días vencido"),
                    "whatsapp_url": st.column_config.LinkColumn("WhatsApp", display_text="Escribir"),
                    "valor_pagado": st.column_config.TextColumn("Valor"),
                },
                hide_index=True,
                use_container_width=True,
            )

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
