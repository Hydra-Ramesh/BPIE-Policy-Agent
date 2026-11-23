import re

def is_valid_bpie_email(email: str, allowed_domain: str = "@bpie.ac.in") -> bool:
    """
    Validates if the email belongs to the college domain (e.g. @bpie.ac.in).
    """
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    pattern = rf"^[a-zA-Z0-9_.+-]+{re.escape(allowed_domain)}$"
    return bool(re.match(pattern, email))

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove problematic characters.
    """
    import os
    clean = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
    return clean
