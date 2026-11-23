from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models.user import User
from models.chat import ChatSession, ChatMessage
from services.auth_service import token_required

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

@chat_bp.route("/sessions", methods=["POST"])
@token_required
def create_session(current_user: User):
    """
    Create a new chat session for the authenticated user.
    """
    data = request.get_json() or {}
    title = data.get("title", "New Conversation").strip()
    language = data.get("language", "en").strip()

    session = ChatSession(
        user_id=current_user.id,
        title=title,
        language=language
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "message": "Chat session created",
        "session": session.to_dict(include_messages=True)
    }), 201


@chat_bp.route("/sessions", methods=["GET"])
@token_required
def list_sessions(current_user: User):
    """
    List all chat sessions belonging to current user, ordered by newest updated.
    """
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return jsonify({
        "sessions": [s.to_dict(include_messages=False) for s in sessions]
    }), 200


@chat_bp.route("/sessions/<session_id>", methods=["GET"])
@token_required
def get_session(current_user: User, session_id: str):
    """
    Retrieve message history for a specific chat session.
    """
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({
        "session": session.to_dict(include_messages=True)
    }), 200


@chat_bp.route("/sessions/<session_id>", methods=["DELETE"])
@token_required
def delete_session(current_user: User, session_id: str):
    """
    Delete a specific chat session and all associated messages.
    """
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session)
    db.session.commit()

    return jsonify({"message": "Chat session deleted successfully"}), 200


@chat_bp.route("/sessions", methods=["DELETE"])
@token_required
def clear_all_sessions(current_user: User):
    """
    Delete all chat sessions and history for the current user.
    """
    sessions = ChatSession.query.filter_by(user_id=current_user.id).all()
    count = len(sessions)
    for s in sessions:
        db.session.delete(s)
    db.session.commit()

    return jsonify({"message": f"Successfully deleted {count} chat sessions"}), 200


@chat_bp.route("/query", methods=["POST"])
@token_required
def query_agent(current_user: User):
    """
    Send question to RAG Policy Agent, record user message and assistant answer.
    """
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    session_id = data.get("session_id")
    language = data.get("language", "en")

    if not message_text:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Find or create session
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({"error": "Session not found"}), 404
    else:
        # Create a new session automatically
        preview_title = (message_text[:30] + "...") if len(message_text) > 30 else message_text
        session = ChatSession(
            user_id=current_user.id,
            title=preview_title,
            language=language
        )
        db.session.add(session)
        db.session.flush()

    # Load history for context
    history_messages = [
        {"role": m.role, "content": m.content}
        for m in session.messages[-8:]
    ]

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=message_text
    )
    db.session.add(user_msg)

    # Invoke RAG Service
    rag_service = current_app.config.get("RAG_SERVICE")
    if not rag_service:
        return jsonify({"error": "RAG Service is not initialized on server"}), 500

    rag_result = rag_service.answer_query(
        query=message_text,
        conversation_history=history_messages,
        language=language
    )

    answer_text = rag_result.get("answer", "No response generated.")
    sources = rag_result.get("sources", [])

    # Save assistant message with citations
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        sources=sources
    )
    db.session.add(assistant_msg)

    # Auto-update session title if it was default
    if session.title == "New Conversation" or not session.title:
        session.title = (message_text[:35] + "...") if len(message_text) > 35 else message_text

    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "user_message": user_msg.to_dict(),
        "assistant_message": assistant_msg.to_dict(),
        "answer": answer_text,
        "sources": sources
    }), 200
