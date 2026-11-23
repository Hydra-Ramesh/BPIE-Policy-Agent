import streamlit as st
from api_client import APIClient

def render_chat_view(api_client: APIClient):
    token = st.session_state.get("token")
    session_id = st.session_state.get("active_session_id")
    language = st.session_state.get("language", "en")
    voice_enabled = st.session_state.get("voice_enabled", False)

    # Top Banner with College Logo
    import os
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "bpie_logo.jpg")
    col_logo, col_title = st.columns([0.16, 0.84])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
    with col_title:
        st.markdown("""
            <div style="padding-top: 4px;">
                <h2 style="margin: 0; color: #0D6EFD; font-size: 1.55rem;">BPIE Policy & Regulations Assistant</h2>
                <h4 style="margin: 2px 0 0 0; color: #1E293B; font-size: 1.05rem; font-weight: 600;">Bishnupur Public Institute of Engineering</h4>
                <p style="margin: 3px 0 0 0; color: #64748B; font-size: 0.85rem;">
                    Bishnupur, Bankura • Estd. 2010 • A Polytechnic College | Verified answers backed by institutional regulations.
                </p>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # Load session history if active session exists
    messages = []
    if session_id:
        res, status = api_client.get_session(token, session_id)
        if status == 200:
            messages = res.get("session", {}).get("messages", [])
        elif status == 404:
            st.session_state["active_session_id"] = None

    # Render message history
    if not messages:
        st.markdown("""
            <div style="text-align: center; padding: 40px 20px; background: white; border-radius: 12px; border: 1px dashed #CBD5E1; margin: 30px 0;">
                <h3 style="color: #334155;">How can I assist you today?</h3>
                <p style="color: #64748B; max-width: 550px; margin: 0 auto 20px auto;">
                    You can ask about attendance minimums, examination rules, hostel curfew, disciplinary actions, anti-ragging policies, or fee submission deadlines.
                </p>
                <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                    <span style="background: #EFF6FF; color: #1D4ED8; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #BFDBFE;">
                        📋 What is the minimum attendance requirement for semester exams?
                    </span>
                    <span style="background: #EFF6FF; color: #1D4ED8; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #BFDBFE;">
                        🛑 What are the institute's anti-ragging measures?
                    </span>
                    <span style="background: #EFF6FF; color: #1D4ED8; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #BFDBFE;">
                        🏠 What are the hostel curfew hours and gate pass rules?
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            sources = msg.get("sources", [])

            with st.chat_message(role):
                st.markdown(content)

                # Render production citations if present
                if role == "assistant" and sources:
                    with st.expander("📚 Verified Policy References & Citations", expanded=False):
                        for src in sources:
                            doc_title = src.get("document", "Official Document")
                            page = src.get("page", 1)
                            snippet = src.get("snippet", "")
                            st.markdown(f"""
                                <div style="background: #F8FAFC; border-left: 3px solid #0D6EFD; padding: 8px 12px; margin-bottom: 8px; border-radius: 0 6px 6px 0;">
                                    <div style="font-weight: 600; font-size: 0.85rem; color: #0F172A;">
                                        📄 {doc_title} — Page {page}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #475569; font-style: italic; margin-top: 3px;">
                                        "{snippet}"
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

    # Voice Input section (Speech-to-Text via Groq Whisper Large v3)
    with st.expander("🎙️ Speak your question (Voice Input Assistant)", expanded=False):
        st.caption("Record your voice query in English, Bengali, or Hindi. Powered by Groq Whisper Large v3.")
        audio_file = None
        # Use native st.audio_input if available in this streamlit version, else st.file_uploader
        try:
            audio_file = st.audio_input("Record audio from microphone")
        except AttributeError:
            audio_file = st.file_uploader("Upload audio recording (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a", "ogg"])

        if audio_file is not None and st.button("Transcribe & Send Voice Query", type="secondary"):
            with st.spinner("Transcribing audio with Groq Whisper..."):
                audio_bytes = audio_file.read()
                fname = getattr(audio_file, "name", "voice_input.wav")
                stt_res, stt_status = api_client.transcribe_audio(token, audio_bytes, fname)
                if stt_status == 200:
                    transcribed_text = stt_res.get("text", "")
                    st.info(f"🎤 Transcribed: *\"{transcribed_text}\"*")
                    if transcribed_text:
                        _process_query(api_client, token, transcribed_text, session_id, language, voice_enabled)
                else:
                    st.error(stt_res.get("error", "Transcription failed."))

    # Text Input box
    user_query = st.chat_input("Ask a question about BPIE rules, regulations, attendance, hostel, exams...")
    if user_query:
        _process_query(api_client, token, user_query, session_id, language, voice_enabled)

def _process_query(api_client, token, query_text, session_id, language, voice_enabled):
    with st.chat_message("user"):
        st.markdown(query_text)

    with st.chat_message("assistant"):
        with st.spinner("Consulting official BPIE policy documents..."):
            res, status = api_client.query_agent(
                token=token,
                message=query_text,
                session_id=session_id,
                language=language
            )

            if status == 200:
                answer = res.get("answer", "")
                sources = res.get("sources", [])
                st.session_state["active_session_id"] = res.get("session_id")

                st.markdown(answer)

                if sources:
                    with st.expander("📚 Verified Policy References & Citations", expanded=False):
                        for src in sources:
                            doc_title = src.get("document", "Official Document")
                            page = src.get("page", 1)
                            snippet = src.get("snippet", "")
                            st.markdown(f"""
                                <div style="background: #F8FAFC; border-left: 3px solid #0D6EFD; padding: 8px 12px; margin-bottom: 8px; border-radius: 0 6px 6px 0;">
                                    <div style="font-weight: 600; font-size: 0.85rem; color: #0F172A;">
                                        📄 {doc_title} — Page {page}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #475569; font-style: italic; margin-top: 3px;">
                                        "{snippet}"
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                if voice_enabled:
                    with st.spinner("Synthesizing audio voice response..."):
                        tts_res, tts_status = api_client.synthesize_speech(token, answer, language)
                        if tts_status == 200:
                            audio_url = tts_res.get("audio_url")
                            st.audio(audio_url, format="audio/mp3", autoplay=True)

                st.rerun()
            else:
                st.error(res.get("error", "Error contacting the Policy Agent."))
