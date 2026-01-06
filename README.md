# Gemini Account Switcher

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A secure, simple, and elegant CLI tool to manage and switch between multiple Gemini CLI accounts.  
Inspired by [cc-account-switcher](https://github.com/ming86/cc-account-switcher).

## 🚀 Why use this?

If you work with multiple Google accounts (e.g., Personal, Work, Freelance) and use the **Gemini CLI**, constantly logging in and out is a pain. 

**Gemini Account Switcher** solves this by securely storing your session tokens locally and allowing you to swap them with a single command.

*   **Secure:** Credentials never leave your machine. They are stored in `~/.gemini/saved_creds/`.
*   **Safe:** Checks if your current session is saved before switching, preventing accidental data loss.
*   **Simple:** Easy-to-remember commands: `save`, `list`, `use`.
*   **Beautiful:** Rich terminal output.

## 📦 Installation

You can install this directly from source (recommended for now):

```bash
git clone https://github.com/minermartijn/gemini-account-switcher.git
cd gemini-account-switcher
pip install .
```

*Note: In the future, this will be available via PyPI.*

## 🛠 Usage

### 1. Save your current login
First, login normally with the Gemini CLI. Then, save that session:

```bash
$ gemini-switch save
Successfully saved credentials for your.email@gmail.com
```

### 2. Add another account
Login with the Gemini CLI again (this overwrites the current session, but don't worry, you saved it!):

```bash
$ gemini login
# ... perform login flow ...
$ gemini-switch save
Successfully saved credentials for other.work@company.com
```

### 3. List accounts
See all your saved sessions:

```bash
$ gemini-switch list
Saved Gemini Accounts
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status   ┃ Email                    ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✅ Active │ other.work@company.com   │
│          │ your.email@gmail.com     │
└──────────┴──────────────────────────┘
```

### 4. Switch instantly
Swap back to your personal account:

```bash
$ gemini-switch use your.email@gmail.com
Successfully switched to: your.email@gmail.com
```

## 🔒 Security

This tool operates **entirely locally**. 
- It simply copies the `oauth_creds.json` file found in your `~/.gemini` directory to a subdirectory `~/.gemini/saved_creds/`.
- It reads the `id_token` only to identify the email address associated with the session.
- No data is ever sent to any third-party server.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Disclaimer: This is an unofficial tool and is not affiliated with Google.*
