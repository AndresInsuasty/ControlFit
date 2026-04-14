import urllib.parse
import streamlit as st
import plotly.graph_objects as go
from data.sheets import get_data
from data.calculations import (
    compute_status,
    format_whatsapp_url,
    get_expired_students,
    get_expiring_students,
    get_metrics,
    get_monthly_income,
    get_projected_income,
    get_renewed_students,
    get_status_counts,
)
from utils.theme import apply_theme, PAGE_CONFIG

st.set_page_config(page_title="ControlFit", page_icon="💪", **PAGE_CONFIG)

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

apply_theme()

# ── CSS (dashboard-specific) ───────────────────────────────────────────────
st.markdown("""
<style>
/* ─ PAGE TITLE ─ */
.cf-page-header {
    margin-bottom: 1.75rem;
}
.cf-page-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: clamp(2rem, 6vw, 2.8rem);
    font-weight: 800;
    color: #F1F5F9;
    letter-spacing: -0.01em;
    line-height: 1;
    margin: 0;
}
.cf-page-title em {
    font-style: normal;
    color: #4ADE80;
}
.cf-date {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: #334155;
    font-weight: 500;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ─ KPI GRID ─ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 1.75rem;
    overflow: visible;
}
@media (min-width: 560px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 860px) { .kpi-grid { grid-template-columns: repeat(5, 1fr); } }

.kpi-card {
    background: #111120;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 18px 16px 16px;
    position: relative;
    overflow: visible;
    transition: border-color 0.2s, transform 0.2s;
}
.kpi-card:hover {
    border-color: rgba(255,255,255,0.13);
    transform: translateY(-2px);
}
.kpi-accent {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 20px 20px 0 0;
}
.kpi-icon {
    font-size: 1.2rem;
    display: block;
    margin-bottom: 14px;
    line-height: 1;
}
.kpi-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: clamp(1.9rem, 4.5vw, 2.6rem);
    font-weight: 700;
    color: #F1F5F9;
    line-height: 1;
    letter-spacing: -0.02em;
}
.kpi-value.md { font-size: clamp(1.4rem, 3vw, 1.8rem); }
.kpi-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 8px;
}
.kpi-delta {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: #64748B;
    margin-top: 5px;
}

/* ─ DIVIDER ─ */
.cf-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 1.25rem 0 1.5rem;
}

/* ─ SECTION TITLE ─ */
.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.section-title span { margin-right: 6px; }

/* ─ ACTION CARD ─ */
.action-card {
    background: #111120;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    overflow-x: hidden;
    overflow-y: auto;
    max-height: 204px;
    margin-bottom: 0.75rem;
}
.action-card::-webkit-scrollbar { width: 4px; }
.action-card::-webkit-scrollbar-track { background: transparent; }
.action-card::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.08);
    border-radius: 4px;
}
.action-item {
    display: flex;
    align-items: center;
    padding: 14px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    gap: 10px;
}
.action-item:last-child { border-bottom: none; }
.action-item:hover { background: rgba(255,255,255,0.015); }
.action-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.action-info { flex: 1; min-width: 0; }
.action-name {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    color: #E2E8F0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.action-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    color: #475569;
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.badge {
    border-radius: 20px;
    padding: 1px 8px;
    font-size: 0.68rem;
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
    white-space: nowrap;
    letter-spacing: 0.02em;
}
.badge-amber {
    background: rgba(251,191,36,0.1);
    color: #FCD34D;
    border: 1px solid rgba(251,191,36,0.2);
}
.badge-red {
    background: rgba(248,113,113,0.1);
    color: #FCA5A5;
    border: 1px solid rgba(248,113,113,0.2);
}
.badge-green {
    background: rgba(52,211,153,0.1);
    color: #6EE7B7;
    border: 1px solid rgba(52,211,153,0.2);
}
.action-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
    flex-shrink: 0;
}
.action-valor {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #64748B;
}
.wa-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(74,222,128,0.08);
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 50%;
    width: 30px;
    height: 30px;
    text-decoration: none !important;
    transition: background 0.15s;
    flex-shrink: 0;
}
.wa-btn:hover {
    background: rgba(74,222,128,0.2);
    text-decoration: none !important;
}
.wa-btn svg { display: block; }

/* ─ ALL GOOD ─ */
.all-good {
    background: rgba(74,222,128,0.05);
    border: 1px solid rgba(74,222,128,0.12);
    border-radius: 20px;
    padding: 36px 20px;
    text-align: center;
    margin-bottom: 1rem;
}
.all-good-icon { font-size: 2.5rem; display: block; margin-bottom: 10px; }
.all-good-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #4ADE80;
    font-weight: 500;
}
.all-good-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: #334155;
    margin-top: 4px;
}

/* ─ KPI INFO TOOLTIP ─ */
.kpi-info {
    position: relative;
    display: inline-block;
    cursor: default;
    color: #334155;
    font-size: 0.65rem;
    vertical-align: middle;
    margin-left: 4px;
    line-height: 1;
}
.kpi-tooltip {
    visibility: hidden;
    opacity: 0;
    width: 180px;
    background: #1A1A2E;
    color: #94A3B8;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 400;
    text-transform: none;
    letter-spacing: 0;
    line-height: 1.45;
    border-radius: 12px;
    padding: 10px 12px;
    border: 1px solid rgba(255,255,255,0.09);
    position: absolute;
    z-index: 9999;
    bottom: calc(100% + 8px);
    right: 0;
    left: auto;
    transform: none;
    transition: opacity 0.18s;
    pointer-events: none;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.kpi-info:hover .kpi-tooltip { visibility: visible; opacity: 1; }

/* 2-col (mobile <560px): card 5 cae en columna izquierda → extender a la derecha */
@media (max-width: 559px) {
    .kpi-card:nth-child(5) .kpi-tooltip { left: 0; right: auto; }
}
/* 3-col (560-859px): cards 4 y 5 caen en columna izquierda → extender a la derecha */
@media (min-width: 560px) and (max-width: 859px) {
    .kpi-card:nth-child(4) .kpi-tooltip,
    .kpi-card:nth-child(5) .kpi-tooltip { left: 0; right: auto; }
}

/* ─ CHART CARDS ─ */
[data-testid="stPlotlyChart"] > div {
    background: #111120 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 20px !important;
    overflow: hidden !important;
}
.chart-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #334155;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

</style>
""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────
df_raw = get_data()
df = compute_status(df_raw) if not df_raw.empty else df_raw
metrics = get_metrics(df)
projected, renewal_count = get_projected_income(df)
expiring_df = get_expiring_students(df)
expired_df = get_expired_students(df)
renewed_df = get_renewed_students(df)

# ── FORMAT HELPERS ─────────────────────────────────────────────────────────
def fmt_cop(v):
    return f"$ {v:,.0f}".replace(",", ".")

# ── PAGE HEADER ────────────────────────────────────────────────────────────
from datetime import date, datetime
DIAS_ES = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES_ES_FULL = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                  7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
hoy = date.today()
fecha_str = f"{DIAS_ES[hoy.weekday()]} {hoy.day} {MESES_ES_FULL[hoy.month]} {hoy.year}"

st.markdown(f"""
<div class="cf-page-header">
    <div class="cf-page-title">Control<em>Fit</em></div>
    <div class="cf-date">{fecha_str}</div>
</div>
""", unsafe_allow_html=True)

# ── KPI CARDS ──────────────────────────────────────────────────────────────
ingresos_fmt = fmt_cop(metrics["ingresos_mes"])
proj_fmt = fmt_cop(projected)

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#4ADE80"></div>
        <span class="kpi-icon">💪</span>
        <div class="kpi-value">{metrics['activos']}</div>
        <div class="kpi-label">Activos</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#FBBF24"></div>
        <span class="kpi-icon">⏰</span>
        <div class="kpi-value">{metrics['por_vencer']}</div>
        <div class="kpi-label">Por Vencer</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#F87171"></div>
        <span class="kpi-icon">🔴</span>
        <div class="kpi-value">{metrics['vencidos']}</div>
        <div class="kpi-label">Vencidos</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#60A5FA"></div>
        <span class="kpi-icon">💵</span>
        <div class="kpi-value md">{ingresos_fmt}</div>
        <div class="kpi-label">
            Ingresos este mes
            <span class="kpi-info">ℹ
                <span class="kpi-tooltip">Suma de todos los pagos registrados durante el mes actual, basado en la fecha en que se guardó cada registro.</span>
            </span>
        </div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#A78BFA"></div>
        <span class="kpi-icon">📈</span>
        <div class="kpi-value md">{proj_fmt}</div>
        <div class="kpi-label">
            Proyección próximo mes
            <span class="kpi-info">ℹ
                <span class="kpi-tooltip">Estimado de ingresos del próximo mes basado en los {renewal_count} afiliados activos y por vencer, usando su último valor pagado.</span>
            </span>
        </div>
        <div class="kpi-delta">↑ {renewal_count} activos</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── ACTION TABLES ──────────────────────────────────────────────────────────
if expiring_df.empty and expired_df.empty:
    st.markdown("""
    <div class="all-good">
        <span class="all-good-icon">🎯</span>
        <div class="all-good-text">¡Todo al día!</div>
        <div class="all-good-sub">No hay alumnos por vencer ni vencidos</div>
    </div>
    """, unsafe_allow_html=True)
else:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title"><span>⚠️</span>Por Vencer</div>', unsafe_allow_html=True)
        if expiring_df.empty:
            st.markdown("""
            <div class="action-card">
                <div class="action-item" style="justify-content:center;color:#334155;font-family:'DM Sans',sans-serif;font-size:0.82rem;">
                    Sin alumnos próximos a vencer
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            rows = ""
            for _, r in expiring_df.iterrows():
                wa_url = format_whatsapp_url(r["telefono"])
                dias_restantes = (r["fecha_fin"].date() - hoy).days
                dias_label = "día" if dias_restantes == 1 else "días"
                if wa_url:
                    msg = (
                        f"Hola {r['nombre']}! 👋 Soy la IA de tu Coach Diego. "
                        f"Te escribo para recordarte que tu membresía vence en {dias_restantes} {dias_label}. "
                        f"🏋️ Renueva antes de que venza y sigue entrenando sin interrupciones. "
                        f"¡No dejes que se corte tu racha! 💪"
                    )
                    wa = f'<a href="{wa_url}?text={urllib.parse.quote(msg)}" target="_blank" class="wa-btn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#4ADE80"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>'
                else:
                    wa = ""
                valor = fmt_cop(r["valor_pagado"])
                rows += f"""
                <div class="action-item">
                    <div class="action-dot" style="background:#FBBF24"></div>
                    <div class="action-info">
                        <div class="action-name">{r['nombre']}</div>
                        <div class="action-sub">
                            <span class="badge badge-amber">Vence en {dias_restantes} {dias_label}</span>
                        </div>
                    </div>
                    <div class="action-right">
                        <div class="action-valor">{valor}</div>
                        {wa}
                    </div>
                </div>"""
            st.markdown(f'<div class="action-card">{rows}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-title"><span>❌</span>Vencidos</div>', unsafe_allow_html=True)
        if expired_df.empty:
            st.markdown("""
            <div class="action-card">
                <div class="action-item" style="justify-content:center;color:#334155;font-family:'DM Sans',sans-serif;font-size:0.82rem;">
                    Sin alumnos vencidos
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            rows = ""
            for _, r in expired_df.iterrows():
                wa_url = format_whatsapp_url(r["telefono"])
                fecha = r["fecha_fin"].strftime("%d/%m/%Y")
                valor = fmt_cop(r["valor_pagado"])
                dias = int(r["dias_vencido"])
                label = "día" if dias == 1 else "días"
                if wa_url:
                    msg = (
                        f"Hola {r['nombre']}! 👋 Soy la IA de tu Coach Diego. "
                        f"Hace {dias} {label} que tu membresía venció y te extrañamos en el gym. 🏋️ "
                        f"Sabemos que retomar cuesta, pero ya diste el primer paso al entrenar con Diego. "
                        f"¿Qué te parece si renovamos hoy y seguimos con tu progreso? ¡Te esperamos! 💪"
                    )
                    wa = f'<a href="{wa_url}?text={urllib.parse.quote(msg)}" target="_blank" class="wa-btn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#4ADE80"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>'
                else:
                    wa = ""
                rows += f"""
                <div class="action-item">
                    <div class="action-dot" style="background:#F87171"></div>
                    <div class="action-info">
                        <div class="action-name">{r['nombre']}</div>
                        <div class="action-sub">
                            <span class="badge badge-red">Hace {dias} {label}</span>
                            <span style="color:#334155">{fecha}</span>
                        </div>
                    </div>
                    <div class="action-right">
                        <div class="action-valor">{valor}</div>
                        {wa}
                    </div>
                </div>"""
            st.markdown(f'<div class="action-card">{rows}</div>', unsafe_allow_html=True)

# ── RENOVADOS ──────────────────────────────────────────────────────────────
st.markdown('<hr class="cf-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><span>🎉</span>Renovados (últimos 7 días)</div>', unsafe_allow_html=True)

if renewed_df.empty:
    st.markdown("""
    <div class="action-card">
        <div class="action-item" style="justify-content:center;color:#334155;font-family:'DM Sans',sans-serif;font-size:0.82rem;">
            Sin renovaciones en los últimos 7 días
        </div>
    </div>""", unsafe_allow_html=True)
else:
    rows = ""
    for _, r in renewed_df.iterrows():
        wa_url = format_whatsapp_url(r["telefono"])
        dias_desde = (datetime.now(tz=r["fecha_registro"].tzinfo) - r["fecha_registro"]).days
        dias_label = "día" if dias_desde == 1 else "días"
        fecha_inicio_fmt = r["fecha_inicio"].strftime("%d/%m/%Y")
        fecha_fin_fmt = r["fecha_fin"].strftime("%d/%m/%Y")
        valor = fmt_cop(r["valor_pagado"])
        if wa_url:
            msg = (
                f"Hola {r['nombre']}! 🎉 Soy la IA de tu coach Diego. "
                f"Me alegra confirmarte que tu membresía ha sido renovada exitosamente. "
                f"Tu plan va del {fecha_inicio_fmt} al {fecha_fin_fmt}. "
                f"¡Sigamos trabajando juntos para alcanzar tus metas! 💪🔥"
            )
            wa = f'<a href="{wa_url}?text={urllib.parse.quote(msg)}" target="_blank" class="wa-btn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#4ADE80"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>'
        else:
            wa = ""
        rows += f"""
        <div class="action-item">
            <div class="action-dot" style="background:#34D399"></div>
            <div class="action-info">
                <div class="action-name">{r['nombre']}</div>
                <div class="action-sub">
                    <span class="badge badge-green">Renovó hace {dias_desde} {dias_label}</span>
                    <span style="color:#334155">{fecha_inicio_fmt} → {fecha_fin_fmt}</span>
                </div>
            </div>
            <div class="action-right">
                <div class="action-valor">{valor}</div>
                {wa}
            </div>
        </div>"""
    st.markdown(f'<div class="action-card">{rows}</div>', unsafe_allow_html=True)

# ── CHARTS ─────────────────────────────────────────────────────────────────
st.markdown('<hr class="cf-divider">', unsafe_allow_html=True)

CHART_BG = "rgba(17,17,32,0)"
GRID_COLOR = "rgba(255,255,255,0.04)"
TICK_COLOR = "#334155"
FONT = dict(family="DM Sans, sans-serif", color=TICK_COLOR, size=11)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown('<div class="chart-label">Ingresos por Mes</div>', unsafe_allow_html=True)
    income_df = get_monthly_income(df_raw)
    income_df = income_df[income_df["ingresos"] > 0]
    fig_bar = go.Figure(go.Bar(
        x=income_df["mes"],
        y=income_df["ingresos"],
        marker=dict(
            color=income_df["ingresos"],
            colorscale=[[0, "#1E3A5F"], [1, "#60A5FA"]],
            showscale=False,
            cornerradius=6,
        ),
        hovertemplate="<b>%{x}</b><br>$ %{y:,.0f}<extra></extra>",
    ))
    fig_bar.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=FONT, margin=dict(l=8, r=8, t=12, b=8),
        height=220,
        xaxis=dict(tickangle=-45, gridcolor=GRID_COLOR, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(size=9, color=TICK_COLOR), tickcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(size=9, color=TICK_COLOR), tickcolor="rgba(0,0,0,0)",
                   tickformat="$,.0f"),
        showlegend=False,
        bargap=0.35,
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

with chart_col2:
    st.markdown('<div class="chart-label">Estado de Alumnos</div>', unsafe_allow_html=True)
    counts = get_status_counts(df)
    if sum(counts.values()) > 0:
        fig_pie = go.Figure(go.Pie(
            labels=list(counts.keys()),
            values=list(counts.values()),
            hole=0.6,
            marker=dict(
                colors=["#4ADE80", "#FBBF24", "#F87171"],
                line=dict(color="#07070F", width=3),
            ),
            textfont=dict(family="DM Sans, sans-serif", size=11, color="#94A3B8"),
            hovertemplate="<b>%{label}</b><br>%{value} alumnos<extra></extra>",
        ))
        fig_pie.update_layout(
            paper_bgcolor=CHART_BG,
            font=FONT,
            margin=dict(l=8, r=8, t=12, b=8),
            height=220,
            showlegend=True,
            legend=dict(
                font=dict(family="DM Sans, sans-serif", size=10, color="#64748B"),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                yanchor="bottom", y=-0.15,
                xanchor="center", x=0.5,
            ),
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("""
        <div class="action-card">
            <div class="action-item" style="justify-content:center;color:#334155;font-family:'DM Sans',sans-serif;font-size:0.82rem;padding:40px;">
                No hay alumnos registrados aún
            </div>
        </div>""", unsafe_allow_html=True)
