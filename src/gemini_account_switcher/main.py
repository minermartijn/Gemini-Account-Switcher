import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from typing import Optional
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
    List all saved accounts.
    """
    accounts = utils.list_saved_accounts()
    
    # Identify current active account
    current_creds = utils.get_current_credentials()
    current_email = None
    if current_creds and "id_token" in current_creds:
        current_email = utils.get_email_from_token(current_creds["id_token"])

    if not accounts:
        console.print("[yellow]No saved accounts found.[/yellow]")
        console.print("Use [bold]gemini-switch save[/bold] to save your current login.")
        return

    table = Table(title="Saved Gemini Accounts")
    table.add_column("Status", justify="center", style="cyan", no_wrap=True)
    table.add_column("Email", style="magenta")

    for email in accounts:
        status = "✅ Active" if email == current_email else ""
        table.add_row(status, email)

    console.print(table)

@app.command()
def save(name: Optional[str] = typer.Argument(None, help="Optional alias (defaults to email address)")):
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

    save_name = name if name else email
    
    utils.save_credentials(save_name, creds)
    console.print(f"[green]Successfully saved credentials for[/green] [bold]{email}[/bold]")
    if name:
         console.print(f"Saved as: [bold]{name}[/bold]")

@app.command()
def use(email: str = typer.Argument(..., help="The email address of the account to switch to")):
    """
    Switch to a different account.
    """
    # 1. Check if target exists
    target_creds = utils.load_saved_credentials(email)
    if not target_creds:
        console.print(f"[red]No saved account found for:[/red] {email}")
        console.print("Use [bold]gemini-switch list[/bold] to see available accounts.")
        raise typer.Exit(code=1)

    # 2. Check current account state
    current_creds = utils.get_current_credentials()
    if current_creds:
        current_email = utils.get_email_from_token(current_creds.get("id_token", ""))
        
        # If current is same as target, do nothing
        if current_email == email:
            console.print(f"[yellow]Already logged in as {email}[/yellow]")
            return

        # If current account is NOT saved, warn user
        if current_email:
            saved_current = utils.load_saved_credentials(current_email)
            # Simple check: if file doesn't exist, it's definitely not saved. 
            # (We could compare content, but existence is a good proxy for intent here)
            if not saved_current:
                console.print(f"[bold red]Warning:[/bold red] You are currently logged in as [bold]{current_email}[/bold], but this account is NOT saved.")
                if Confirm.ask("Do you want to save it before switching?"):
                    utils.save_credentials(current_email, current_creds)
                    console.print(f"[green]Saved {current_email}[/green]")
    
    # 3. Perform switch
    utils.activate_credentials(target_creds)
    console.print(f"[green]Successfully switched to:[/green] [bold]{email}[/bold]")

@app.command()
def remove(email: str):
    """
    Remove a saved account.
    """
    if utils.delete_saved_account(email):
        console.print(f"[green]Removed account:[/green] {email}")
    else:
        console.print(f"[red]Account not found:[/red] {email}")

if __name__ == "__main__":
    app()
