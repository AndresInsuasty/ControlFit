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
    get_status_counts,
)

st.set_page_config(page_title="ControlFit", page_icon="💪", layout="wide", initial_sidebar_state="expanded")

if not st.session_state.get("authenticated"):
    st.warning("Debes iniciar sesión primero.")
    st.stop()

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

/* ─ GLOBAL ─ */
.stApp {
    background: #07070F !important;
}
.main .block-container {
    padding: 1.5rem 1rem 3rem !important;
    max-width: 1100px;
}
* { box-sizing: border-box; }

/* ─ HIDE CHROME ─ */
.stDeployButton,
footer,
#MainMenu { display: none !important; }
/* Header: invisible but present so the sidebar toggle still works */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

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
}
@media (min-width: 560px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 860px) { .kpi-grid { grid-template-columns: repeat(5, 1fr); } }

.kpi-card {
    background: #111120;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 18px 16px 16px;
    position: relative;
    overflow: hidden;
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
    overflow: hidden;
    margin-bottom: 0.75rem;
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
    gap: 4px;
    background: rgba(74,222,128,0.08);
    color: #4ADE80;
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    text-decoration: none !important;
    font-family: 'DM Sans', sans-serif;
    transition: background 0.15s;
    white-space: nowrap;
}
.wa-btn:hover {
    background: rgba(74,222,128,0.16);
    color: #4ADE80;
    text-decoration: none !important;
}

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

/* ─ NAV BUTTONS ─ */
[data-testid="stPageLink"] {
    width: 100%;
}
[data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    background: #111120 !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 14px !important;
    color: #94A3B8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
    text-decoration: none !important;
    transition: border-color 0.2s, color 0.2s, background 0.2s !important;
    width: 100% !important;
}
[data-testid="stPageLink"] a:hover {
    background: #181828 !important;
    border-color: rgba(255,255,255,0.18) !important;
    color: #F1F5F9 !important;
    text-decoration: none !important;
}

/* ─ SIDEBAR ─ */
[data-testid="stSidebar"] {
    background: #0D0D1A !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
    font-family: 'DM Sans', sans-serif !important;
    color: #64748B !important;
    border-radius: 10px !important;
    font-size: 0.875rem !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover,
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] {
    background: rgba(255,255,255,0.05) !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebarCollapseButton"] {
    color: #475569 !important;
}

/* ─ STAPP OVERRIDES ─ */
.stDivider hr { border-color: rgba(255,255,255,0.05) !important; }
</style>
""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────
df_raw = get_data()
df = compute_status(df_raw) if not df_raw.empty else df_raw
metrics = get_metrics(df)
projected, renewal_count = get_projected_income(df)
expiring_df = get_expiring_students(df)
expired_df = get_expired_students(df)

# ── FORMAT HELPERS ─────────────────────────────────────────────────────────
def fmt_cop(v):
    return f"$ {v:,.0f}".replace(",", ".")

# ── PAGE HEADER ────────────────────────────────────────────────────────────
from datetime import date
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
        <div class="kpi-label">Ingresos Mes</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:#A78BFA"></div>
        <span class="kpi-icon">📈</span>
        <div class="kpi-value md">{proj_fmt}</div>
        <div class="kpi-label">Proyección</div>
        <div class="kpi-delta">↑ {renewal_count} por renovar</div>
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
                wa = f'<a href="{wa_url}" target="_blank" class="wa-btn">📱 WhatsApp</a>' if wa_url else ""
                fecha = r["fecha_fin"].strftime("%d/%m/%Y")
                valor = fmt_cop(r["valor_pagado"])
                rows += f"""
                <div class="action-item">
                    <div class="action-dot" style="background:#FBBF24"></div>
                    <div class="action-info">
                        <div class="action-name">{r['nombre']}</div>
                        <div class="action-sub">
                            <span class="badge badge-amber">Vence {fecha}</span>
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
                wa = f'<a href="{wa_url}" target="_blank" class="wa-btn">📱 WhatsApp</a>' if wa_url else ""
                fecha = r["fecha_fin"].strftime("%d/%m/%Y")
                valor = fmt_cop(r["valor_pagado"])
                dias = int(r["dias_vencido"])
                label = "día" if dias == 1 else "días"
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
