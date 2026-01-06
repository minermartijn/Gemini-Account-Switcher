import json
import shutil
import jwt
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

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

def save_credentials(email: str, creds: Dict[str, Any], alias: Optional[str] = None) -> Path:
    """
    Save the credentials dictionary to a file named after the email.
    The 'alias' is stored in the _meta field.
    """
    ensure_dirs()
    
    # Always use the email address as the filename to ensure uniqueness
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    
    existing_meta = {}
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                existing_meta = data.get("_meta", {})
        except json.JSONDecodeError:
            pass
            
    # Update timestamp
    existing_meta["last_used"] = time.time()
    
    # Update alias if provided
    if alias:
        existing_meta["alias"] = alias
    
    # Create a copy to avoid modifying the original dictionary in memory
    creds_to_save = creds.copy()
    creds_to_save["_meta"] = existing_meta

    with open(file_path, "w") as f:
        json.dump(creds_to_save, f, indent=2)
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

def get_account_meta(email: str) -> Dict[str, Any]:
    """Helper to get the metadata for an account."""
    creds = load_saved_credentials(email)
    if not creds:
        return {}
    return creds.get("_meta", {})

def list_saved_accounts_sorted() -> List[Tuple[str, Dict[str, Any]]]:
    """
    Return a list of (email, meta) tuples sorted by last used (oldest first).
    """
    ensure_dirs()
    files = list(SAVED_CREDS_DIR.glob("*.json"))
    
    accounts = []
    for f in files:
        email = f.stem
        # Filter out any non-email filenames if they exist from previous versions (optional cleanup)
        # For now, we assume all .json files are accounts.
        meta = get_account_meta(email)
        last_used = meta.get("last_used", 0.0)
        accounts.append((email, meta, last_used))
    
    # Sort by timestamp ascending (oldest first)
    accounts.sort(key=lambda x: x[2])
    
    return [(email, meta) for email, meta, _ in accounts]

def activate_credentials(creds: Dict[str, Any]):
    """Write the provided credentials to the active oauth_creds.json file."""
    # We strip out the _meta field before writing to the main oauth_creds file
    creds_to_write = creds.copy()
    if "_meta" in creds_to_write:
        del creds_to_write["_meta"]

    with open(CREDS_FILE, "w") as f:
        json.dump(creds_to_write, f, indent=2)
        
    # Update the 'last_used' timestamp in the saved file for this account
    if "id_token" in creds:
        email = get_email_from_token(creds["id_token"])
        if email:
            # Re-save with updated timestamp, preserving existing alias
            saved = load_saved_credentials(email)
            if saved:
                # We pass alias=None so it doesn't overwrite the existing alias,
                # but save_credentials updates the timestamp automatically.
                save_credentials(email, saved)


def delete_saved_account(email: str) -> bool:
    """Delete the saved credential file for an email."""
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    if file_path.exists():
        file_path.unlink()
        return True
    return False

def rename_alias(email: str, new_alias: str) -> bool:
    """Update the alias for an existing account."""
    creds = load_saved_credentials(email)
    if not creds:
        return False
    
    save_credentials(email, creds, alias=new_alias)
    return True

@contextmanager
def temporary_switch(email: str):
    """
    Context manager to temporarily switch to an account and switch back on exit.
    Usage:
        with temporary_switch("user@example.com"):
            subprocess.run(...)
    """
    original_creds = get_current_credentials()
    target_creds = load_saved_credentials(email)
    
    if not target_creds:
        raise ValueError(f"Account {email} not found.")

    try:
        # Switch to target
        activate_credentials(target_creds)
        yield
    finally:
        # Switch back to original, if it existed
        if original_creds:
            activate_credentials(original_creds)
        else:
            # If there were no creds before, remove the current ones? 
            # Safer to leave the last used one or delete file.
            # Here we choose to delete to restore "no login" state.
            if CREDS_FILE.exists():
                CREDS_FILE.unlink()

def create_backup(zip_path: Path):
    """Create a zip backup of the saved credentials directory."""
    ensure_dirs()
    if zip_path.suffix != ".zip":
        zip_path = zip_path.with_suffix(".zip")
    
    shutil.make_archive(str(zip_path.with_suffix("")), 'zip', SAVED_CREDS_DIR)
    return zip_path

def restore_backup(zip_path: Path):
    """Restore credentials from a zip backup."""
    ensure_dirs()
    if not zip_path.exists():
        raise FileNotFoundError(f"Backup file not found: {zip_path}")
        
    shutil.unpack_archive(str(zip_path), SAVED_CREDS_DIR)