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
