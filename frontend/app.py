import os
import streamlit as st
from dotenv import load_dotenv
from api_client import APIClient
from components.auth_view import render_auth_view
from components.sidebar import render_sidebar
from components.chat_view import render_chat_view
from components.admin_view import render_admin_view

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Page Configuration
logo_path = os.path.join(os.path.dirname(__file__), "assets", "bpie_logo.jpg")

st.set_page_config(
    page_title="BPIE AI Policy Agent | Bishnupur Public Institute of Engineering",
    page_icon=logo_path if os.path.exists(logo_path) else "🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
        /* Base typography & colors */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
        }
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #FAFAFA;
            border-right: 1px solid #E5E7EB;
        }
        /* Chat message container */
        .stChatMessage {
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize API Client
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
api_client = APIClient(base_url=BACKEND_URL)

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "active_session_id" not in st.session_state:
    st.session_state["active_session_id"] = None
if "language" not in st.session_state:
    st.session_state["language"] = "en"
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "chat"
if "voice_enabled" not in st.session_state:
    st.session_state["voice_enabled"] = False

# Application Flow
def main():
    token = st.session_state.get("token")

    if not token:
        render_auth_view(api_client)
    else:
        render_sidebar(api_client)

        current_view = st.session_state.get("current_view", "chat")
        user = st.session_state.get("user", {})

        if current_view == "admin" and user.get("role") == "admin":
            render_admin_view(api_client)
        else:
            render_chat_view(api_client)

if __name__ == "__main__":
    main()
