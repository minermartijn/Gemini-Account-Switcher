import typer
import subprocess
import questionary
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from typing import Optional, List
import datetime
from . import utils

__version__ = "1.1.0"

app = typer.Typer(
    name="gemini-switch",
    help="Manage and switch between multiple Gemini CLI accounts.",
    add_completion=True,
)
console = Console()

def interactive_menu():
    """Launch the interactive TUI menu."""
    while True:
        accounts = utils.list_saved_accounts_sorted()
        
        # Build choices
        choices = []
        
        # Current account
        current_creds = utils.get_current_credentials()
        current_email = None
        if current_creds and "id_token" in current_creds:
            current_email = utils.get_email_from_token(current_creds["id_token"])
        
        for email, meta in accounts:
            alias = meta.get("alias", "")
            display = f"{email}"
            if alias:
                display += f" ({alias})"
            if email == current_email:
                display += " [Active]"
            choices.append(questionary.Choice(display, value=email))
            
        choices.append(questionary.Separator())
        choices.append(questionary.Choice("➕ Save Current Account", value="save"))
        choices.append(questionary.Choice("🚀 Run As (Exec)", value="exec"))
        choices.append(questionary.Choice("❌ Exit", value="exit"))

        answer = questionary.select(
            "Select an account to switch to:",
            choices=choices,
            use_indicator=True,
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
                ('question', 'bold'),               # question text
                ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
                ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
                ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
                ('selected', 'fg:#cc5454'),         # style for a selected choice of a checkbox
                ('separator', 'fg:#cc5454'),        # separator in lists
                ('instruction', ''),                # user instructions for select, rawselect, checkbox
                ('text', ''),                       # plain text
                ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
            ])
        ).ask()

        if not answer or answer == "exit":
            break
            
        if answer == "save":
            # Prompt for alias
            alias = questionary.text("Enter an alias (optional):").ask()
            # Call save logic manually
            # We can't easily call the CLI command wrapper, so we call util directly
            creds = utils.get_current_credentials()
            if creds and "id_token" in creds:
                email = utils.get_email_from_token(creds["id_token"])
                if email:
                    utils.save_credentials(email, creds, alias=alias)
                    console.print(f"[green]Saved {email}[/green]")
                else:
                    console.print("[red]Error: Could not extract email[/red]")
            else:
                console.print("[red]No active credentials to save[/red]")
            input("Press Enter to continue...")
            continue
            
        if answer == "exec":
            console.print("[yellow]Use the CLI command for this: gemini-switch exec <account> -- <command>[/yellow]")
            input("Press Enter to continue...")
            continue

        # Switch to account
        target_creds = utils.load_saved_credentials(answer)
        if target_creds:
            utils.activate_credentials(target_creds)
            console.print(f"[green]Switched to {answer}[/green]")
            # We exit after switching? Or stay? Usually users want to switch and work.
            break

def version_callback(value: bool):
    if value:
        console.print(f"Gemini Account Switcher [bold cyan]v{__version__}[/bold cyan]")
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show the application version and exit.", callback=version_callback, is_eager=True
    )
):
    """
    Manage and switch between multiple Gemini CLI accounts.
    """
    # If no command is invoked, run the interactive menu
    if ctx.invoked_subcommand is None:
        interactive_menu()

@app.command()
def list():
    """
    List all saved accounts sorted by last usage.
    """
    accounts = utils.list_saved_accounts_sorted()
    
    # Identify current active account
    current_creds = utils.get_current_credentials()
    current_email = None
    if current_creds and "id_token" in current_creds:
        current_email = utils.get_email_from_token(current_creds["id_token"])

    if not accounts:
        console.print("[yellow]No saved accounts found.[/yellow]")
        console.print("Use [bold]gemini-switch save[/bold] to save your current login.")
        return

    table = Table(title="Saved Gemini Accounts (Sorted by Last Used)")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center", style="green", no_wrap=True)
    table.add_column("Alias", style="blue")
    table.add_column("Email", style="magenta")
    table.add_column("Last Used", style="dim")

    for idx, (email, meta) in enumerate(accounts, start=1):
        status = "✅ Active" if email == current_email else ""
        alias = meta.get("alias", "")
        last_used_ts = meta.get("last_used", 0.0)
        
        last_used_str = "Never"
        if last_used_ts > 0:
            dt = datetime.datetime.fromtimestamp(last_used_ts)
            last_used_str = dt.strftime("%Y-%m-%d %H:%M")

        table.add_row(str(idx), status, alias, email, last_used_str)

    console.print(table)

@app.command()
def save(alias: Optional[str] = typer.Argument(None, help="Optional alias for the account (e.g., 'Work', 'Personal')")):
    """
    Save the currently logged-in account.
    """
    creds = utils.get_current_credentials()
    if not creds:
        console.print("[red]No active Gemini credentials found.[/red]")
        console.print("Please login with the Gemini CLI first: [bold]gemini login[/bold]")
        raise typer.Exit(code=1)

    if "id_token" not in creds:
        console.print("[red]Invalid credentials format: missing id_token.[/red]")
        raise typer.Exit(code=1)

    email = utils.get_email_from_token(creds["id_token"])
    if not email:
        console.print("[red]Could not extract email from identity token.[/red]")
        raise typer.Exit(code=1)

    utils.save_credentials(email, creds, alias=alias)
    
    msg = f"[green]Successfully saved credentials for[/green] [bold]{email}[/bold]"
    if alias:
        msg += f" as alias '[bold blue]{alias}[/bold blue]'"
    console.print(msg)

@app.command()
def use(identifier: str = typer.Argument(..., help="Email address OR the number from the list")):
    """
    Switch to a different account using email or list number.
    """
    email_to_use = identifier
    accounts = utils.list_saved_accounts_sorted()

    # Check if identifier is a number
    if identifier.isdigit():
        idx = int(identifier)
        if 1 <= idx <= len(accounts):
            email_to_use = accounts[idx - 1][0] # Get email from tuple
        else:
            console.print(f"[red]Invalid number:[/red] {idx}. Must be between 1 and {len(accounts)}.")
            raise typer.Exit(code=1)

    # 1. Check if target exists
    target_creds = utils.load_saved_credentials(email_to_use)
    if not target_creds:
        console.print(f"[red]No saved account found for:[/red] {email_to_use}")
        console.print("Use [bold]gemini-switch list[/bold] to see available accounts.")
        raise typer.Exit(code=1)

    # 2. Check current account state
    current_creds = utils.get_current_credentials()
    if current_creds:
        current_email = utils.get_email_from_token(current_creds.get("id_token", ""))
        
        # If current is same as target, do nothing
        if current_email == email_to_use:
            console.print(f"[yellow]Already logged in as {email_to_use}[/yellow]")
            return

        # If current account is NOT saved, warn user
        if current_email:
            saved_current = utils.load_saved_credentials(current_email)
            if not saved_current:
                console.print(f"[bold red]Warning:[/bold red] You are currently logged in as [bold]{current_email}[/bold], but this account is NOT saved.")
                if Confirm.ask("Do you want to save it before switching?"):
                    utils.save_credentials(current_email, current_creds)
                    console.print(f"[green]Saved {current_email}[/green]")
    
    # 3. Perform switch
    utils.activate_credentials(target_creds)
    console.print(f"[green]Successfully switched to:[/green] [bold]{email_to_use}[/bold]")

@app.command()
def next():
    """
    Smart switch to the account used longest ago (Least Recently Used).
    """
    accounts = utils.list_saved_accounts_sorted()
    if not accounts:
        console.print("[red]No saved accounts found.[/red]")
        return

    # Get current email
    current_creds = utils.get_current_credentials()
    current_email = None
    if current_creds:
        current_email = utils.get_email_from_token(current_creds.get("id_token", ""))

    # Logic: Pick the first account in the sorted list that is NOT the current one.
    target_email = None
    for email, _ in accounts:
        if email != current_email:
            target_email = email
            break
    
    if not target_email:
        console.print("[yellow]No other accounts available to switch to.[/yellow]")
        return

    console.print(f"🔄 Rotating to: [bold]{target_email}[/bold]")
    
    target_creds = utils.load_saved_credentials(target_email)
    if target_creds:
        utils.activate_credentials(target_creds)
        console.print(f"[green]Successfully rotated to:[/green] [bold]{target_email}[/bold]")
    else:
        console.print(f"[red]Error loading credentials for {target_email}[/red]")

@app.command()
def rename(identifier: str = typer.Argument(..., help="Email or number of account"), 
           new_alias: str = typer.Argument(..., help="New alias name")):
    """
    Rename the alias for an existing account.
    """
    email_to_rename = identifier
    accounts = utils.list_saved_accounts_sorted()

    # Resolve number to email
    if identifier.isdigit():
        idx = int(identifier)
        if 1 <= idx <= len(accounts):
            email_to_rename = accounts[idx - 1][0]
        else:
            console.print(f"[red]Invalid number:[/red] {idx}")
            raise typer.Exit(code=1)
            
    if utils.rename_alias(email_to_rename, new_alias):
         console.print(f"[green]Updated alias for {email_to_rename} to:[/green] [bold blue]{new_alias}[/bold blue]")
    else:
         console.print(f"[red]Account not found:[/red] {email_to_rename}")

@app.command()
def whoami():
    """
    Show current active account details.
    """
    creds = utils.get_current_credentials()
    if not creds or "id_token" not in creds:
        console.print("[red]Not logged in.[/red]")
        return

    email = utils.get_email_from_token(creds["id_token"])
    meta = utils.get_account_meta(email)
    alias = meta.get("alias", "None")
    
    console.print(f"Email: [bold magenta]{email}[/bold magenta]")
    console.print(f"Alias: [bold blue]{alias}[/bold blue]")

@app.command()
def remove(identifier: str = typer.Argument(..., help="Email or number of account")):
    """
    Remove a saved account.
    """
    email_to_remove = identifier
    accounts = utils.list_saved_accounts_sorted()

    if identifier.isdigit():
        idx = int(identifier)
        if 1 <= idx <= len(accounts):
            email_to_remove = accounts[idx - 1][0]
        else:
             console.print(f"[red]Invalid number:[/red] {idx}")
             raise typer.Exit(code=1)

    if utils.delete_saved_account(email_to_remove):
        console.print(f"[green]Removed account:[/green] {email_to_remove}")
    else:
        console.print(f"[red]Account not found:[/red] {email_to_remove}")

@app.command("exec")
def exec_command(
    identifier: str = typer.Argument(..., help="Email or number of account to run as"),
    cmd: List[str] = typer.Argument(..., help="The command to run")
):
    """
    Run a command as a specific user without permanently switching.
    Example: gemini-switch exec Work -- gemini prompt "Hello"
    """
    email_to_use = identifier
    accounts = utils.list_saved_accounts_sorted()

    if identifier.isdigit():
        idx = int(identifier)
        if 1 <= idx <= len(accounts):
            email_to_use = accounts[idx - 1][0]
        else:
            console.print(f"[red]Invalid number:[/red] {idx}")
            raise typer.Exit(code=1)

    try:
        with utils.temporary_switch(email_to_use):
            console.print(f"[dim]Running as {email_to_use}...[/dim]")
            subprocess.run(cmd)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Error running command: {e}[/red]")

@app.command()
def export(output: Path = typer.Argument(..., help="Path to save the zip file")):
    """
    Export all saved accounts to a zip file.
    """
    try:
        zip_path = utils.create_backup(output)
        console.print(f"[green]Successfully exported accounts to:[/green] {zip_path}")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")

@app.command("import")
def import_backup(input_file: Path = typer.Argument(..., help="Path to the zip file to import")):
    """
    Import accounts from a zip file.
    """
    try:
        utils.restore_backup(input_file)
        console.print(f"[green]Successfully imported accounts from:[/green] {input_file}")
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")

if __name__ == "__main__":
    app()