import hashlib

import pandas as pd
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
/* Fila WhatsApp + enlace Renovar (móvil: dos columnas equilibradas) */
.acciones-badge-row { margin: 0 0 10px 0; }
.wa-en-fila {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    min-height: 40px;
}
/* Enlace discreto Renovar → Gestión */
div[data-testid="stPageLink"] a[href*="prefill_renovar"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px 2px 8px 0 !important;
    min-height: 0 !important;
    width: auto !important;
}
div[data-testid="stPageLink"] a[href*="prefill_renovar"] p {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #94A3B8 !important;
    margin: 0 !important;
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
}
div[data-testid="stPageLink"] a[href*="prefill_renovar"]:hover p {
    color: #4ADE80 !important;
}
/* Lápiz editar fila (page_link, conserva sesión) */
div[data-testid="stPageLink"] a[href*="prefill_edit_id"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    min-height: 0 !important;
    width: auto !important;
}
div[data-testid="stPageLink"] a[href*="prefill_edit_id"] p {
    font-size: 1.1rem !important;
    line-height: 1 !important;
    margin: 0 !important;
    text-decoration: none !important;
}
div[data-testid="stPageLink"] a[href*="prefill_edit_id"]:hover p {
    transform: scale(1.1);
}
.acciones-antes-tabla { height: 12px; }
</style>
""", unsafe_allow_html=True)

# ── LOGO (volver al app) ───────────────────────────────────────────────────
render_logo_link()

st.title("👥 Alumnos")

# ── Lectura de estado de navegación entrante ───────────────────────────────
filter_state = st.session_state.pop("alumnos_filter", None)
auto_open = st.session_state.pop("alumno_detail", None)
# Enlaces HTML del dashboard: ?alumno=… (no borramos el param para evitar rerun que pierda el foco)
if auto_open is None and "alumno" in st.query_params:
    raw = st.query_params["alumno"]
    nombre_qp = raw if isinstance(raw, str) else (raw[0] if raw else "")
    auto_open = nombre_qp or None

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


def _fmt_cop_val(x) -> str:
    return f"$ {float(x):,.0f}".replace(",", ".")


def _render_historial_alumno(nombre: str) -> None:
    """Tabla real (st.dataframe). Editar: st.page_link (no <a href>) para no perder sesión."""
    historia = (
        df_raw[df_raw["nombre"] == nombre]
        .sort_values("fecha_fin", ascending=False)
        .reset_index(drop=True)
    )
    if historia.empty:
        st.caption("Sin historial de periodos.")
        return

    hist_display = historia[["fecha_inicio", "fecha_fin", "valor_pagado", "notas"]].copy()
    hist_display["fecha_inicio"] = hist_display["fecha_inicio"].dt.strftime("%d/%m/%Y")
    hist_display["fecha_fin"] = hist_display["fecha_fin"].dt.strftime("%d/%m/%Y")
    hist_display["valor_pagado"] = hist_display["valor_pagado"].apply(_fmt_cop_val)
    hist_display["notas"] = hist_display["notas"].fillna("").astype(str)
    hist_display.columns = ["Inicio", "Fin", "Valor pagado", "Notas"]

    col_cfg = {
        "Inicio": st.column_config.TextColumn("Inicio", width="small"),
        "Fin": st.column_config.TextColumn("Fin", width="small"),
        "Valor pagado": st.column_config.TextColumn("Valor pagado", width="small"),
        "Notas": st.column_config.TextColumn("Notas", width="large"),
    }

    tbl_key = "hist_" + hashlib.sha256(nombre.encode("utf-8")).hexdigest()[:24]

    def _edit_row_link(rid: str, caption: str) -> None:
        c_a, c_b = st.columns([0.22, 2], gap="small", vertical_alignment="center")
        with c_a:
            st.page_link(
                "pages/3_Gestion.py",
                label="✏️",
                icon=None,
                query_params={"prefill_edit_id": rid},
                width="content",
                help="Editar este periodo en Gestión",
            )
        with c_b:
            st.caption(caption)

    if len(historia) == 1:
        st.dataframe(
            hist_display,
            width="stretch",
            hide_index=True,
            column_config=col_cfg,
        )
        rid = str(historia.iloc[0]["id"])
        r0 = historia.iloc[0]
        res = f"{r0['fecha_inicio'].strftime('%d/%m/%Y')} → {r0['fecha_fin'].strftime('%d/%m/%Y')}"
        _edit_row_link(rid, f"Editar: **{res}**")
        return

    event = st.dataframe(
        hist_display,
        key=tbl_key,
        on_select="rerun",
        selection_mode="single-row",
        width="stretch",
        hide_index=True,
        column_config=col_cfg,
    )

    sel = getattr(event, "selection", None)
    rows = []
    if sel is not None:
        rows = list(getattr(sel, "rows", None) or [])
        if not rows:
            try:
                rows = list(sel["rows"])
            except (TypeError, KeyError):
                pass

    if rows:
        idx = int(rows[0])
        if 0 <= idx < len(historia):
            row = historia.iloc[idx]
            rid = str(row["id"])
            res = f"{row['fecha_inicio'].strftime('%d/%m/%Y')} → {row['fecha_fin'].strftime('%d/%m/%Y')}"
            _edit_row_link(rid, f"Fila seleccionada · **{res}**")
    else:
        st.caption(
            "Toca una fila para seleccionarla y después pulsa ✏️ para editar ese periodo en Gestión."
        )


def render_student_section(
    group_df,
    title,
    empty_msg,
    *,
    badge_class: str | None = None,
    badge_fn=None,
    msg_fn=None,
):
    """Expander por alumno (nombre · fecha fin) + acciones + historial.
    Con badge_fn/msg_fn: WhatsApp y Renovar; historial en tabla + ✏️ (selección de fila)."""
    st.subheader(f"{title} ({len(group_df)})")
    if group_df.empty:
        st.caption(empty_msg)
        return
    with_actions = badge_fn is not None and msg_fn is not None
    for _, row in group_df.iterrows():
        nombre = row["nombre"]
        fecha_fin_str = row["fecha_fin"].strftime("%d/%m/%Y")
        expanded = auto_open == nombre
        with st.expander(f"{nombre}  ·  {fecha_fin_str}", expanded=expanded):
            wa_url = format_whatsapp_url(row["telefono"])
            if with_actions:
                msg = msg_fn(row)
                st.markdown(
                    f'<p class="acciones-badge-row"><span class="badge {badge_class}">'
                    f"{badge_fn(row)}</span></p>",
                    unsafe_allow_html=True,
                )
                c_wa, c_ren = st.columns(2, gap="small", vertical_alignment="center")
                c_wa.markdown(
                    f'<div class="wa-en-fila">{wa_button_html(wa_url, msg)}</div>',
                    unsafe_allow_html=True,
                )
                with c_ren:
                    st.page_link(
                        "pages/3_Gestion.py",
                        label="Renovar",
                        icon=None,
                        query_params={"prefill_renovar": nombre},
                        width="content",
                        help="Renovar membresía en Gestión",
                    )
            else:
                msg = _activo_wa_msg(row)
                st.markdown(
                    f'<div class="wa-en-fila">{wa_button_html(wa_url, msg)}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<div class="acciones-antes-tabla"></div>', unsafe_allow_html=True)
            _render_historial_alumno(nombre)


# ── Badge & mensaje builders ───────────────────────────────────────────────
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


def _activo_wa_msg(row):
    fin = row["fecha_fin"].strftime("%d/%m/%Y")
    return (
        f"Hola {row['nombre']}! 👋 Soy la IA de tu Coach Diego. "
        f"Tu plan actual va hasta el {fin}. "
        f"¡Seguimos entrenando fuerte! 💪"
    )


# ── Secciones (respeta filtro entrante del dashboard) ──────────────────────
def section_activos():
    render_student_section(activos, "💪 Activos", "Sin alumnos activos.")


def section_por_vencer():
    render_student_section(
        por_vencer,
        "⏰ Por Vencer",
        "Sin alumnos próximos a vencer.",
        badge_class="badge-amber",
        badge_fn=_pv_badge,
        msg_fn=_pv_msg,
    )


def section_vencidos():
    render_student_section(
        vencidos,
        "🔴 Vencidos",
        "Sin alumnos vencidos.",
        badge_class="badge-red",
        badge_fn=_vc_badge,
        msg_fn=_vc_msg,
    )


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
