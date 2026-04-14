import streamlit as st
import uuid
from datetime import datetime, date, timezone, timedelta
from data.sheets import get_data, append_record, update_record
from utils.theme import apply_theme, PAGE_CONFIG, render_logo_link

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

render_logo_link()

st.title("⚙️ Gestión de Alumnos")

prefill_renovar = st.session_state.pop("prefill_renovar", None)
if prefill_renovar is None and "prefill_renovar" in st.query_params:
    raw = st.query_params["prefill_renovar"]
    q = raw if isinstance(raw, str) else (raw[0] if raw else "")
    prefill_renovar = (q or "").strip() or None
if prefill_renovar:
    st.info(f"Renovando membresía de **{prefill_renovar}**")

prefill_edit_id = st.session_state.pop("prefill_edit_id", None)
if prefill_edit_id is None and "prefill_edit_id" in st.query_params:
    raw = st.query_params["prefill_edit_id"]
    q = raw if isinstance(raw, str) else (raw[0] if raw else "")
    prefill_edit_id = (q or "").strip() or None
if prefill_edit_id:
    if st.session_state.get("_edit_prefill_seen") != prefill_edit_id:
        st.session_state.gestion_tab_ix = 2
        st.session_state._edit_prefill_seen = prefill_edit_id
        st.info("Editando el registro que elegiste en **Alumnos**.")

TAB_LABELS = ["🔄 Renovación", "➕ Agregar Alumno", "✏️ Editar Alumno"]
if "gestion_tab_ix" not in st.session_state:
    st.session_state.gestion_tab_ix = 0

tab_ix = st.radio(
    " ",
    range(3),
    format_func=lambda i: TAB_LABELS[i],
    horizontal=True,
    label_visibility="collapsed",
    key="gestion_tab_ix",
)

# ──────────────── TAB: AGREGAR ────────────────

if tab_ix == 1:
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


# ──────────────── TAB: RENOVACIÓN ────────────────

elif tab_ix == 0:
    st.subheader("Renovar Membresía")

    df_all = get_data()

    if df_all.empty:
        st.info("No hay alumnos registrados. Ve a Agregar Alumno para crear el primero.")
    else:
        # Latest record per student (highest fecha_fin)
        df_current = df_all.sort_values("fecha_fin").groupby("nombre", as_index=False).last()
        nombres = df_current["nombre"].tolist()
        default_idx = nombres.index(prefill_renovar) if prefill_renovar in nombres else None
        selected_nombre = st.selectbox("Selecciona un alumno", nombres, index=default_idx,
                                       placeholder="Escoge un alumno...", key="renew_select")

        if selected_nombre is not None:
            row_r = df_current[df_current["nombre"] == selected_nombre].iloc[0]

            with st.form("form_renovar", clear_on_submit=True):
                nombre_r = st.text_input("Nombre *", value=row_r["nombre"])
                telefono_r = st.text_input("Teléfono / WhatsApp", value=str(int(row_r["telefono"])) if isinstance(row_r["telefono"], float) else row_r["telefono"])
                col1, col2 = st.columns(2)
                fecha_inicio_r = col1.date_input("Fecha de inicio *", value=date.today())
                fecha_fin_r = col2.date_input("Fecha de fin *", value=date.today() + timedelta(days=30))
                valor_r = st.number_input("Valor pagado (COP) *", value=float(row_r["valor_pagado"]),
                                          min_value=0.0, step=1000.0, format="%.0f")
                notas_r = st.text_area("Notas", value=row_r["notas"])
                save_r = st.form_submit_button("Registrar renovación", use_container_width=True)

            if save_r:
                if not nombre_r.strip():
                    st.error("El nombre es obligatorio.")
                elif fecha_fin_r < fecha_inicio_r:
                    st.error("La fecha de fin no puede ser anterior a la fecha de inicio.")
                else:
                    record = {
                        "id": str(uuid.uuid4()),
                        "nombre": nombre_r.strip(),
                        "telefono": telefono_r.strip(),
                        "fecha_inicio": fecha_inicio_r.strftime("%d/%m/%Y"),
                        "fecha_fin": fecha_fin_r.strftime("%d/%m/%Y"),
                        "valor_pagado": float(valor_r),
                        "notas": notas_r.strip(),
                        "fecha_registro": datetime.now(timezone(timedelta(hours=-5))).isoformat(),
                    }
                    append_record(record)
                    st.success(f"✅ Renovación de **{nombre_r}** registrada exitosamente.")


# ──────────────── TAB: EDITAR ────────────────

elif tab_ix == 2:
    st.subheader("Editar Registro Existente")

    df = get_data()

    if df.empty:
        st.info("No hay registros para editar.")
    else:
        df = df.sort_values("fecha_fin", ascending=False).reset_index(drop=True)
        df["_label"] = (
            df["nombre"] + " — "
            + df["fecha_inicio"].dt.strftime("%d/%m/%Y") + " → "
            + df["fecha_fin"].dt.strftime("%d/%m/%Y")
        )
        labels = df["_label"].tolist()
        prefill_idx = None
        if prefill_edit_id:
            target = str(prefill_edit_id)
            for i, rid in enumerate(df["id"].astype(str)):
                if rid == target:
                    prefill_idx = i
                    break
        selected_idx = st.selectbox(
            "Selecciona un registro",
            range(len(labels)),
            index=prefill_idx,
            format_func=lambda i: labels[i],
            placeholder="Escoge un registro...",
        )

        if selected_idx is not None:
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
