import streamlit as st

st.set_page_config(
    page_title="ControlFit",
    page_icon="💪",
    layout="centered",
)

if st.session_state.get("authenticated"):
    st.switch_page("pages/1_Dashboard.py")

st.title("💪 ControlFit")
st.subheader("Ingresa tu contraseña para continuar")

with st.form("login_form"):
    password = st.text_input("Contraseña", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Ingresar", use_container_width=True)

if submitted:
    if password == st.secrets["password"]:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.error("Contraseña incorrecta. Intenta de nuevo.")
