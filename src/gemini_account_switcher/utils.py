import json
import shutil
import jwt
from pathlib import Path
from typing import Optional, Dict, Any, List

# Constants
GEMINI_DIR = Path.home() / ".gemini"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
SAVED_CREDS_DIR = GEMINI_DIR / "saved_creds"

def ensure_dirs():
    """Ensure the saved credentials directory exists."""
    SAVED_CREDS_DIR.mkdir(parents=True, exist_ok=True)

def get_current_credentials() -> Optional[Dict[str, Any]]:
    """Read the current oauth_creds.json file."""
    if not CREDS_FILE.exists():
        return None
    try:
        with open(CREDS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def get_email_from_token(token: str) -> Optional[str]:
    """Decode the JWT id_token to extract the email address."""
    try:
        # We don't verify the signature here as we just want the email 
        # for identification purposes and we trust the file on disk.
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("email")
    except Exception:
        return None

def save_credentials(email: str, creds: Dict[str, Any]) -> Path:
    """Save the credentials dictionary to a file named after the email."""
    ensure_dirs()
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    with open(file_path, "w") as f:
        json.dump(creds, f, indent=2)
    return file_path

def load_saved_credentials(email: str) -> Optional[Dict[str, Any]]:
    """Load credentials for a specific email."""
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def list_saved_accounts() -> List[str]:
    """Return a list of emails for which we have saved credentials."""
    ensure_dirs()
    files = SAVED_CREDS_DIR.glob("*.json")
    return [f.stem for f in files]

def activate_credentials(creds: Dict[str, Any]):
    """Write the provided credentials to the active oauth_creds.json file."""
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

def delete_saved_account(email: str) -> bool:
    """Delete the saved credential file for an email."""
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    if file_path.exists():
        file_path.unlink()
        return True
    return False
