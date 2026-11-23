import os
import requests
from typing import Optional, Dict, Any, Tuple

class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:5000")).rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _safe_request(self, method: str, url: str, **kwargs) -> Tuple[Dict[str, Any], int]:
        """
        Safely execute HTTP request, preventing JSONDecodeError crashes if server returns HTML/errors.
        """
        try:
            resp = requests.request(method, url, timeout=kwargs.pop("timeout", 60), **kwargs)
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text.strip() or f"Server returned status {resp.status_code}"}
            return data, resp.status_code
        except requests.exceptions.ConnectionError:
            return {"error": "Unable to connect to the backend server. Please verify the Flask backend is active on port 5000."}, 503
        except requests.exceptions.Timeout:
            return {"error": "Server request timed out. Please try again."}, 504
        except Exception as e:
            return {"error": f"Network error: {str(e)}"}, 500

    # --- Authentication Endpoints ---
    def register(self, email: str, full_name: str, password: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/auth/register"
        return self._safe_request("POST", url, json={"email": email, "full_name": full_name, "password": password})

    def login(self, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/auth/login"
        return self._safe_request("POST", url, json={"email": email, "password": password})

    def get_profile(self, token: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/auth/me"
        return self._safe_request("GET", url, headers=self._headers(token))

    # --- Chat Session Endpoints ---
    def create_session(self, token: str, title: str = "New Conversation", language: str = "en") -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/sessions"
        return self._safe_request("POST", url, json={"title": title, "language": language}, headers=self._headers(token))

    def get_sessions(self, token: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/sessions"
        return self._safe_request("GET", url, headers=self._headers(token))

    def get_session(self, token: str, session_id: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/sessions/{session_id}"
        return self._safe_request("GET", url, headers=self._headers(token))

    def delete_session(self, token: str, session_id: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/sessions/{session_id}"
        return self._safe_request("DELETE", url, headers=self._headers(token))

    def clear_all_sessions(self, token: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/sessions"
        return self._safe_request("DELETE", url, headers=self._headers(token))

    def query_agent(self, token: str, message: str, session_id: Optional[str] = None, language: str = "en") -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/chat/query"
        payload = {
            "message": message,
            "session_id": session_id,
            "language": language
        }
        return self._safe_request("POST", url, json=payload, headers=self._headers(token))

    # --- Admin PDF Endpoints (RBAC) ---
    def upload_pdf(self, token: str, file_bytes: bytes, filename: str, title: str = "") -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/admin/upload-pdf"
        files = {"file": (filename, file_bytes, "application/pdf")}
        data = {"title": title}
        headers = self._headers(token)
        return self._safe_request("POST", url, files=files, data=data, headers=headers)

    def get_documents(self, token: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/admin/documents"
        return self._safe_request("GET", url, headers=self._headers(token))

    def delete_document(self, token: str, doc_id: str) -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/admin/documents/{doc_id}"
        return self._safe_request("DELETE", url, headers=self._headers(token))

    # --- Voice Assistant Endpoints ---
    def transcribe_audio(self, token: str, audio_bytes: bytes, filename: str = "speech.wav") -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/voice/transcribe"
        files = {"audio": (filename, audio_bytes, "audio/wav")}
        headers = self._headers(token)
        return self._safe_request("POST", url, files=files, headers=headers)

    def synthesize_speech(self, token: str, text: str, language: str = "en") -> Tuple[Dict[str, Any], int]:
        url = f"{self.base_url}/api/voice/synthesize"
        return self._safe_request("POST", url, json={"text": text, "language": language}, headers=self._headers(token))
