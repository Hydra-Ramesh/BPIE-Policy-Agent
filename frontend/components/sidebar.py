import os
import streamlit as st
from api_client import APIClient

def render_sidebar(api_client: APIClient):
    token = st.session_state.get("token")
    user = st.session_state.get("user", {})
    user_role = user.get("role", "student")
    full_name = user.get("full_name", "User")
    email = user.get("email", "")

    with st.sidebar:
        # College Logo in Sidebar
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "bpie_logo.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

        # Header / Brand
        st.markdown(f"""
            <div style="padding: 6px 0 12px 0; border-bottom: 1px solid #E9ECEF; margin-bottom: 12px; text-align: center;">
                <div style="font-size: 1.15rem; font-weight: 700; color: #0D6EFD;">BPIE Policy Agent</div>
                <div style="font-size: 0.83rem; font-weight: 600; color: #1E293B;">Bishnupur Public Institute of Engineering</div>
                <div style="font-size: 0.75rem; color: #64748B;">Bishnupur, Bankura • Estd. 2010</div>
            </div>
            <div style="background: #F1F5F9; padding: 10px 12px; border-radius: 8px; margin-bottom: 15px;">
                <div style="font-weight: 600; font-size: 0.95rem; color: #1E293B;">{full_name}</div>
                <div style="font-size: 0.8rem; color: #64748B;">{email}</div>
                <div style="margin-top: 5px;">
                    <span style="background-color: {'#DC3545' if user_role == 'admin' else '#0D6EFD'};
                                 color: white; font-size: 0.7rem; font-weight: 700;
                                 padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">
                        {user_role}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Admin View Switcher (RBAC)
        if user_role == "admin":
            st.markdown("##### 🧭 Navigation")
            current_view = st.session_state.get("current_view", "chat")
            view_option = st.radio(
                "Select Interface",
                options=["💬 Chat with Policy Agent", "📑 Policy Docs Manager (Admin)"],
                index=0 if current_view == "chat" else 1,
                label_visibility="collapsed"
            )
            st.session_state["current_view"] = "chat" if "Chat" in view_option else "admin"
            st.divider()

        # Language selection for RAG output
        st.markdown("##### 🌐 Response Language")
        languages = {
            "en": "English",
            "bn": "বাংলা (Bengali)",
            "hi": "हिंदी (Hindi)"
        }
        current_lang = st.session_state.get("language", "en")
        selected_lang_label = st.selectbox(
            "Language",
            options=list(languages.values()),
            index=list(languages.keys()).index(current_lang) if current_lang in languages else 0,
            label_visibility="collapsed"
        )
        for code, label in languages.items():
            if label == selected_lang_label:
                st.session_state["language"] = code
                break

        # Voice Assistant Settings
        st.markdown("##### 🎙️ Voice Assistant")
        voice_enabled = st.checkbox("Enable Audio Voice Response", value=st.session_state.get("voice_enabled", False))
        st.session_state["voice_enabled"] = voice_enabled

        st.divider()

        # Chat Sessions & New Chat
        st.markdown("##### 💬 Chat Sessions")
        if st.button("➕ New Chat Session", use_container_width=True, type="primary"):
            res, status = api_client.create_session(token, title="New Conversation", language=st.session_state.get("language", "en"))
            if status == 201:
                st.session_state["active_session_id"] = res.get("session", {}).get("id")
                st.session_state["current_view"] = "chat"
                st.rerun()

        # Fetch sessions
        sessions_res, s_status = api_client.get_sessions(token)
        sessions = sessions_res.get("sessions", []) if s_status == 200 else []

        if not st.session_state.get("active_session_id") and sessions:
            st.session_state["active_session_id"] = sessions[0]["id"]

        if sessions:
            for s in sessions:
                s_id = s["id"]
                s_title = s.get("title", "Conversation")
                is_active = (s_id == st.session_state.get("active_session_id"))

                col1, col2 = st.columns([0.82, 0.18])
                with col1:
                    btn_label = f"💬 {s_title[:22]}..." if len(s_title) > 22 else f"💬 {s_title}"
                    if is_active:
                        btn_label = f"▶ {btn_label}"
                    if st.button(btn_label, key=f"session_btn_{s_id}", use_container_width=True):
                        st.session_state["active_session_id"] = s_id
                        st.session_state["current_view"] = "chat"
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_session_{s_id}", help="Delete this chat"):
                        api_client.delete_session(token, s_id)
                        if st.session_state.get("active_session_id") == s_id:
                            st.session_state["active_session_id"] = None
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧹 Clear All Chats", use_container_width=True):
                api_client.clear_all_sessions(token)
                st.session_state["active_session_id"] = None
                st.success("All chats deleted")
                st.rerun()
        else:
            st.caption("No conversations yet. Start a new chat above!")

        st.divider()

        # Logout button
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
