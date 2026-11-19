"""
Multi-Agent Job Hunter -- CLI Entry Point

Commands:
  python main.py run          Full pipeline (resume > match > save matches > dashboard)
  python main.py analyze      Resume analysis only
  python main.py search       Job search & matching (real job board scraping)
  python main.py outreach     Execute outreach only (requires prior search)
  python main.py track        Show matched jobs dashboard (alias for dashboard)
  python main.py dashboard    Show matched jobs dashboard
"""
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
# The embedding model load report and the hub download notice are informational
# and would otherwise dominate the CLI output. These have to be set before the
# model libraries are imported (they configure themselves on import).
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")


def _force_utf8_output() -> None:
    """Make the console able to render the box-drawing characters used in logs."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - platform dependent
            pass


_force_utf8_output()

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
    # The embedding model load report and the hub download notice are noise
    # for a CLI run and can be very long.
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

    # JobSpy installs its own stderr handler and reports blocked job boards at
    # ERROR level. The search layer reports those conditions itself, so the
    # third-party stream is muted to keep the pipeline output readable.
    for name in list(logging.root.manager.loggerDict):
        if name.startswith("JobSpy"):
            jobspy_logger = logging.getLogger(name)
            jobspy_logger.setLevel(logging.CRITICAL)
            for handler in list(jobspy_logger.handlers):
                jobspy_logger.removeHandler(handler)
            jobspy_logger.propagate = False


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose):
    """Multi-Agent Job Hunter -- Autonomous job search & outreach system."""
    setup_logging(verbose)


@cli.command()
@click.argument("resume_path", type=click.Path(exists=True))
@click.option("--roles", "-r", multiple=True, help="Target job titles")
@click.option("--locations", "-l", multiple=True, help="Target locations")
@click.option("--boards", "-b", multiple=True, help="Job sources to use (default: ENABLED_SOURCES)")
def run(resume_path, roles, locations, boards):
    """Run the pipeline and export results to data/job_hunt_results.xlsx."""
    from config.constants import DEFAULT_BOARDS
    from config.settings import get_settings
    from graph.orchestrator import run_pipeline

    try:
        configured = [
            item.strip()
            for item in (get_settings().enabled_sources or "").split(",")
            if item.strip()
        ]
    except Exception:
        configured = []

    selected_boards = list(boards) or configured or list(DEFAULT_BOARDS)

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
@click.option("--resume-path", "-r", required=True, type=click.Path(exists=True), help="Path to resume PDF")
@click.option("--roles", "-R", multiple=True, required=True, help="Target job roles to search for")
@click.option("--locations", "-L", multiple=True, default=["Remote"], help="Target locations")
@click.option("--boards", "-b", multiple=True, default=[], help="Job boards to search (default: ENABLED_SOURCES)")
@click.option("--threshold", "-t", type=float, default=None, help="Override match threshold (default: MATCH_THRESHOLD)")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def search(resume_path, roles, locations, boards, threshold, verbose):
    """Search & match jobs against real job boards (Agent 2).

    Scrapes configured job boards, computes match scores (semantic, TF-IDF, skill overlap,
    LLM verification), and displays ranked results with composite scores.
    """
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    from agents.job_match_agent import search_and_match_jobs
    from agents.resume_agent import analyze_resume
    from config.constants import DEFAULT_BOARDS
    from config.settings import get_settings

    settings = get_settings()

    # Determine boards to use
    selected_boards = list(boards)
    if not selected_boards:
        try:
            configured = [
                item.strip()
                for item in (settings.enabled_sources or "").split(",")
                if item.strip()
            ]
            selected_boards = configured or list(DEFAULT_BOARDS)
        except Exception:
            selected_boards = list(DEFAULT_BOARDS)

    # Determine threshold
    match_threshold = threshold if threshold is not None else settings.match_threshold

    # Analyze resume
    try:
        result = analyze_resume(str(Path(resume_path).resolve()), settings)
    except FileNotFoundError:
        console.print(f"[red]Error: Resume file not found: {resume_path}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: Invalid PDF file: {resume_path} ({e})[/red]")
        raise SystemExit(1)

    resume_text = result["resume_text"]
    candidate_profile = result["candidate_profile"]

    # Search and match
    try:
        match_result = search_and_match_jobs(
            candidate_profile=candidate_profile,
            resume_text=resume_text,
            settings=settings,
            target_locations=list(locations),
            target_roles=list(roles),
            boards=selected_boards,
        )
    except Exception as e:
        console.print(f"[red]Error: No LLM provider available or all job sources failed ({e})[/red]")
        raise SystemExit(3)

    matched_jobs = match_result.get("matched_jobs", [])

    # Filter by threshold (search_and_match_jobs already applies threshold, but allow override)
    if threshold is not None:
        matched_jobs = [
            job for job in matched_jobs
            if job.get("match_scores", {}).get("composite_score", 0) >= threshold
        ]

    # Display results
    if matched_jobs:
        console.print(f"\nFound {len(matched_jobs)} matched jobs for \"{', '.join(roles)}\" (threshold: {match_threshold:.0%})\n")
        console.print(render_matched_jobs_table(matched_jobs, verbose=verbose))
        console.print("\nRun 'main.py run' to save matches and generate dashboard.")
    else:
        console.print(f"\nNo jobs matched above threshold {match_threshold:.0%} for \"{', '.join(roles)}\".")
        console.print("Try adjusting --roles, --locations, or --threshold.")
        raise SystemExit(0)


@cli.command()
def track():
    """Show matched jobs dashboard (alias for dashboard)."""
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
    """Show matched jobs dashboard."""
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

def render_matched_jobs_table(matched_jobs: list[dict], verbose: bool = False) -> Table:
    """Render a consistently formatted table of matched jobs.
    
    Used by search, run, and dashboard commands for terminology consistency (FR-008).
    """
    # Determine if jobs have interpretation field (new calibrated output)
    has_interpretation = any("score_interpretation" in job for job in matched_jobs)

    table = Table(title=f"Matched Jobs ({len(matched_jobs)} above threshold)")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", width=30)
    table.add_column("Company", style="green", width=20)
    table.add_column("Source", width=18)
    table.add_column("Score", style="bold yellow", width=8)
    if has_interpretation:
        table.add_column("Int", width=12)
    table.add_column("Location", width=15)
    table.add_column("Job Link", style="blue", overflow="fold")

    for i, job in enumerate(matched_jobs):
        score = job.get("match_scores", {}).get("composite_score", 0)
        interpretation = job.get("score_interpretation", "")

        # Emoji and text for interpretation
        if interpretation == "strong":
            int_display = "🟢 Strong"
        elif interpretation == "moderate":
            int_display = "🟡 Moderate"
        elif interpretation == "weak":
            int_display = "🔴 Weak"
        else:
            int_display = ""

        row = [
            str(i + 1),
            job.get("title", "N/A")[:30],
            job.get("company", "N/A")[:20],
            job.get("source_board", "N/A")[:18],
            f"{score:.1%}",
        ]
        if has_interpretation:
            row.append(int_display)
        row.extend([
            job.get("location", "N/A")[:15],
            job.get("source_url", ""),
        ])
        table.add_row(*row)

    # If verbose, print detailed breakdown for each job
    if verbose and has_interpretation:
        for i, job in enumerate(matched_jobs):
            console.print(f"\n[bold]Score breakdown for #{i + 1}:[/bold]")
            _print_score_breakdown(job)

    return table


def _print_score_breakdown(job: dict) -> None:
    """Print detailed score breakdown for a matched job in verbose mode."""
    match_scores = job.get("match_scores", {})
    score_breakdown = job.get("score_breakdown")
    weight_config = job.get("weight_config_used")

    if not score_breakdown:
        console.print("  [dim]No detailed breakdown available[/dim]")
        return

    interpretation = job.get("score_interpretation", "moderate")
    if interpretation == "strong":
        int_text = "🟢 Strong match — likely to pass initial screening"
    elif interpretation == "moderate":
        int_text = "🟡 Moderate match — manual review recommended"
    else:
        int_text = "🔴 Weak match — significant gaps"

    console.print(f"  [bold]Interpretation:[/bold] {int_text}")
    console.print(f"  [bold]Composite Score:[/bold] {match_scores.get('composite_score', 0):.1%}")

    # Stage 1 breakdown
    if score_breakdown.get("stage1_components"):
        console.print("  [bold]Stage 1 (Pre-filter composite):[/bold]")
        for name, comp in score_breakdown["stage1_components"].items():
            name_fmt = name.replace("_", " ").title()
            console.print(f"    {name_fmt} ({comp['weight']:.2f}): {comp['raw_score']:.2f} → {comp['weighted_contribution']:.3f}")
        console.print(f"    [dim]Stage 1 Score: {score_breakdown['stage1_formula']}[/dim]")

    # Stage 2 breakdown
    if score_breakdown.get("stage2_components"):
        console.print("  [bold]Stage 2 (Final composite):[/bold]")
        for name, comp in score_breakdown["stage2_components"].items():
            name_fmt = name.replace("_", " ").title()
            console.print(f"    {name_fmt} ({comp['weight']:.2f}): {comp['raw_score']:.2f} → {comp['weighted_contribution']:.3f}")
        console.print(f"    [dim]Composite: {score_breakdown['stage2_formula']}[/dim]")

    # Interpretation bands
    bands = score_breakdown.get("interpretation_band", {})
    if bands:
        console.print(f"  [bold]Bands:[/bold] Strong ≥ {bands.get('strong_min', 0.7):.0%}, Moderate ≥ {bands.get('moderate_min', 0.5):.0%}")


def render_outreach_summary(summary: dict) -> Panel:
    """Render a consistently formatted outreach summary panel.
    
    Ensures honest counts when no external outreach occurs (FR-006).
    """
    return Panel.fit(
        f"Attempted: {summary.get('total_attempted', 0)}\n"
        f"[green]Sent: {summary.get('successfully_sent', 0)}[/green]\n"
        f"Skipped: {summary.get('skipped', 0)}\n"
        f"[red]Failed: {summary.get('failed', 0)}[/red]",
        title="[bold]Outreach Summary[/bold]",
    )


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

    # Matched Jobs - use shared helper for consistent terminology (FR-008)
    if matched:
        console.print(render_matched_jobs_table(matched))
        console.print("\n[bold]Job links[/bold]")
        for i, job in enumerate(matched, start=1):
            title = job.get("title") or "Untitled job"
            company = job.get("company") or "Unknown company"
            source = job.get("source_board") or "unknown source"
            url = job.get("source_url") or ""
            console.print(Text(f"{i}. {title} — {company} ({source})"))
            if url:
                console.print(Text(f"   Open job / apply page: {url}"))
            else:
                console.print(Text("   No job link was provided; search this title and company on the source board."))
    else:
        console.print("[yellow]No jobs matched above the threshold.[/yellow]")

    # Outreach Summary - use shared helper for honest counts (FR-006)
    if outreach:
        console.print(render_outreach_summary(outreach))

    # Dashboard
    if dashboard:
        _display_dashboard(dashboard)

    from tools.excel_export import export_pipeline_results

    try:
        workbook_path = export_pipeline_results(state)
    except OSError as exc:
        raise click.ClickException(
            f"Could not save Excel results. Close the workbook if it is open and retry. {exc}"
        ) from exc
    console.print(f"\n[green]Excel results saved to:[/green] {workbook_path}")


def _display_dashboard(dashboard_data):
    """Display matched jobs dashboard (FR-007)."""
    if not dashboard_data:
        console.print("[dim]No tracking data available.[/dim]")
        return

    breakdown = dashboard_data.get("status_breakdown", {})
    if breakdown:
        table = Table(title="Matched Jobs Dashboard")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="bold", justify="right")
        for status, count in breakdown.items():
            table.add_row(status.replace("_", " ").title(), str(count))
        total = sum(breakdown.values())
        table.add_row("─" * 20, "─" * 5, style="dim")
        table.add_row("Total matched jobs saved", str(total), style="bold")
        console.print(table)


def _display_db_dashboard(db):
    """Display matched jobs dashboard from database (FR-007)."""
    breakdown = db.get_status_breakdown()
    recent = db.get_recent_activity(limit=10)

    if breakdown:
        table = Table(title="Matched Jobs Dashboard")
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
        table.add_column("Action", style="dim")
        for r in recent:
            table.add_row(
                r["company"][:20], r["title"][:25],
                r["status"], r.get("last_action", "saved to database")[:30],
            )
        console.print(table)


if __name__ == "__main__":
    cli()
