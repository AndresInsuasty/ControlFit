import streamlit as st
import uuid
from datetime import datetime, date, timezone, timedelta
from data.sheets import get_data, append_record, update_record
from utils.theme import apply_theme, PAGE_CONFIG

st.set_page_config(
    page_title="Gestión — ControlFit",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state=PAGE_CONFIG["initial_sidebar_state"],
)

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

apply_theme()

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
        fecha_fin = col2.date_input("Fecha de fin *", value=date.today() + timedelta(days=30))
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
                "fecha_registro": datetime.now(timezone(timedelta(hours=-5))).isoformat(),
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
        df["_label"] = (
            df["nombre"] + " — "
            + df["fecha_inicio"].dt.strftime("%d/%m/%Y") + " → "
            + df["fecha_fin"].dt.strftime("%d/%m/%Y")
        )
        labels = df["_label"].tolist()
        selected_idx = st.selectbox("Selecciona un registro", range(len(labels)), format_func=lambda i: labels[i])
        row = df.iloc[selected_idx]
        selected_id = row["id"]

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
