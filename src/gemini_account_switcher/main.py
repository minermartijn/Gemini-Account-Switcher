import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from typing import Optional
import datetime
from . import utils

app = typer.Typer(
    name="gemini-switch",
    help="Manage and switch between multiple Gemini CLI accounts.",
    add_completion=True,
)
console = Console()

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

if __name__ == "__main__":
    app()
