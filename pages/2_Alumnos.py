import streamlit as st
from data.sheets import get_data
from data.calculations import compute_status, format_whatsapp_url
from utils.theme import apply_theme, PAGE_CONFIG, wa_button_html, render_logo_link

st.set_page_config(page_title="Alumnos — ControlFit", page_icon="👥", **PAGE_CONFIG)

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

apply_theme()

# CSS for inline rows
st.markdown("""
<style>
.wa-btn {
    display: inline-flex; align-items: center; justify-content: center;
    background: rgba(74,222,128,0.08);
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 50%;
    width: 30px; height: 30px;
    text-decoration: none !important;
}
.wa-btn:hover { background: rgba(74,222,128,0.2); }
.wa-btn svg { display: block; }
.badge {
    border-radius: 20px; padding: 1px 8px;
    font-size: 0.68rem; font-weight: 600;
    font-family: 'DM Sans', sans-serif;
}
.badge-amber { background: rgba(251,191,36,0.1); color: #FCD34D; border: 1px solid rgba(251,191,36,0.2); }
.badge-red   { background: rgba(248,113,113,0.1); color: #FCA5A5; border: 1px solid rgba(248,113,113,0.2); }
.badge-green { background: rgba(52,211,153,0.1); color: #6EE7B7; border: 1px solid rgba(52,211,153,0.2); }
</style>
""", unsafe_allow_html=True)

# ── LOGO (volver al app) ───────────────────────────────────────────────────
render_logo_link()

st.title("👥 Alumnos")

# ── Lectura de estado de navegación entrante ───────────────────────────────
filter_state = st.session_state.pop("alumnos_filter", None)
auto_open = st.session_state.pop("alumno_detail", None)

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


def _go_renovar(nombre: str) -> None:
    st.session_state["prefill_renovar"] = nombre
    st.switch_page("pages/3_Gestion.py")


def _historia_display(nombre: str):
    historia = (
        df_raw[df_raw["nombre"] == nombre]
        .sort_values("fecha_fin", ascending=False)
    )
    hist_display = historia[["fecha_inicio", "fecha_fin", "valor_pagado", "notas"]].copy()
    hist_display["fecha_inicio"] = hist_display["fecha_inicio"].dt.strftime("%d/%m/%Y")
    hist_display["fecha_fin"] = hist_display["fecha_fin"].dt.strftime("%d/%m/%Y")
    hist_display["valor_pagado"] = hist_display["valor_pagado"].apply(
        lambda x: f"$ {x:,.0f}".replace(",", ".")
    )
    hist_display.columns = ["Inicio", "Fin", "Valor pagado", "Notas"]
    return hist_display


def render_expandable(group_df, title, empty_msg):
    st.subheader(f"{title} ({len(group_df)})")
    if group_df.empty:
        st.caption(empty_msg)
        return
    for _, row in group_df.iterrows():
        fecha_fin_str = row["fecha_fin"].strftime("%d/%m/%Y")
        expanded = (auto_open == row["nombre"])
        with st.expander(f"{row['nombre']}  ·  {fecha_fin_str}", expanded=expanded):
            st.dataframe(_historia_display(row["nombre"]), hide_index=True, use_container_width=True)


def render_inline_rows(group_df, badge_class, badge_fn, msg_fn, key_prefix):
    for idx, row in group_df.iterrows():
        nombre = row["nombre"]
        wa_url = format_whatsapp_url(row["telefono"])
        msg = msg_fn(row)
        c_name, c_badge, c_wa, c_ren = st.columns([2.2, 1.5, 0.5, 1.2])
        with c_name:
            if st.button(f"👤 {nombre}", key=f"{key_prefix}_name_{idx}", use_container_width=True):
                st.session_state["alumno_detail"] = nombre
                st.rerun()
        c_badge.markdown(
            f'<div style="padding-top:8px"><span class="badge {badge_class}">{badge_fn(row)}</span></div>',
            unsafe_allow_html=True,
        )
        c_wa.markdown(
            f'<div style="padding-top:4px">{wa_button_html(wa_url, msg)}</div>',
            unsafe_allow_html=True,
        )
        with c_ren:
            if st.button("🔄 Renovar", key=f"{key_prefix}_renovar_{idx}", type="primary", use_container_width=True):
                _go_renovar(nombre)
        if auto_open == nombre:
            with st.expander("Historial del alumno", expanded=True):
                st.dataframe(_historia_display(nombre), hide_index=True, use_container_width=True)


# ── Badge & mensaje builders ───────────────────────────────────────────────
import pandas as pd
TODAY = pd.Timestamp.now().normalize()


def _pv_badge(row):
    dias = (row["fecha_fin"] - TODAY).days
    label = "día" if dias == 1 else "días"
    return f"Vence en {dias} {label}"


def _pv_msg(row):
    dias = (row["fecha_fin"] - TODAY).days
    label = "día" if dias == 1 else "días"
    return (
        f"Hola {row['nombre']}! 👋 Soy la IA de tu Coach Diego. "
        f"Te escribo para recordarte que tu membresía vence en {dias} {label}. "
        f"🏋️ Renueva antes de que venza y sigue entrenando sin interrupciones. "
        f"¡No dejes que se corte tu racha! 💪"
    )


def _vc_badge(row):
    dias = (TODAY - row["fecha_fin"]).days
    label = "día" if dias == 1 else "días"
    return f"Hace {dias} {label}"


def _vc_msg(row):
    dias = (TODAY - row["fecha_fin"]).days
    label = "día" if dias == 1 else "días"
    return (
        f"Hola {row['nombre']}! 👋 Soy la IA de tu Coach Diego. "
        f"Hace {dias} {label} que tu membresía venció y te extrañamos en el gym. 🏋️ "
        f"Sabemos que retomar cuesta, pero ya diste el primer paso al entrenar con Diego. "
        f"¿Qué te parece si renovamos hoy y seguimos con tu progreso? ¡Te esperamos! 💪"
    )


# ── Secciones (respeta filtro entrante del dashboard) ──────────────────────
def section_activos():
    render_expandable(activos, "💪 Activos", "Sin alumnos activos.")


def section_por_vencer():
    st.subheader(f"⏰ Por Vencer ({len(por_vencer)})")
    if por_vencer.empty:
        st.caption("Sin alumnos próximos a vencer.")
        return
    render_inline_rows(por_vencer, "badge-amber", _pv_badge, _pv_msg, "pv")


def section_vencidos():
    st.subheader(f"🔴 Vencidos ({len(vencidos)})")
    if vencidos.empty:
        st.caption("Sin alumnos vencidos.")
        return
    render_inline_rows(vencidos, "badge-red", _vc_badge, _vc_msg, "vc")


sections = {
    "ACTIVO": section_activos,
    "POR VENCER": section_por_vencer,
    "VENCIDO": section_vencidos,
}

if filter_state in sections:
    st.caption(f"Filtrado desde dashboard: **{filter_state}**")
    sections[filter_state]()
else:
    section_activos()
    st.divider()
    section_por_vencer()
    st.divider()
    section_vencidos()
