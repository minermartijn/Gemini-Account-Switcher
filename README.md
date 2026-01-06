
![Banner](images/banner.png)

# Gemini Account Switcher

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A professional, secure, and elegant CLI tool to manage multiple Gemini accounts. Designed specifically for users of the Gemini interactive CLI.

---

## 🚀 Pro Tip: Using inside the Gemini CLI
If you are already inside the **Gemini interactive shell**, you don't need to exit! Just use the `!` prefix to run switcher commands:

*   `!gemini-switch list` - See your accounts.
*   `!gemini-switch next` - Switch to the next available account.

---

## 🛠 Setup & Usage

### 1. Installation
```bash
git clone https://github.com/minermartijn/Gemini-Account-Switcher.git
cd Gemini-Account-Switcher
pip install .
```

### 2. Adding your first account
Inside the Gemini CLI, authenticate your first account:
1.  Run `/auth` to open the login page.
2.  Complete the login in your browser.
3.  Run `!gemini-switch save` to store these credentials.

### 3. Adding more accounts
Repeat the process for each Google account:
1.  Run `/auth` again.
2.  Log in with a **different** Google account.
3.  Run `!gemini-switch save`.

### 4. Smart Rotation (Instant Switch)
When you hit a quota limit or want to change identity, just run:
```bash
!gemini-switch next
```
The tool will automatically pick the account you haven't used in the longest time.

---

## 📖 Command Reference

| Command | Action |
| :--- | :--- |
| `gemini-switch list` | View all saved accounts & their usage history. |
| `gemini-switch save` | Save your current active login session. |
| `gemini-switch next` | **Smart Switch:** Rotates to the "freshest" account. |
| `gemini-switch use 1` | Switch to a specific account by its number in the list. |
| `gemini-switch use email@gmail.com` | Switch to an account by its email address. |

---

## 🔒 Security & Privacy
*   **100% Local:** Your credentials stay on your machine in `~/.gemini/saved_creds/`.
*   **Transparent:** The tool only moves JSON files; it never sends data to any server.
*   **Reliable:** It checks if your current session is saved before letting you switch.

---
*Disclaimer: This is an unofficial tool and is not affiliated with Google.*
