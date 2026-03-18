import streamlit as st
from data.sheets import get_data
from data.calculations import compute_status
from utils.theme import apply_theme, PAGE_CONFIG

st.set_page_config(page_title="Alumnos — ControlFit", page_icon="👥", **PAGE_CONFIG)

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

apply_theme()

st.title("👥 Alumnos")

df_raw = get_data()

if df_raw.empty:
    st.info("No hay alumnos registrados. Ve a Gestión para agregar el primero.")
    st.stop()

df = compute_status(df_raw)

# One row per student — most recent plan
df_current = df.sort_values("fecha_fin").groupby("nombre", as_index=False).last()

activos    = df_current[df_current["estado"] == "ACTIVO"].sort_values("fecha_fin")
por_vencer = df_current[df_current["estado"] == "POR VENCER"].sort_values("fecha_fin")
vencidos   = df_current[df_current["estado"] == "VENCIDO"].sort_values("fecha_fin", ascending=False)


def render_section(group_df, title, empty_msg):
    st.subheader(f"{title} ({len(group_df)})")
    if group_df.empty:
        st.caption(empty_msg)
        return
    for _, row in group_df.iterrows():
        fecha_fin_str = row["fecha_fin"].strftime("%d/%m/%Y")
        with st.expander(f"{row['nombre']}  ·  {fecha_fin_str}"):
            historia = (
                df_raw[df_raw["nombre"] == row["nombre"]]
                .sort_values("fecha_fin", ascending=False)
            )
            hist_display = historia[["fecha_inicio", "fecha_fin", "valor_pagado", "notas"]].copy()
            hist_display["fecha_inicio"] = hist_display["fecha_inicio"].dt.strftime("%d/%m/%Y")
            hist_display["fecha_fin"] = hist_display["fecha_fin"].dt.strftime("%d/%m/%Y")
            hist_display["valor_pagado"] = hist_display["valor_pagado"].apply(
                lambda x: f"$ {x:,.0f}".replace(",", ".")
            )
            hist_display.columns = ["Inicio", "Fin", "Valor pagado", "Notas"]
            st.dataframe(hist_display, hide_index=True, use_container_width=True)


render_section(activos, "💪 Activos", "Sin alumnos activos.")
st.divider()
render_section(por_vencer, "⏰ Por Vencer", "Sin alumnos próximos a vencer.")
st.divider()
render_section(vencidos, "🔴 Vencidos", "Sin alumnos vencidos.")
