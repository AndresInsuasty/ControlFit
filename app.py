import streamlit as st
from utils.theme import apply_theme, PAGE_CONFIG, render_login_wordmark

st.set_page_config(
    page_title="ControlFit",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state=PAGE_CONFIG["initial_sidebar_state"],
)

if st.session_state.get("authenticated"):
    st.switch_page("pages/1_Dashboard.py")

apply_theme()

st.markdown("""
<style>
.login-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    color: #475569;
    margin-top: 6px;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

render_login_wordmark()
st.markdown('<div class="login-sub">Ingresa tu contraseña para continuar</div>', unsafe_allow_html=True)

with st.form("login_form"):
    password = st.text_input("Contraseña", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Ingresar", use_container_width=True)

if submitted:
    if password == st.secrets["password"]:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.error("Contraseña incorrecta. Intenta de nuevo.")
