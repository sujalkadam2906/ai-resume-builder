"""Command Line Interface for the Multi-Provider ATS Resume Builder with Multi-Profile Support."""

import argparse
from pathlib import Path
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .ai.provider_manager import ProviderManager
from .ats.scorer import calculate_ats_readiness
from .config import DEFAULT_PROFILE_ID, LOGS_DIR, PROJECT_ROOT, config, get_profile_dir
from .content.generator import build_resume_manifest
from .jd_analysis.analyzer import JDAnalyzer
from .profile.manager import ProfileManager
from .project_selection.selector import select_projects_for_jd
from .reports.report_writer import write_complete_application
from .utils.logger import setup_logger

console = Console()


def get_multiline_jd_input() -> str:
    """Prompt user for multiline JD input terminated by 'END JD'."""
    console.print(
        "[bold cyan]Paste the Job Description below. When finished, type 'END JD' on a new line and press Enter:[/bold cyan]"
    )
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END JD":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def run_pipeline(
    jd_text: str,
    profile_id: str = DEFAULT_PROFILE_ID,
    company: Optional[str] = None,
    role: Optional[str] = None,
    provider: Optional[str] = None,
    offline: bool = False,
    dry_run: bool = False,
    check_only: bool = False,
    custom_output: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Execute the end-to-end resume generation and validation pipeline."""
    logger = setup_logger(log_dir=LOGS_DIR, verbose=verbose)

    if not jd_text.strip():
        console.print("[bold red]Error: Job description is empty.[/bold red]")
        return 1

    try:
        # Validate profile directory exists
        try:
            profile_dir = get_profile_dir(profile_id)
        except ValueError as ve:
            console.print(f"[bold red]Profile Error:[/bold red] {ve}")
            return 1

        if not profile_dir.exists() or not (profile_dir / "master_profile.json").exists():
            if profile_id != DEFAULT_PROFILE_ID:
                console.print(
                    f"[bold red]Error: Profile '{profile_id}' does not exist or has not been initialized.[/bold red]\n"
                    f"Use --list-profiles to view available profiles, or --create-profile {profile_id} to initialize."
                )
                return 1

        # [1/7] Reading candidate profile
        console.print(
            f"[bold blue][1/7][/bold blue] Reading candidate profile and projects database (Profile: [bold cyan]{profile_id}[/bold cyan])..."
        )
        pm = ProfileManager(profile_id=profile_id)
        profile = pm.load_profile()
        projects = pm.load_projects()
        profile_config = pm.load_profile_config()
        console.print(f"  [green]✓[/green] Loaded verified profile for [bold]{profile.personal_info.full_name}[/bold]")
        console.print(f"  [green]✓[/green] Loaded {len(projects)} verified projects from database")

        # [2/7] Analysing job description
        console.print("[bold blue][2/7][/bold blue] Analysing job description...")
        analyzer = JDAnalyzer(profile, projects)
        jd = analyzer.analyze(jd_text, user_company=company, user_role=role)
        console.print(f"  [green]✓[/green] Target Company : [bold]{jd.company_name}[/bold]")
        console.print(f"  [green]✓[/green] Target Role    : [bold]{jd.job_title}[/bold]")
        console.print(f"  [green]✓[/green] Identified {len(jd.required_skills)} required technical skills")

        # [3/7] Mapping requirements to evidence
        console.print("[bold blue][3/7][/bold blue] Mapping requirements to candidate evidence...")
        req_matrix = analyzer.evaluate_match(jd)
        console.print(
            f"  [green]✓[/green] Match Coverage: [bold]{req_matrix.match_percentage}%[/bold] "
            f"({req_matrix.strong_match_count} strong, {req_matrix.partial_match_count} partial, "
            f"{req_matrix.missing_count} missing, {req_matrix.unsupported_count} unsupported)"
        )

        if check_only:
            console.print("[bold green]Check-only mode finished successfully. Requirements matrix mapped.[/bold green]")
            return 0

        # [4/7] Selecting projects according to profile configuration
        has_fx = profile_config.project_selection.has_fixed_project
        rule_desc = (
            f"Fixed Rule: {profile_config.project_selection.fixed_project.id} at #{profile_config.project_selection.fixed_project.position}"
            if has_fx and profile_config.project_selection.fixed_project
            else "Pure Dynamic Ranking"
        )
        console.print(f"[bold blue][4/7][/bold blue] Selecting projects ({rule_desc})...")
        selected_projects, scored_pool, shortage = select_projects_for_jd(
            all_projects=projects,
            jd=jd,
            selection_config=profile_config.project_selection,
        )

        if shortage:
            console.print(f"  [yellow]![/yellow] {shortage}")

        console.print("  [bold]Selected Projects Sequence:[/bold]")
        for idx, p in enumerate(selected_projects, 1):
            is_fx_pos = (
                has_fx
                and profile_config.project_selection.fixed_project
                and idx == profile_config.project_selection.fixed_project.position
            )
            tag = f"[bold cyan][FIXED POSITION {idx}][/bold cyan]" if is_fx_pos else f"[dynamic rank #{idx}]"
            console.print(f"    {idx}. {p.title} {tag}")

        # [5/7] Generating tailored content
        console.print("[bold blue][5/7][/bold blue] Generating tailored content with Multi-Provider AI system...")
        provider_mgr = ProviderManager()
        tailored_content, provider_name, model_used = provider_mgr.generate(
            profile=profile,
            selected_projects=selected_projects,
            jd=jd,
            req_matrix=req_matrix,
            requested_provider=provider,
            offline=offline,
        )
        console.print(f"  [green]✓[/green] Content generated by: [bold cyan]{provider_name}[/bold cyan] (Model: [bold]{model_used}[/bold])")

        # Assemble manifest
        manifest = build_resume_manifest(
            profile=profile,
            selected_projects=selected_projects,
            tailored_ai=tailored_content,
            jd=jd,
            model_used=f"{provider_name} ({model_used})",
            profile_config=profile_config,
        )

        if dry_run:
            console.print("[bold yellow]Dry-run requested. Skipping document generation to disk.[/bold yellow]")
            console.print(Panel(manifest.summary, title="Generated Professional Summary"))
            return 0

        # [6/7] Creating one-page documents
        console.print("[bold blue][6/7][/bold blue] Creating exactly one-page PDF and DOCX documents...")
        base_out = Path(custom_output) if custom_output else PROJECT_ROOT / "output"
        app_results = write_complete_application(
            manifest=manifest,
            jd=jd,
            req_matrix=req_matrix,
            selected_projects=selected_projects,
            scored_pool=scored_pool,
            base_output_dir=base_out,
            profile_id=profile_id,
        )
        util_pct = app_results.get("vertical_utilization_pct", "N/A")
        console.print(f"  [green]✓[/green] PDF generated ({app_results['page_count']} page, {util_pct}% vertical utilization) -> {app_results['pdf_path']}")
        console.print(f"  [green]✓[/green] DOCX generated -> {app_results['docx_path']}")
        if "preview_png" in app_results:
            console.print(f"  [green]✓[/green] Visual QA preview image -> {app_results['preview_png']}")

        # [7/7] Running ATS validation
        console.print("[bold blue][7/7][/bold blue] Running ATS validation on actual generated document...")
        ats_report = app_results["ats_report"]
        console.print(f"  [green]✓[/green] Extracted selectable text from final PDF ({len(app_results['ats_report'].matched_must_have)} must-have matches)")

        # Print ATS Report
        console.print("")
        console.print(Panel(ats_report.format_console_text(), title="[bold green]ATS READINESS REPORT[/bold green]"))

        console.print("")
        console.print(f"[bold green]Application package created successfully:[/bold green] {app_results['output_directory']}")
        return 0

    except Exception as e:
        logger.exception("Pipeline failed with exception")
        console.print(f"\n[bold red]Pipeline Error:[/bold red] {e}")
        return 1


def handle_check_providers() -> None:
    """Check health, connectivity, auth, and free-tier eligibility for all providers."""
    console.print("\n[bold cyan]Scanning All Configured AI Providers...[/bold cyan]\n")
    mgr = ProviderManager()
    data = mgr.check_all_providers()

    table = Table(title="AI Provider Health & Availability Status")
    table.add_column("Priority", justify="center", style="cyan")
    table.add_column("Provider", style="bold")
    table.add_column("Key Configured", justify="center")
    table.add_column("Auth Status", justify="center")
    table.add_column("Connectivity", justify="center")
    table.add_column("Free Tier", justify="center", style="green")
    table.add_column("Status / Details", style="dim")

    for p in data["providers"]:
        cfg_str = "[green]YES[/green]" if p["configured"] else "[red]NO[/red]"
        auth_color = "green" if p["auth_status"] in ("Valid", "Not Required") else "red"
        auth_str = f"[{auth_color}]{p['auth_status']}[/{auth_color}]"
        conn_color = "green" if "Reachable" in p["connectivity"] or "Local" in p["connectivity"] else "yellow"
        conn_str = f"[{conn_color}]{p['connectivity']}[/{conn_color}]"
        ft_str = "[green]YES[/green]" if p["free_tier"] else "[yellow]PAID[/yellow]"

        table.add_row(
            f"#{p['priority_rank']}",
            p["provider"],
            cfg_str,
            auth_str,
            conn_str,
            ft_str,
            p["details"],
        )

    console.print(table)
    console.print(f"\n[bold green]Selected Primary Provider:[/bold green] {data['selected_primary']}")
    console.print(f"[bold cyan]Active Fallback Sequence:[/bold cyan] {' -> '.join(data['fallback_sequence'])}\n")


def handle_benchmark_providers() -> None:
    """Benchmark configured providers with a lightweight anonymized test prompt."""
    console.print("\n[bold cyan]Benchmarking Available AI Providers...[/bold cyan]\n")
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    mgr = ProviderManager()
    results = mgr.benchmark_providers(profile, projects)

    table = Table(title="AI Provider Benchmark Results")
    table.add_column("Provider", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Latency (sec)", justify="right", style="cyan")
    table.add_column("Schema Valid", justify="center")
    table.add_column("Bearing Fault Pos #2", justify="center")
    table.add_column("Model Used", style="magenta")

    for r in results:
        status_color = "green" if r["status"] == "Success" else ("yellow" if "Skipped" in r["status"] else "red")
        status_str = f"[{status_color}]{r['status']}[/{status_color}]"
        lat_str = f"{r['latency_sec']}s" if r["latency_sec"] is not None else "-"
        schema_str = "[green]PASS[/green]" if r["schema_valid"] else ("-" if r["schema_valid"] is None else "[red]FAIL[/red]")
        bf_str = "[green]PASS[/green]" if r["bearing_fault_pos2"] else ("-" if r["bearing_fault_pos2"] is None else "[red]FAIL[/red]")

        table.add_row(
            r["provider"],
            status_str,
            lat_str,
            schema_str,
            bf_str,
            r["model_used"],
        )

    console.print(table)
    console.print("\n[green]✓ Benchmark complete. Candidate personal identifiers were completely stripped.[/green]\n")


def handle_list_profiles() -> None:
    """List all registered candidate profiles in a structured table."""
    profiles = ProfileManager.list_all_profiles()
    table = Table(title="Registered Candidate Profiles")
    table.add_column("Profile ID", style="cyan", justify="left")
    table.add_column("Candidate Name", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Profile File", justify="center")
    table.add_column("Projects File", justify="center")
    table.add_column("Created", style="dim")

    for p in profiles:
        stat_color = "green" if p["source_status"] in ("verified_source", "synthetic_fixture") else "yellow"
        stat_str = f"[{stat_color}]{p['source_status']}[/{stat_color}]"
        pf_str = "[green]YES[/green]" if p["has_profile"] else "[red]NO[/red]"
        pj_str = "[green]YES[/green]" if p["has_projects"] else "[red]NO[/red]"
        created = p["created_at"][:19].replace("T", " ") if "T" in p["created_at"] else p["created_at"]
        table.add_row(
            p["profile_id"],
            p["candidate_name"],
            stat_str,
            pf_str,
            pj_str,
            created,
        )

    console.print(table)


def handle_validate_profile(profile_id: str) -> None:
    """Run comprehensive validation on specified candidate profile."""
    console.print(f"[bold blue]Validating Profile:[/bold blue] [bold cyan]{profile_id}[/bold cyan]...")
    pm = ProfileManager(profile_id=profile_id)
    val = pm.validate_profile()

    if val["valid"]:
        console.print(f"[bold green]✓ Profile '{profile_id}' is valid and fully compliant![/bold green]")
        console.print(f"  Candidate: [bold]{val.get('candidate_name', 'N/A')}[/bold]")
        console.print(f"  Verified Projects: [bold]{val['projects_count']}[/bold]")
        console.print(f"  Technical Skills: [bold]{val['skills_count']}[/bold]")
        if val["warnings"]:
            for w in val["warnings"]:
                console.print(f"  [yellow]Warning:[/yellow] {w}")
    else:
        console.print(f"[bold red]✗ Profile '{profile_id}' failed validation:[/bold red]")
        for err in val["errors"]:
            console.print(f"  [red]- {err}[/red]")
        sys.exit(1)


def handle_profile_info(profile_id: str) -> None:
    """Print in-depth information about a specific candidate profile."""
    info = ProfileManager.get_profile_info(profile_id)
    table = Table(title=f"Profile Details: {profile_id}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold")

    table.add_row("Profile ID", info.get("profile_id", profile_id))
    table.add_row("Candidate Name", info.get("candidate_name", "N/A"))
    table.add_row("Email", info.get("email", "N/A"))
    table.add_row("Phone", info.get("phone", "N/A"))
    table.add_row("Headline Rule", f"{info.get('headline_mode')} -> {info.get('headline', 'N/A')}")
    table.add_row("Summary Rule", info.get("summary_mode", "N/A"))
    fx = info.get("fixed_project")
    fx_str = f"{fx['id']} at position #{fx['position']}" if fx else "None (Dynamic)"
    table.add_row("Fixed Project Rule", fx_str)
    table.add_row("Prohibited Terms", ", ".join(info.get("prohibited_terms", [])) or "None")
    table.add_row("Verified Projects Count", str(info.get("projects_count", 0)))
    table.add_row("Technical Skills Count", str(info.get("skills_count", 0)))
    table.add_row("Synthetic Fixture", "YES" if info.get("is_synthetic") else "NO")
    table.add_row("Validation Status", "[green]VALID[/green]" if info.get("valid") else "[red]INVALID[/red]")

    console.print(table)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Provider AI ATS Resume Tailoring System with Multi-Profile Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Profile management options
    parser.add_argument("--profile", type=str, default=DEFAULT_PROFILE_ID, help="Active candidate profile ID (default: sujal)")
    parser.add_argument("--list-profiles", action="store_true", help="List all registered candidate profiles")
    parser.add_argument("--create-profile", type=str, help="Scaffold a new candidate profile directory with given ID")
    parser.add_argument("--source-dir", type=str, help="Source directory containing PDF resumes for newly created profile")
    parser.add_argument("--validate-profile", action="store_true", help="Validate active profile schema, projects, and rules")
    parser.add_argument("--profile-info", action="store_true", help="Display deep details and statistics for active profile")

    # JD and generation options
    parser.add_argument("--jd", "--jd-file", dest="jd_file", type=str, help="Path to job description text file")
    parser.add_argument("--jd-text", type=str, help="Raw job description text passed via command line")
    parser.add_argument("--company", type=str, help="Target company name (override auto-detection)")
    parser.add_argument("--role", type=str, help="Target job role/title (override auto-detection)")
    parser.add_argument("--provider", type=str, choices=["gemini", "groq", "cohere", "openrouter", "cloudflare", "offline"], help="Specify preferred AI provider")
    parser.add_argument("--output", type=str, help="Custom output directory")
    parser.add_argument("--dry-run", action="store_true", help="Perform analysis and generation without writing files")
    parser.add_argument("--check-only", action="store_true", help="Analyze JD and candidate match without building documents")
    parser.add_argument("--offline", action="store_true", help="Run in deterministic offline mode (no API calls)")
    parser.add_argument("--list-projects", action="store_true", help="List all verified candidate projects in database")
    parser.add_argument("--refresh-profile", action="store_true", help="Rescan source resumes and refresh master profile with backup")
    parser.add_argument("--check-providers", action="store_true", help="Audit AI providers health, connectivity, and model availability")
    parser.add_argument("--benchmark-providers", action="store_true", help="Benchmark providers with an anonymized test prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed debug logs")

    args = parser.parse_args()

    # Handle profile management commands
    if args.list_profiles:
        handle_list_profiles()
        sys.exit(0)

    if args.create_profile:
        src_path = Path(args.source_dir) if args.source_dir else None
        try:
            res = ProfileManager.create_new_profile(
                profile_id=args.create_profile,
                candidate_name=args.create_profile.replace("_", " ").title(),
                source_dir=src_path,
            )
            console.print(f"[bold green]✓ Created profile '{res['profile_id']}' at {res['profile_dir']}[/bold green]")
            if res["copied_sources"]:
                console.print(f"  Copied source files: {', '.join(res['copied_sources'])}")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Failed to create profile: {e}[/bold red]")
            sys.exit(1)

    if args.validate_profile:
        handle_validate_profile(args.profile)
        sys.exit(0)

    if args.profile_info:
        handle_profile_info(args.profile)
        sys.exit(0)

    # Handle --check-providers
    if args.check_providers:
        handle_check_providers()
        sys.exit(0)

    # Handle --benchmark-providers
    if args.benchmark_providers:
        handle_benchmark_providers()
        sys.exit(0)

    # Handle --list-projects
    if args.list_projects:
        pm = ProfileManager(profile_id=args.profile)
        summary = pm.list_projects_summary()
        table = Table(title=f"Verified Candidate Projects Database ({args.profile})")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Categories", style="magenta")
        table.add_column("Fixed Rule", style="yellow")
        table.add_column("Status", style="green")

        for p in summary:
            rule_str = f"Slot #{p['fixed_pos']} (Permanent)" if p["is_fixed"] else "Dynamic"
            table.add_row(p["id"], p["title"], ", ".join(p["categories"]), rule_str, p["verification_status"])

        console.print(table)
        sys.exit(0)

    # Handle --refresh-profile
    if args.refresh_profile:
        console.print(f"[bold blue]Refreshing master profile for {args.profile} from source resumes...[/bold blue]")
        pm = ProfileManager(profile_id=args.profile)
        try:
            res = pm.refresh_from_source(PROJECT_ROOT)
            console.print(f"[bold green]✓ Profile refreshed successfully from {res['r1']} and {res['r2']}[/bold green]")
            console.print(f"Verified Projects Count: {res['projects_count']}")
            if res["conflicts"]:
                console.print("\n[bold yellow]Reconciled Audit Conflicts:[/bold yellow]")
                for c in res["conflicts"]:
                    console.print(f"- [bold]{c['field']}:[/bold] {c['detail']}")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Failed to refresh profile: {e}[/bold red]")
            sys.exit(1)

    # Obtain JD text
    jd_text = ""
    if args.jd_text:
        jd_text = args.jd_text
    elif args.jd_file:
        p = Path(args.jd_file)
        if not p.exists():
            console.print(f"[bold red]Error: JD file does not exist: {p}[/bold red]")
            sys.exit(1)
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            jd_text = f.read()
    else:
        # Multiline interactive input
        jd_text = get_multiline_jd_input()

    exit_code = run_pipeline(
        jd_text=jd_text,
        profile_id=args.profile,
        company=args.company,
        role=args.role,
        provider=args.provider,
        offline=args.offline,
        dry_run=args.dry_run,
        check_only=args.check_only,
        custom_output=args.output,
        verbose=args.verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
