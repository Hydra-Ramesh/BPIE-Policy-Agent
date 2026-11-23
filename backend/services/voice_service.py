import os
import io
import base64
from groq import Groq
from gtts import gTTS

class VoiceService:
    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

    def transcribe_audio(self, audio_file_bytes: bytes, filename: str = "voice_input.wav") -> str:
        """
        Transcribe audio input using Groq's high-speed Whisper Large v3 model.
        Supports multiple languages (English, Bengali, Hindi, etc.)
        """
        if not self.client:
            raise ValueError("GROQ_API_KEY is not configured for Whisper transcription.")

        audio_file = (filename, audio_file_bytes)
        transcription = self.client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="json",
            temperature=0.0
        )
        return transcription.text.strip()

    def synthesize_speech(self, text: str, language_code: str = "en") -> str:
        """
        Synthesize text into speech using gTTS.
        Supports:
          'en' -> English
          'hi' -> Hindi
          'bn' -> Bengali
        Returns base64 encoded audio string (MP3) ready for inline HTML audio player.
        """
        # Map frontend language keys to gTTS language codes
        lang_map = {
            "en": "en",
            "english": "en",
            "bn": "bn",
            "bengali": "bn",
            "hi": "hi",
            "hindi": "hi"
        }
        lang = lang_map.get(language_code.lower(), "en")

        # Strip markdown syntax for natural voice synthesis
        clean_text = self._clean_markdown(text)
        # Limit text length for TTS to prevent excessive audio duration
        if len(clean_text) > 800:
            clean_text = clean_text[:800] + "... Please read the remaining response on screen."

        tts = gTTS(text=clean_text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_b64 = base64.b64encode(fp.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{audio_b64}"

    def _clean_markdown(self, text: str) -> str:
        import re
        # Remove bold, italics, links, headers
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        text = re.sub(r"[*_#`]", "", text)
        text = re.sub(r"\n+", " ", text)
        return text.strip()
