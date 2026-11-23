import os
import streamlit as st
from api_client import APIClient

def render_auth_view(api_client: APIClient):
    # Centered Logo Display
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "bpie_logo.jpg")
    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    st.markdown("""
        <div style="text-align: center; margin-top: 5px; margin-bottom: 25px;">
            <h1 style="color: #0D6EFD; margin-bottom: 2px; font-size: 2rem;">BPIE AI Policy Agent</h1>
            <h3 style="color: #1E293B; font-weight: 700; margin-bottom: 2px;">Bishnupur Public Institute of Engineering</h3>
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 10px; font-weight: 500;">
                Bishnupur, Bankura • Estd. 2010 • A Polytechnic College
            </p>
            <p style="font-size: 0.95rem; color: #495057; max-width: 600px; margin: 0 auto;">
                Official AI Assistant for Institute Rules, Regulations, Examination Guidelines & Codes of Conduct.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.info("🔒 **Access Restricted:** You must authenticate with an authorized institute email address ending in `@bpie.ac.in`.")

    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register New Account"])

    # --- TAB 1: LOGIN ---
    with tab_login:
        st.subheader("Login to Policy Portal")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Institute Email", placeholder="your_name@bpie.ac.in")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submit_login:
            if not email or not password:
                st.error("Please enter both email and password.")
            elif not email.strip().lower().endswith("@bpie.ac.in"):
                st.error("Invalid email domain. Please enter your '@bpie.ac.in' institute email.")
            else:
                with st.spinner("Authenticating..."):
                    res, status = api_client.login(email.strip().lower(), password)
                    if status == 200:
                        st.session_state["token"] = res.get("token")
                        st.session_state["user"] = res.get("user")
                        st.session_state["active_session_id"] = None
                        st.success(f"Welcome back, {res.get('user', {}).get('full_name')}!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Login failed. Check your credentials."))

    # --- TAB 2: REGISTER ---
    with tab_register:
        st.subheader("Create Student / Staff Account")
        with st.form("register_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", placeholder="e.g. Rahul Sharma")
            reg_email = st.text_input("Institute Email Address", placeholder="e.g. rahul.sharma@bpie.ac.in")
            reg_password = st.text_input("Choose Password (min 6 characters)", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if submit_register:
            if not full_name or not reg_email or not reg_password:
                st.error("All fields are required.")
            elif not reg_email.strip().lower().endswith("@bpie.ac.in"):
                st.error("Registration is strictly limited to `@bpie.ac.in` email addresses.")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters long.")
            elif reg_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                with st.spinner("Creating your institutional account..."):
                    res, status = api_client.register(reg_email.strip().lower(), full_name.strip(), reg_password)
                    if status == 201:
                        st.session_state["token"] = res.get("token")
                        st.session_state["user"] = res.get("user")
                        st.session_state["active_session_id"] = None
                        st.success("Account created successfully! Logging you in...")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Registration failed."))
