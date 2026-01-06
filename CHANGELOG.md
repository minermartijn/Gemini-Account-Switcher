# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-06

### Added
- **Initial Release** of Gemini Account Switcher.
- **Save**: Ability to save current Gemini CLI credentials (`gemini-switch save`).
- **List**: Display saved accounts with status, aliases, and last usage time (`gemini-switch list`).
- **Switch**: Switch active accounts using email or list number (`gemini-switch use`).
- **Smart Rotation**: Automatically switch to the least recently used account (`gemini-switch next`).
- **Aliases**: Support for custom aliases for accounts (`gemini-switch rename`).
- **Whoami**: Command to show current active account (`gemini-switch whoami`).
- **Metadata**: Tracks "Last Used" timestamps for smarter rotation.
