"""Shared dark theme for all ControlFit pages."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

/* ── GLOBAL ── */
.stApp { background: #07070F !important; }
.main .block-container {
    padding: 1.5rem 1rem 3rem !important;
    max-width: 1100px;
}
* { box-sizing: border-box; }

/* ── HIDE STREAMLIT CHROME ── */
.stDeployButton, footer, #MainMenu { display: none !important; }
/* Keep header in DOM (transparent) so the sidebar toggle button still works */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0D0D1A !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
    font-family: 'DM Sans', sans-serif !important;
    color: #64748B !important;
    border-radius: 10px !important;
    font-size: 0.875rem !important;
    transition: background 0.15s, color 0.15s !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover,
[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] {
    background: rgba(255,255,255,0.05) !important;
    color: #E2E8F0 !important;
}

/* ── TYPOGRAPHY ── */
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    color: #F1F5F9 !important;
}
p, li, label, .stMarkdown {
    font-family: 'DM Sans', sans-serif !important;
}

/* ── DIVIDER ── */
.stDivider hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
"""


def apply_theme() -> None:
    """Inject the global dark theme CSS. Call once per page after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


# Common kwargs for set_page_config — pages can spread this dict and override as needed.
# Usage: st.set_page_config(**PAGE_CONFIG, page_title="My Page", page_icon="🔥")
PAGE_CONFIG: dict = {
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
