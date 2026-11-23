from flask import Blueprint, request, jsonify, current_app
from services.auth_service import token_required
from services.voice_service import VoiceService

voice_bp = Blueprint("voice", __name__, url_prefix="/api/voice")

@voice_bp.route("/transcribe", methods=["POST"])
@token_required
def transcribe_audio_input(current_user):
    """
    Transcribe speech to text using Groq Whisper Large v3.
    Accepts multipart/form-data audio file or raw bytes.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided in request"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "Empty audio filename"}), 400

    voice_service: VoiceService = current_app.config.get("VOICE_SERVICE")
    if not voice_service:
        return jsonify({"error": "Voice service is not initialized on server"}), 500

    try:
        audio_bytes = audio_file.read()
        transcribed_text = voice_service.transcribe_audio(audio_bytes, audio_file.filename)
        return jsonify({"text": transcribed_text}), 200
    except Exception as e:
        return jsonify({"error": f"Audio transcription failed: {str(e)}"}), 500


@voice_bp.route("/synthesize", methods=["POST"])
@token_required
def synthesize_speech_output(current_user):
    """
    Generate speech audio (MP3 data URI) from answer text.
    Supports English, Bengali, and Hindi.
    """
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    language = data.get("language", "en")

    if not text:
        return jsonify({"error": "Text is required for voice synthesis"}), 400

    voice_service: VoiceService = current_app.config.get("VOICE_SERVICE")
    if not voice_service:
        return jsonify({"error": "Voice service is not initialized on server"}), 500

    try:
        audio_url = voice_service.synthesize_speech(text=text, language_code=language)
        return jsonify({"audio_url": audio_url}), 200
    except Exception as e:
        return jsonify({"error": f"Voice synthesis failed: {str(e)}"}), 500
