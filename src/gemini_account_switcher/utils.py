import json
import os
import hashlib
import shutil
import socket
import getpass
import jwt
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

# Constants
GEMINI_DIR = Path.home() / ".gemini"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"           # Legacy file (kept for compat)
TOKEN_FILE = GEMINI_DIR / "mcp-oauth-tokens-v2.json"  # Gemini CLI v0.30+ encrypted storage
GOOGLE_ACCOUNTS_FILE = GEMINI_DIR / "google_accounts.json"
SAVED_CREDS_DIR = GEMINI_DIR / "saved_creds"
MAIN_ACCOUNT_KEY = "main-account"  # Key used by Gemini CLI internally

def ensure_dirs():
    """Ensure the saved credentials directory exists."""
    SAVED_CREDS_DIR.mkdir(parents=True, exist_ok=True)


# ─── AES-256-GCM helpers (matches Gemini CLI v0.30+ FileTokenStorage) ──────

def _derive_encryption_key() -> bytes:
    """
    Derive the AES-256 key using the same algorithm as Gemini CLI's FileTokenStorage.
    scryptSync('gemini-cli-oauth', '{hostname}-{username}-gemini-cli', 32)
    """
    hostname = socket.gethostname()
    username = getpass.getuser()
    salt = f"{hostname}-{username}-gemini-cli"
    return hashlib.scrypt(
        b"gemini-cli-oauth",
        salt=salt.encode("utf-8"),
        n=16384,
        r=8,
        p=1,
        dklen=32,
    )


def _encrypt(text: str, key: bytes) -> str:
    """AES-256-GCM encrypt. Returns 'iv_hex:authtag_hex:ciphertext_hex'."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(16)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(iv, text.encode("utf-8"), None)
    ciphertext, tag = ct_with_tag[:-16], ct_with_tag[-16:]
    return iv.hex() + ":" + tag.hex() + ":" + ciphertext.hex()


def _decrypt(encrypted_data: str, key: bytes) -> str:
    """AES-256-GCM decrypt from 'iv_hex:authtag_hex:ciphertext_hex'."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    parts = encrypted_data.split(":")
    if len(parts) != 3:
        raise ValueError("Invalid encrypted data format")
    iv = bytes.fromhex(parts[0])
    tag = bytes.fromhex(parts[1])
    ciphertext = bytes.fromhex(parts[2])
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext + tag, None).decode("utf-8")


def _load_token_file() -> Optional[Dict[str, Any]]:
    """
    Decrypt and load mcp-oauth-tokens-v2.json.
    Returns the credential entry for MAIN_ACCOUNT_KEY, or None.
    """
    if not TOKEN_FILE.exists():
        return None
    try:
        key = _derive_encryption_key()
        encrypted = TOKEN_FILE.read_text("utf-8")
        data = json.loads(_decrypt(encrypted, key))
        return data.get(MAIN_ACCOUNT_KEY)
    except Exception:
        return None


def _save_token_file(creds: Dict[str, Any]) -> None:
    """
    Encrypt and write credentials into mcp-oauth-tokens-v2.json.
    Converts from Google OAuth format to Gemini CLI's internal MCP format.
    Preserves any other server entries already in the file.
    """
    # Load existing encrypted data so we preserve other MCP server entries
    existing: Dict[str, Any] = {}
    if TOKEN_FILE.exists():
        try:
            key_r = _derive_encryption_key()
            existing = json.loads(_decrypt(TOKEN_FILE.read_text("utf-8"), key_r))
        except Exception:
            pass

    # Convert Google Credentials → Gemini CLI OAuthCredentials format
    mcp_entry = {
        "serverName": MAIN_ACCOUNT_KEY,
        "token": {
            "accessToken":  creds.get("access_token"),
            "refreshToken": creds.get("refresh_token"),
            "tokenType":    creds.get("token_type", "Bearer"),
            "scope":        creds.get("scope"),
            "expiresAt":    creds.get("expiry_date"),
        },
        "updatedAt": int(time.time() * 1000),
    }
    existing[MAIN_ACCOUNT_KEY] = mcp_entry

    key_w = _derive_encryption_key()
    encrypted = _encrypt(json.dumps(existing, indent=2), key_w)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(encrypted, "utf-8")
    TOKEN_FILE.chmod(0o600)


# ─── google_accounts.json helpers ────────────────────────────────────────────

def _update_google_accounts(new_email: str) -> None:
    """
    Update google_accounts.json: set active to new_email,
    move the previous active into the 'old' list (deduped).
    """
    try:
        data: Dict[str, Any] = {}
        if GOOGLE_ACCOUNTS_FILE.exists():
            try:
                parsed = json.loads(GOOGLE_ACCOUNTS_FILE.read_text("utf-8"))
                if isinstance(parsed, dict) and isinstance(parsed.get("old"), list):
                    data = parsed
            except Exception:
                pass

        current_active = data.get("active", "")
        old_list: List[str] = data.get("old", [])

        if current_active and current_active != new_email:
            if current_active not in old_list:
                old_list.append(current_active)

        # Remove new_email from old list if present
        old_list = [e for e in old_list if e != new_email]

        GOOGLE_ACCOUNTS_FILE.write_text(
            json.dumps({"active": new_email, "old": old_list}, indent=2),
            "utf-8",
        )
    except Exception:
        pass  # Non-fatal


# ─── Public credential API ────────────────────────────────────────────────────

def get_current_email() -> Optional[str]:
    """
    Return the email of the currently active Gemini account.
    Checks google_accounts.json first (works with all Gemini CLI versions),
    then falls back to jwt-decoding the id_token in oauth_creds.json.
    """
    # 1. New format: google_accounts.json (Gemini CLI v0.30+)
    if GOOGLE_ACCOUNTS_FILE.exists():
        try:
            d = json.loads(GOOGLE_ACCOUNTS_FILE.read_text("utf-8"))
            if isinstance(d, dict) and d.get("active"):
                return d["active"]
        except Exception:
            pass

    # 2. Legacy: id_token inside oauth_creds.json
    creds = _load_legacy_creds()
    if creds and "id_token" in creds:
        return get_email_from_token(creds["id_token"])

    return None


def _load_legacy_creds() -> Optional[Dict[str, Any]]:
    """Read the legacy oauth_creds.json file (no decryption needed)."""
    if not CREDS_FILE.exists():
        return None
    try:
        return json.loads(CREDS_FILE.read_text("utf-8"))
    except json.JSONDecodeError:
        return None


def get_current_credentials() -> Optional[Dict[str, Any]]:
    """
    Read the currently active OAuth credentials.
    Tries the new encrypted token file first, then falls back to the legacy file.
    Returns a dict in legacy Google format (access_token, refresh_token, etc.).
    """
    # 1. New encrypted format (Gemini CLI v0.30+). Only use if a real accessToken exists.
    token_entry = _load_token_file()
    if token_entry and token_entry.get("token") and token_entry["token"].get("accessToken"):
        t = token_entry["token"]
        return {
            "access_token":  t.get("accessToken"),
            "refresh_token": t.get("refreshToken"),
            "token_type":    t.get("tokenType"),
            "scope":         t.get("scope"),
            "expiry_date":   t.get("expiresAt"),
        }

    # 2. Legacy file (includes id_token)
    return _load_legacy_creds()


def get_email_from_token(token: str) -> Optional[str]:
    """Decode the JWT id_token to extract the email address."""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("email")
    except Exception:
        return None

def save_credentials(email: str, creds: Dict[str, Any], alias: Optional[str] = None) -> Path:
    """
    Save the credentials dictionary to a file named after the email.
    The 'alias' and 'email_hint' are stored in the _meta field.
    """
    ensure_dirs()
    file_path = SAVED_CREDS_DIR / f"{email}.json"

    existing_meta: Dict[str, Any] = {}
    if file_path.exists():
        try:
            data = json.loads(file_path.read_text("utf-8"))
            existing_meta = data.get("_meta", {})
        except json.JSONDecodeError:
            pass

    existing_meta["last_used"] = time.time()
    # Always persist the email so activate_credentials can find it without id_token
    existing_meta["email_hint"] = email
    if alias:
        existing_meta["alias"] = alias

    creds_to_save = creds.copy()
    creds_to_save["_meta"] = existing_meta
    file_path.write_text(json.dumps(creds_to_save, indent=2), "utf-8")
    return file_path

def load_saved_credentials(email: str) -> Optional[Dict[str, Any]]:
    """Load credentials for a specific email."""
    file_path = SAVED_CREDS_DIR / f"{email}.json"
    if not file_path.exists():
        return None
    try:
        return json.loads(file_path.read_text("utf-8"))
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
        meta = get_account_meta(email)
        last_used = meta.get("last_used", 0.0)
        accounts.append((email, meta, last_used))

    accounts.sort(key=lambda x: x[2])
    return [(email, meta) for email, meta, _ in accounts]

def activate_credentials(creds: Dict[str, Any], email: Optional[str] = None) -> None:
    """
    Activate the given credentials as the current Gemini session.

    Writes to:
      1. mcp-oauth-tokens-v2.json  – encrypted file that Gemini CLI v0.30+ reads
      2. oauth_creds.json          – legacy file (kept for backward compat / email extraction)
      3. google_accounts.json      – updates the 'active' email entry

    Also bumps the last_used timestamp in our saved_creds store.
    """
    # Resolve the email (needed for google_accounts.json)
    if not email:
        meta = creds.get("_meta", {})
        email = meta.get("email_hint")  # stored by save_credentials()
    if not email and "id_token" in creds:
        email = get_email_from_token(creds["id_token"])

    # Strip internal metadata before writing to any Gemini file
    clean = {k: v for k, v in creds.items() if k != "_meta"}

    # 1. Write to the new encrypted token file (primary path Gemini CLI reads)
    try:
        _save_token_file(clean)
    except ImportError:
        pass  # cryptography not installed – fall through to legacy file only

    # 2. Write the legacy oauth_creds.json (secondary; also keeps id_token available)
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDS_FILE.write_text(json.dumps(clean, indent=2), "utf-8")

    # 3. Update google_accounts.json so Gemini CLI shows the correct active account
    if email:
        _update_google_accounts(email)

    # 4. Bump last_used timestamp in our own saved_creds store
    if email:
        saved = load_saved_credentials(email)
        if saved:
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
            # Restore "no login" state by removing both credential files
            CREDS_FILE.unlink(missing_ok=True)
            TOKEN_FILE.unlink(missing_ok=True)

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