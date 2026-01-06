# Uninstalling and Updating Instructions Needed

## Issue
The README.md does not mention how to uninstall or update the tool. This can be confusing for users who want to remove or upgrade the CLI.

## Recommendation
- Add a section to the README.md with instructions for uninstalling and updating.
- For uninstalling: `pip uninstall gemini-account-switcher`
- For updating: `git pull` in the repo directory, then `pip install .` again.

## Example
```
# Uninstall
pip uninstall gemini-account-switcher

# Update
cd Gemini-Account-Switcher
git pull
pip install .
```

## Benefits
- Improves user experience and clarity.
- Reduces support requests for basic maintenance tasks.