"""
Multi-Agent Job Hunter -- CLI Entry Point

Commands:
  python main.py run          Full pipeline (resume > match > outreach > track)
  python main.py analyze      Resume analysis only
  python main.py search       Job search & matching only (requires prior analyze)
  python main.py outreach     Execute outreach only (requires prior search)
  python main.py track        Run one follow-up cycle
  python main.py dashboard    Show current application status
"""
import os
import sys
import logging
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler

# Load .env before anything else
load_dotenv()

console = Console()


def setup_logging(verbose: bool = False):
    """Configure structured logging with Rich."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose):
    """Multi-Agent Job Hunter -- Autonomous job search & outreach system."""
    setup_logging(verbose)


@cli.command()
@click.argument("resume_path", type=click.Path(exists=True))
@click.option("--roles", "-r", multiple=True, help="Target job titles")
@click.option("--locations", "-l", multiple=True, help="Target locations")
@click.option("--boards", "-b", multiple=True, help="Job boards/platforms")
def run(resume_path, roles, locations, boards):
    """Run the full pipeline: analyze > search > outreach > track."""
    from graph.orchestrator import run_pipeline
    from config.constants import DEFAULT_BOARDS

    selected_boards = list(boards) or DEFAULT_BOARDS

    console.print(Panel.fit(
        "[bold green]Multi-Agent Job Hunter[/bold green]\n"
        f"Resume: {resume_path}\n"
        f"Roles: {', '.join(roles) if roles else 'Auto-detect'}\n"
        f"Locations: {', '.join(locations) if locations else 'Any'}\n"
        f"Boards: {', '.join(selected_boards)}",
        title="[bold]Pipeline Configuration[/bold]",
    ))

    final_state = run_pipeline(
        resume_path=str(Path(resume_path).resolve()),
        target_roles=list(roles),
        target_locations=list(locations),
        boards=selected_boards,
    )

    _display_results(final_state)


@cli.command()
@click.argument("resume_path", type=click.Path(exists=True))
def analyze(resume_path):
    """Analyze a resume (Agent 1 only)."""
    from agents.resume_agent import analyze_resume
    from config.settings import get_settings

    settings = get_settings()
    result = analyze_resume(str(Path(resume_path).resolve()), settings)

    profile = result["candidate_profile"]
    console.print(Panel.fit(
        f"[bold]{profile.name}[/bold]\n"
        f"Email: {profile.email}\n"
        f"Level: {profile.seniority_level}\n"
        f"Experience: {profile.total_years_experience} years\n"
        f"Skills: {len(profile.skills.all_skills)} detected",
        title="[bold]Resume Analysis Complete[/bold]",
    ))

    # Show skills table
    table = Table(title="Detected Skills")
    table.add_column("Category", style="cyan")
    table.add_column("Skills", style="green")

    for field_name in profile.skills.model_fields:
        skills = getattr(profile.skills, field_name)
        if skills:
            table.add_row(field_name, ", ".join(skills))

    console.print(table)


@cli.command()
def search():
    """Search & match jobs (Agent 2). Requires prior 'analyze' run."""
    from agents.job_match_agent import search_and_match_jobs
    from config.settings import get_settings

    from tools.embedding_tools import query_similar

    settings = get_settings()

    # Check for stored resume data
    results = query_similar([0.0] * 384, n_results=1, persist_dir=settings.chroma_path)
    if not results:
        console.print("[red]No resume found. Run 'analyze' first.[/red]")
        return

    console.print("[yellow]Note: Using stored resume data. Run 'analyze' first if not done.[/yellow]")
    console.print("[yellow]Search will start with default profile. Use 'run' for full pipeline.[/yellow]")


@cli.command()
def track():
    """Run one follow-up cycle (Agent 4)."""
    from config.settings import get_settings
    from models.database import Database

    settings = get_settings()
    db = Database(settings.db_path)

    # Agents removed: synthesize a simple dashboard from the DB.
    dashboard = {
        "status_breakdown": db.get_status_breakdown(),
        "recent_activity": db.get_recent_activity(limit=20),
    }
    _display_dashboard(dashboard)


@cli.command()
def dashboard():
    """Show current application status dashboard."""
    from config.settings import get_settings
    from models.database import Database

    settings = get_settings()
    db_path = Path(settings.db_path)
    if not db_path.exists():
        console.print("[red]No database found. Run the pipeline first.[/red]")
        return

    db = Database(settings.db_path)
    _display_db_dashboard(db)


# ──────────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────────

def _display_results(state: dict):
    """Display the final pipeline results."""
    errors = state.get("errors", [])
    matched = state.get("matched_jobs", [])
    outreach = state.get("outreach_summary", {})
    dashboard = state.get("tracking_dashboard", {})

    # Errors
    if errors:
        console.print(Panel.fit(
            "\n".join(f"[!] {e}" for e in errors),
            title="[yellow]Warnings[/yellow]",
            border_style="yellow",
        ))

    # Matched Jobs
    if matched:
        table = Table(title=f"Matched Jobs ({len(matched)} above threshold)")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="cyan", width=30)
        table.add_column("Company", style="green", width=20)
        table.add_column("Source", width=18)
        table.add_column("Score", style="bold yellow", width=8)
        table.add_column("Location", width=15)
        table.add_column("Apply Link", style="blue", overflow="fold")

        for i, job in enumerate(matched):
            score = job.get("match_scores", {}).get("composite_score", 0)
            table.add_row(
                str(i + 1),
                job.get("title", "N/A")[:30],
                job.get("company", "N/A")[:20],
                job.get("source_board", "N/A")[:18],
                f"{score:.1%}",
                job.get("location", "N/A")[:15],
                job.get("source_url", ""),
            )
        console.print(table)
    else:
        console.print("[yellow]No jobs matched above the threshold.[/yellow]")

    # Outreach Summary
    if outreach:
        console.print(Panel.fit(
            f"Attempted: {outreach.get('total_attempted', 0)}\n"
            f"[green]Sent: {outreach.get('successfully_sent', 0)}[/green]\n"
            f"Skipped: {outreach.get('skipped', 0)}\n"
            f"[red]Failed: {outreach.get('failed', 0)}[/red]",
            title="[bold]Outreach Summary[/bold]",
        ))

    # Dashboard
    if dashboard:
        _display_dashboard(dashboard)


def _display_dashboard(dashboard_data):
    """Display tracking dashboard."""
    if not dashboard_data:
        console.print("[dim]No tracking data available.[/dim]")
        return

    breakdown = dashboard_data.get("status_breakdown", {})
    if breakdown:
        table = Table(title="Application Status Dashboard")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="bold", justify="right")
        for status, count in breakdown.items():
            style = "green" if "positive" in status else "red" if "negative" in status or "cold" in status else ""
            table.add_row(status.replace("_", " ").title(), str(count), style=style)
        total = sum(breakdown.values())
        table.add_row("─" * 20, "─" * 5, style="dim")
        table.add_row("Total", str(total), style="bold")
        console.print(table)


def _display_db_dashboard(db):
    """Display dashboard from database."""
    breakdown = db.get_status_breakdown()
    recent = db.get_recent_activity(limit=10)

    if breakdown:
        table = Table(title="Application Status Dashboard")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="bold", justify="right")
        for status, count in breakdown.items():
            table.add_row(status.replace("_", " ").title(), str(count))
        console.print(table)

    if recent:
        table = Table(title="Recent Activity")
        table.add_column("Company", style="green")
        table.add_column("Title", style="cyan")
        table.add_column("Status")
        table.add_column("Last Activity", style="dim")
        for r in recent:
            table.add_row(
                r["company"][:20], r["title"][:25],
                r["status"], r.get("last_action_at", "")[:16],
            )
        console.print(table)


if __name__ == "__main__":
    cli()
