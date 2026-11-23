import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.document import PolicyDocument
from services.auth_service import admin_required
from services.pdf_service import PDFService
from utils.validators import sanitize_filename

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/upload-pdf", methods=["POST"])
@admin_required
def upload_policy_pdf(current_user: User):
    """
    RBAC Protected: Only Admin can upload official college policy PDFs.
    Parses PDF, extracts text by page, splits into chunks, and indexes into Qdrant.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    raw_filename = secure_filename(file.filename)
    safe_name = sanitize_filename(raw_filename)
    custom_title = request.form.get("title", "").strip() or os.path.splitext(safe_name)[0].replace("_", " ").title()

    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, safe_name)
    file.save(file_path)

    pdf_service = PDFService()
    rag_service = current_app.config.get("RAG_SERVICE")

    try:
        # Extract and chunk
        chunks = pdf_service.extract_and_chunk(file_path=file_path, document_title=custom_title)
        if not chunks:
            return jsonify({"error": "No readable text could be extracted from this PDF"}), 400

        # Calculate hash and size
        file_hash = pdf_service.calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)

        # Create PolicyDocument record in DB
        doc_record = PolicyDocument(
            title=custom_title,
            filename=safe_name,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            chunks_count=len(chunks),
            uploaded_by=current_user.id
        )
        db.session.add(doc_record)
        db.session.commit()

        # Embed & index into Qdrant
        if rag_service:
            indexed_count = rag_service.index_chunks(
                document_id=doc_record.id,
                document_title=custom_title,
                chunks=chunks
            )
        else:
            indexed_count = 0

        return jsonify({
            "message": f"Document '{custom_title}' successfully uploaded and indexed.",
            "document": doc_record.to_dict(),
            "chunks_indexed": indexed_count
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process and index document: {str(e)}"}), 500


@admin_bp.route("/documents", methods=["GET"])
@admin_required
def list_documents(current_user: User):
    """
    RBAC Protected: List all indexed college policy documents.
    """
    docs = PolicyDocument.query.order_by(PolicyDocument.created_at.desc()).all()
    return jsonify({
        "documents": [d.to_dict() for d in docs]
    }), 200


@admin_bp.route("/documents/<doc_id>", methods=["DELETE"])
@admin_required
def delete_document(current_user: User, doc_id: str):
    """
    RBAC Protected: Delete a policy document, purge its vectors from Qdrant,
    and remove the stored PDF file.
    """
    doc = PolicyDocument.query.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    rag_service = current_app.config.get("RAG_SERVICE")
    # Delete points from Qdrant
    if rag_service:
        rag_service.delete_document_points(document_id=doc.id)

    # Remove physical file if it exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            print(f"[Admin] Warning: Could not remove file {doc.file_path}: {e}")

    # Remove from database
    db.session.delete(doc)
    db.session.commit()

    return jsonify({
        "message": f"Document '{doc.title}' and all associated vector embeddings have been deleted successfully."
    }), 200
