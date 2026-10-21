"""CLI entry point — `todaytech` command with init, scan, and run subcommands.

Usage:
    todaytech init       Interactive onboarding → writes profile.yaml
    todaytech scan       Run a scan and print the digest
    todaytech run        Start the Telegram bot (same as python -m todaytech)
    todaytech digest     Show the latest digest from cache
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console(force_terminal=True, legacy_windows=False)


@click.group()
@click.version_option(version="0.1.0", prog_name="TodayTech")
def cli() -> None:
    """TodayTech — Personal opportunity-radar agent."""
    pass


# ---------------------------------------------------------------------------
# todaytech init
# ---------------------------------------------------------------------------


@cli.command()
def init() -> None:
    """Interactive onboarding — build your profile.yaml."""
    console.print("\n🚀 [bold cyan]TodayTech Setup Wizard[/bold cyan]\n")
    console.print("I'll ask a few questions to build your profile.\n")
    console.print("You can always edit [bold]profile.yaml[/bold] by hand later.\n")

    profile: dict = {}

    # Personal
    console.print("[bold]── Personal ──[/bold]")
    profile["name"] = Prompt.ask("Your full name")
    profile["country"] = Prompt.ask("Country of residence")
    citizenship = Prompt.ask("Citizenship(s), comma-separated", default=profile["country"])
    profile["citizenship"] = [c.strip() for c in citizenship.split(",")]
    profile["city"] = Prompt.ask("City")

    # Education
    console.print("\n[bold]── Education ──[/bold]")
    profile["university"] = Prompt.ask("University/Institution")
    profile["level"] = Prompt.ask(
        "Level",
        choices=["undergraduate", "masters", "phd", "bootcamp", "self-taught", "graduated"],
        default="undergraduate",
    )
    profile["year"] = int(Prompt.ask("Year of study (or years since graduation)", default="1"))
    profile["field_of_study"] = Prompt.ask("Field of study", default="Computer Science")

    # Skills
    console.print("\n[bold]── Skills & Interests ──[/bold]")
    skills = Prompt.ask("Skills (comma-separated)", default="Python, JavaScript")
    profile["skills"] = [s.strip() for s in skills.split(",")]
    interests = Prompt.ask("Interests (comma-separated)", default="Open Source, AI")
    profile["interests"] = [i.strip() for i in interests.split(",")]
    causes = Prompt.ask("Causes you care about (comma-separated, or skip)", default="")
    profile["causes"] = [c.strip() for c in causes.split(",") if c.strip()]

    # Languages
    console.print("\n[bold]── Languages ──[/bold]")
    languages = []
    while True:
        lang = Prompt.ask("Language (or 'done' to finish)", default="done")
        if lang.lower() == "done":
            break
        level = Prompt.ask(
            f"  {lang} level",
            choices=["native", "fluent", "intermediate", "basic"],
            default="fluent",
        )
        languages.append({"language": lang, "level": level})
    if not languages:
        languages.append({"language": "English", "level": "fluent"})
    profile["languages"] = languages

    # Preferences
    console.print("\n[bold]── Preferences ──[/bold]")
    types_input = Prompt.ask(
        "Opportunity types (comma-separated)",
        default="hackathon, scholarship, internship, fellowship, grant, program, competition",
    )
    profile["opportunity_types"] = [t.strip() for t in types_input.split(",")]

    regions = Prompt.ask("Regions you can travel to (comma-separated)", default="Global")
    profile["regions"] = [r.strip() for r in regions.split(",")]

    profile["max_application_fee"] = float(
        Prompt.ask("Max application fee (USD, 0 = free only)", default="0")
    )

    # Notification
    console.print("\n[bold]── Notifications ──[/bold]")
    profile["digest_time"] = Prompt.ask("Daily digest time (HH:MM, 24h)", default="08:00")
    profile["timezone"] = Prompt.ask("Your timezone (IANA format)", default="UTC")

    # Scoring
    profile["scoring_weights"] = {
        "eligibility": 40,
        "relevance": 25,
        "benefit": 20,
        "effort": 15,
    }

    # Source packs
    console.print("\n[bold]── Source Packs ──[/bold]")
    packs_dir = Path("sources/packs")
    available_packs = []
    if packs_dir.exists():
        available_packs = [f.stem for f in packs_dir.glob("*.yaml")]
    if available_packs:
        console.print(f"Available packs: {', '.join(available_packs)}")
        packs_input = Prompt.ask("Enable packs (comma-separated, or skip)", default="")
        profile["source_packs"] = [p.strip() for p in packs_input.split(",") if p.strip()]
    else:
        profile["source_packs"] = []

    # Writing samples
    profile["writing_samples"] = []
    profile["cv_path"] = ""

    # Write profile
    profile_path = Path("profile.yaml")
    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    console.print(f"\n✅ [bold green]Profile saved to {profile_path}[/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Edit [bold]profile.yaml[/bold] to fine-tune")
    console.print("  2. Fill in [bold].env[/bold] with your API keys")
    console.print("  3. Run [bold]todaytech run[/bold] or [bold]docker compose up[/bold]")
    console.print("  4. Send [bold]update me[/bold] to your Telegram bot\n")


# ---------------------------------------------------------------------------
# todaytech scan
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--force", is_flag=True, help="Force a fresh scan even if cached")
def scan(force: bool) -> None:
    """Run a scan and print the digest to stdout."""
    console.print("🔍 [bold]Running scan...[/bold]\n")

    async def _run():
        from todaytech.core.config import get_settings
        from todaytech.core.logging import setup_logging
        from todaytech.core.database import init_db, get_session, get_opportunities
        from todaytech.core.pipeline import run_scan
        from todaytech.core.digest import format_digest

        settings = get_settings()
        setup_logging(settings.log_level)
        await init_db(settings.database_url)

        result = await run_scan(force=force)
        if "error" in result:
            console.print(f"[red]❌ {result['error']}[/red]")
            return

        async with get_session() as session:
            opportunities = await get_opportunities(session, limit=50)

        digest = format_digest(
            opportunities,
            unhealthy_sources=result.get("unhealthy_sources", []),
        )
        console.print(digest)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# todaytech run
# ---------------------------------------------------------------------------


@cli.command()
def run() -> None:
    """Start the Telegram bot (main application)."""
    from todaytech.__main__ import main
    main()


# ---------------------------------------------------------------------------
# todaytech digest
# ---------------------------------------------------------------------------


@cli.command()
def digest() -> None:
    """Show the latest digest from the database."""

    async def _run():
        from todaytech.core.config import get_settings
        from todaytech.core.logging import setup_logging
        from todaytech.core.database import init_db, get_session, get_opportunities
        from todaytech.core.digest import format_digest

        settings = get_settings()
        setup_logging(settings.log_level)
        await init_db(settings.database_url)

        async with get_session() as session:
            opportunities = await get_opportunities(session, limit=50)

        if not opportunities:
            console.print("📭 No opportunities in database. Run [bold]todaytech scan[/bold] first.")
            return

        digest_text = format_digest(opportunities)
        console.print(digest_text)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# todaytech web
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host address to bind to")
@click.option("--port", default=8000, help="Port to listen on")
def web(host: str, port: int) -> None:
    """Start the TodayTech Web Dashboard."""
    import uvicorn
    console.print(f"\n🚀 [bold green]Starting TodayTech Web Dashboard[/bold green] at http://{host}:{port}\n")
    uvicorn.run("todaytech.web.app:create_app", host=host, port=port, factory=True, reload=False)


if __name__ == "__main__":
    cli()

