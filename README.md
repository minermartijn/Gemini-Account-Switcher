<div align="center">
  <img src="images/banner.png" alt="Gemini Account Switcher Banner" width="100%">
</div>

# 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/minermartijn/Gemini-Account-Switcher/actions/workflows/test.yml/badge.svg)](https://github.com/minermartijn/Gemini-Account-Switcher/actions/workflows/test.yml)

A professional, secure, and elegant CLI tool to manage multiple Gemini accounts. Designed specifically for users of the Gemini interactive CLI.

---

## 🚀 Pro Tip: Using inside the Gemini CLI
If you are already inside the **Gemini interactive shell**, you don't need to exit! Just use the `!` prefix to run switcher commands:

*   `!gemini-switch` - Launch the **Interactive Menu**.
*   `!gemini-switch next` - Switch to the next available account.

---

## 🛠 Setup & Usage

### 1. Installation
```bash
git clone https://github.com/minermartijn/Gemini-Account-Switcher.git
cd Gemini-Account-Switcher
pip install .
```

### 2. Interactive Mode (New!)
Simply run the command without arguments to launch the menu:
```bash
gemini-switch
```
Use arrow keys to select an account, save your current login, or exit.

### 3. Adding your first account
Inside the Gemini CLI, authenticate your first account:
1.  Run `/auth` to open the login page.
2.  Complete the login in your browser.
3.  Run `!gemini-switch save "My Alias"` (optional alias) to store these credentials.

### 4. Run As (Exec)
Run a command as another user *without* permanently switching your session. Perfect for quick checks!

```bash
gemini-switch exec "Work" -- gemini prompt "Hello World"
```

### 5. Backup & Restore
Move your accounts to a new machine easily.

```bash
# Export all accounts to a zip file
gemini-switch export my_accounts.zip

# Import from a zip file
gemini-switch import my_accounts.zip
```

---

## 📖 Command Reference

| Command | Action |
| :--- | :--- |
| `gemini-switch` | **Launch Interactive Menu.** |
| `gemini-switch list` | View all saved accounts, aliases & usage history. |
| `gemini-switch save [alias]` | Save current login, optionally with a friendly name. |
| `gemini-switch next` | **Smart Switch:** Rotates to the "freshest" account. |
| `gemini-switch use 1` | Switch to a specific account by its number in the list. |
| `gemini-switch exec 1 -- cmd` | Run a command as a specific user (one-off). |
| `gemini-switch rename 1 Name` | Change the alias of an account. |
| `gemini-switch export file` | Backup all accounts to a zip file. |
| `gemini-switch import file` | Restore accounts from a zip file. |

---

## 🔒 Security & Privacy
*   **100% Local:** Your credentials stay on your machine in `~/.gemini/saved_creds/`.
*   **Transparent:** The tool only moves JSON files; it never sends data to any server.
*   **Reliable:** It checks if your current session is saved before letting you switch.

---

## 🔄 Uninstall & Update

**To Update:**
```bash
cd Gemini-Account-Switcher
git pull
pip install .
```

**To Uninstall:**
```bash
pip uninstall gemini-account-switcher
```

---

<a href="https://www.buymeacoffee.com/minermartijn" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup
1.  Clone the repository.
2.  Install dependencies: `pip install -e .`
3.  Install development tools: `pip install pytest pre-commit`
4.  Setup pre-commit hooks: `pre-commit install`
5.  Run tests: `pytest`

---
*Disclaimer: This is an unofficial tool and is not affiliated with Google.*