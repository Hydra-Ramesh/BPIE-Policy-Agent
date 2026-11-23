import streamlit as st
from api_client import APIClient

def render_admin_view(api_client: APIClient):
    token = st.session_state.get("token")
    user = st.session_state.get("user", {})

    if user.get("role") != "admin":
        st.error("⛔ Access Denied: You do not have administrator privileges.")
        return

    import os
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "bpie_logo.jpg")
    col_logo, col_title = st.columns([0.16, 0.84])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
    with col_title:
        st.markdown("""
            <div style="padding-top: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0; color: #DC3545; font-size: 1.55rem;">📑 Policy Document Management (RBAC)</h2>
                        <h4 style="margin: 2px 0 0 0; color: #1E293B; font-size: 1.05rem; font-weight: 600;">Bishnupur Public Institute of Engineering</h4>
                        <p style="margin: 3px 0 0 0; color: #64748B; font-size: 0.85rem;">
                            Bishnupur, Bankura • Estd. 2010 • Upload official institute PDFs, inspect vector embeddings, and manage active Qdrant knowledge base.
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    tab_upload, tab_manage = st.tabs(["📤 Upload New Policy PDF", "📚 Indexed Knowledge Base"])

    # --- TAB 1: UPLOAD ---
    with tab_upload:
        st.subheader("Upload Official College Regulations PDF")
        st.caption("Supported: Academic Regulations, Examination Rules, Anti-Ragging Policies, Code of Conduct, Hostel Rules.")

        with st.form("upload_pdf_form", clear_on_submit=True):
            custom_title = st.text_input("Document Official Title", placeholder="e.g. BPIE Academic Regulations 2026")
            uploaded_file = st.file_uploader("Select PDF File", type=["pdf"], help="Upload official institute PDF (up to 32MB)")
            submit_upload = st.form_submit_button("Upload & Index to Vector DB", type="primary", use_container_width=True)

        if submit_upload:
            if not uploaded_file:
                st.error("Please select a PDF file to upload.")
            else:
                title_to_use = custom_title.strip() or uploaded_file.name.replace(".pdf", "").replace("_", " ").title()
                with st.spinner("Extracting text by page, generating embeddings, and updating Qdrant vector database..."):
                    file_bytes = uploaded_file.read()
                    res, status = api_client.upload_pdf(
                        token=token,
                        file_bytes=file_bytes,
                        filename=uploaded_file.name,
                        title=title_to_use
                    )
                    if status == 201:
                        st.success(f"✅ Successfully indexed '{title_to_use}'! Total {res.get('chunks_indexed', 0)} vector chunks stored in Qdrant.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to upload and index document."))

    # --- TAB 2: MANAGE ---
    with tab_manage:
        st.subheader("Currently Indexed College Documents")
        res, status = api_client.get_documents(token)
        documents = res.get("documents", []) if status == 200 else []

        if not documents:
            st.info("No policy documents have been uploaded yet. Upload your first institute PDF above to activate RAG!")
        else:
            st.write(f"Total **{len(documents)}** active policy documents indexed in Qdrant Vector DB.")
            for doc in documents:
                doc_id = doc.get("id")
                title = doc.get("title")
                filename = doc.get("filename")
                chunks = doc.get("chunks_count", 0)
                file_size_kb = round(doc.get("file_size", 0) / 1024, 1)
                created_at = (doc.get("created_at") or "")[:10]

                col_info, col_del = st.columns([0.85, 0.15])
                with col_info:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
                            <div style="font-weight: 700; font-size: 1rem; color: #1E293B;">📄 {title}</div>
                            <div style="font-size: 0.85rem; color: #64748B; margin-top: 4px;">
                                File: <code>{filename}</code> | Size: <b>{file_size_kb} KB</b> | Vector Chunks: <b>{chunks}</b> | Uploaded: <b>{created_at}</b>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_doc_{doc_id}", help="Purge document and delete vectors from Qdrant"):
                        with st.spinner("Deleting document and vector embeddings..."):
                            del_res, del_status = api_client.delete_document(token, doc_id)
                            if del_status == 200:
                                st.success("Document purged successfully!")
                                st.rerun()
                            else:
                                st.error(del_res.get("error", "Failed to delete document."))
