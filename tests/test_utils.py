import json
import pytest
from pathlib import Path
from gemini_account_switcher import utils

# Fixture to mock the file system
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
    
    # Monkeypatch the constants in utils
    monkeypatch.setattr(utils, "GEMINI_DIR", gemini_dir)
    monkeypatch.setattr(utils, "CREDS_FILE", creds_file)
    monkeypatch.setattr(utils, "SAVED_CREDS_DIR", saved_creds_dir)
    
    return gemini_dir

def test_save_credentials(mock_gemini_env):
    email = "test@example.com"
    creds = {"access_token": "123", "id_token": "abc"}
    
    # Save credentials
    utils.save_credentials(email, creds, alias="TestAlias")
    
    # Verify file existence
    expected_file = utils.SAVED_CREDS_DIR / f"{email}.json"
    assert expected_file.exists()
    
    # Verify content
    with open(expected_file) as f:
        data = json.load(f)
        assert data["access_token"] == "123"
        assert data["_meta"]["alias"] == "TestAlias"
        assert "last_used" in data["_meta"]

def test_list_saved_accounts_sorted(mock_gemini_env):
    # create dummy files
    files = [
        ("user1@test.com", 100),
        ("user2@test.com", 200),
        ("user3@test.com", 50)  # Oldest
    ]
    
    for email, ts in files:
        file_path = utils.SAVED_CREDS_DIR / f"{email}.json"
        data = {
            "some_data": "true",
            "_meta": {"last_used": ts}
        }
        with open(file_path, "w") as f:
            json.dump(data, f)
            
    # List accounts
    accounts = utils.list_saved_accounts_sorted()
    
    # Expect sorted by timestamp (ascending / oldest first)
    assert len(accounts) == 3
    assert accounts[0][0] == "user3@test.com" # 50
    assert accounts[1][0] == "user1@test.com" # 100
    assert accounts[2][0] == "user2@test.com" # 200

def test_rename_alias(mock_gemini_env):
    email = "rename@test.com"
    creds = {"foo": "bar"}
    utils.save_credentials(email, creds, alias="OldName")
    
    # Rename
    success = utils.rename_alias(email, "NewName")
    assert success is True
    
    # Verify
    saved = utils.load_saved_credentials(email)
    assert saved["_meta"]["alias"] == "NewName"

def test_delete_saved_account(mock_gemini_env):
    email = "delete@test.com"
    utils.save_credentials(email, {"foo": "bar"})
    
    assert utils.delete_saved_account(email) is True
    assert not (utils.SAVED_CREDS_DIR / f"{email}.json").exists()
    
    assert utils.delete_saved_account("nonexistent") is False
