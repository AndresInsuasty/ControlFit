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
