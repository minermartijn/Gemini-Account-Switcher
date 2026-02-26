import json
import pytest
from typer.testing import CliRunner
from gemini_account_switcher import main, utils
from unittest.mock import MagicMock

runner = CliRunner()

@pytest.fixture
def mock_gemini_env(tmp_path, monkeypatch):
    """
    Sets up a temporary directory structure mimicking ~/.gemini
    and monkeypatches the utils module constants to point to it.
    """
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    
    saved_creds_dir = gemini_dir / "saved_creds"
    saved_creds_dir.mkdir()
    
    creds_file = gemini_dir / "oauth_creds.json"
    token_file = gemini_dir / "mcp-oauth-tokens-v2.json"
    accounts_file = gemini_dir / "google_accounts.json"

    # Monkeypatch the constants in utils
    monkeypatch.setattr(utils, "GEMINI_DIR", gemini_dir)
    monkeypatch.setattr(utils, "CREDS_FILE", creds_file)
    monkeypatch.setattr(utils, "TOKEN_FILE", token_file)
    monkeypatch.setattr(utils, "GOOGLE_ACCOUNTS_FILE", accounts_file)
    monkeypatch.setattr(utils, "SAVED_CREDS_DIR", saved_creds_dir)

    return gemini_dir

def test_list_command_empty(mock_gemini_env):
    result = runner.invoke(main.app, ["list"])
    assert result.exit_code == 0
    assert "No saved accounts found" in result.stdout

def test_save_command_no_login(mock_gemini_env):
    result = runner.invoke(main.app, ["save"])
    assert result.exit_code == 1
    assert "No active Gemini credentials found" in result.stdout

def test_save_command_success(mock_gemini_env, monkeypatch):
    # Mock the two functions the updated save() command relies on
    mock_creds = {"access_token": "tok123", "refresh_token": "ref456"}

    monkeypatch.setattr(utils, "get_current_credentials", lambda: mock_creds)
    monkeypatch.setattr(utils, "get_current_email", lambda: "test@example.com")

    result = runner.invoke(main.app, ["save", "MyAlias"])

    assert result.exit_code == 0
    assert "Successfully saved credentials for test@example.com" in result.stdout
    assert "as alias 'MyAlias'" in result.stdout

    # Verify file created
    assert (utils.SAVED_CREDS_DIR / "test@example.com.json").exists()

def test_next_command(mock_gemini_env, monkeypatch):
    # Setup: 2 accounts, UserA (Old) and UserB (New/Active)
    
    # User A (Oldest)
    utils.save_credentials("usera@test.com", {"id_token": "tokenA"})
    # Manually backdate User A
    path_a = utils.SAVED_CREDS_DIR / "usera@test.com.json"
    with open(path_a, "r") as f: data = json.load(f)
    data["_meta"]["last_used"] = 100
    with open(path_a, "w") as f: json.dump(data, f)
    
    # User B (Newer)
    utils.save_credentials("userb@test.com", {"id_token": "tokenB"})
    path_b = utils.SAVED_CREDS_DIR / "userb@test.com.json"
    with open(path_b, "r") as f: data = json.load(f)
    data["_meta"]["last_used"] = 200
    with open(path_b, "w") as f: json.dump(data, f)

    # Mock User B is currently active
    monkeypatch.setattr(utils, "get_current_email", lambda: "userb@test.com")

    # Run Next
    result = runner.invoke(main.app, ["next"])

    assert result.exit_code == 0
    assert "Rotating to: usera@test.com" in result.stdout

    # Check User A's token is now in the legacy creds file
    with open(utils.CREDS_FILE) as f:
        active = json.load(f)
        assert active["id_token"] == "tokenA"
