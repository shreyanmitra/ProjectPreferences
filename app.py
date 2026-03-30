#!/usr/bin/env python3
# (C) Shreyan Mitra
"""
CSE403 Project Team Assignment App

Entry point for assigning students to project teams based on CSV preferences.
Reads a CSV of student preferences (project rankings, pitched projects, preferred
teammates), runs an assignment algorithm (OR-Tools or greedy), and outputs a
report or CSV of team assignments.

Usage:
    python app.py input.csv [--algorithm ortools|greedy] [-o output.txt] [--plain]
"""
import argparse
import sys
from pathlib import Path


def _configure_utf8_console() -> None:
    """
    Reconfigure stdout/stderr to UTF-8 for Rich spinners and Unicode on Windows.
    Silently ignores streams that don't support reconfigure or raise errors.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


from src.config import Config, load_config, merge_config
from src.parser import parse_csv
from src.algorithm import assign
from src.output import generate_report, generate_csv, print_report_rich


def main() -> None:
    """
    Parse arguments, load config, run assignment, and generate output.
    Uses Rich formatting for console output unless --plain or -o is specified.
    """
    parser = argparse.ArgumentParser(
        description="Assign students to CSE403 project teams based on preferences."
    )
    parser.add_argument(
        "input_csv",
        help="Path to input CSV file with student preferences",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to output file (default: print to stdout)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to JSON config file (optional)",
    )
    parser.add_argument(
        "--format",
        choices=["report", "csv"],
        default="report",
        help="Output format: report (human-readable) or csv",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable rich formatting (plain text output)",
    )
    parser.add_argument(
        "--algorithm",
        choices=["greedy", "ortools"],
        default=None,
        help="Assignment algorithm: ortools (default) or greedy",
    )
    parser.add_argument(
        "--ortools-timeout",
        type=int,
        default=None,
        help="OR-Tools solver timeout in seconds (default: 60)",
    )
    # Config overrides
    parser.add_argument("--min-team-size", type=int, default=None)
    parser.add_argument("--max-team-size", type=int, default=None)
    parser.add_argument("--preferred-team-size", type=int, default=None)
    parser.add_argument("--max-projects", type=int, default=None)

    args = parser.parse_args()

    # Ensure UTF-8 console for Rich formatting on Windows
    _configure_utf8_console()

    # Use Rich panels/tables when printing to console (no -o, no --plain)
    use_rich = not args.plain and not args.output

    if use_rich:
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich import box

        console = Console()
        console.print()
        console.print(
            Panel(
                "[bold cyan]CSE403[/] [bold white]Project Team Assignment[/] [dim]v1.0[/]",
                box=box.DOUBLE,
                border_style="cyan",
                padding=(0, 2),
            )
        )
        console.print()

    # Load config from file (if provided) and apply CLI overrides
    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)
    overrides = {
        "min_team_size": args.min_team_size,
        "max_team_size": args.max_team_size,
        "preferred_team_size": args.preferred_team_size,
        "max_projects": args.max_projects,
        "algorithm": args.algorithm,
        "ortools_timeout_seconds": args.ortools_timeout,
    }
    config = merge_config(config, overrides)

    # Parse input CSV into Student objects
    try:
        if use_rich:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Parsing input CSV...", total=None)
                students, warnings = parse_csv(args.input_csv)
                progress.update(task, description=f"[green]Parsed {len(students)} students[/]")
        else:
            students, warnings = parse_csv(args.input_csv)
    except FileNotFoundError as e:
        msg = f"Error: {e}"
        if use_rich:
            console.print(f"[bold red]{msg}[/]")
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    for w in warnings:
        if use_rich:
            console.print(f"  [yellow]⚠[/] [dim]{w}[/]")
        else:
            print(f"Warning: {w}", file=sys.stderr)

    # Run assignment algorithm (ortools or greedy, with fallback)
    if use_rich:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running assignment algorithm...", total=None)
            result, algo_warnings = assign(students, config)
            n_projects = len(result)
            progress.update(task, description=f"[green]Assigned to {n_projects} projects[/]")
    else:
        result, algo_warnings = assign(students, config)

    for w in algo_warnings:
        if use_rich:
            console.print(f"  [yellow]⚠[/] [dim]{w}[/]")
        else:
            print(f"Warning: {w}", file=sys.stderr)

    if use_rich and algo_warnings:
        console.print()

    # Generate output: report (human-readable) or CSV
    if args.format == "report":
        if args.output:
            output = generate_report(result, students, config)
            Path(args.output).write_text(output, encoding="utf-8")
            if use_rich:
                console.print(f"[green]✓[/] Report written to [bold]{args.output}[/]")
        else:
            if use_rich:
                print_report_rich(result, students, config)
            else:
                output = generate_report(result, students, config)
                print(output)
    else:
        output = generate_csv(result, students)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            if use_rich:
                console.print(f"[green]✓[/] CSV written to [bold]{args.output}[/]")
        else:
            print(output)


if __name__ == "__main__":
    main()
