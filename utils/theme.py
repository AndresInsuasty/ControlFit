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


WA_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="#4ADE80"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'
)


def wa_button_html(wa_url: str, message: str) -> str:
    """Return an <a class='wa-btn'> anchor with the WhatsApp SVG and preset message."""
    import urllib.parse
    if not wa_url:
        return ""
    return (
        f'<a href="{wa_url}?text={urllib.parse.quote(message)}" '
        f'target="_blank" class="wa-btn">{WA_SVG}</a>'
    )


def render_logo_link() -> None:
    """Top-of-page ControlFit logo that navigates back to app.py (preserves session)."""
    st.markdown(
        """
        <style>
        .cf-logo-link [data-testid="stPageLink"] a {
            display: inline-flex !important;
            align-items: baseline;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            text-decoration: none !important;
        }
        .cf-logo-link [data-testid="stPageLink"] a p {
            font-family: 'Barlow Condensed', sans-serif !important;
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            color: #F1F5F9 !important;
            letter-spacing: -0.01em;
            line-height: 1;
            margin: 0 !important;
        }
        .cf-logo-link [data-testid="stPageLink"]:hover a p { color: #4ADE80 !important; }
        </style>
        <div class="cf-logo-link"></div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("app.py", label="💪 ControlFit")
