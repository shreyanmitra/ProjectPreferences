# (C) Shreyan Mitra
"""
Output and report generation for CSE403 project team assignments.

Provides plain-text report generation, Rich-formatted console output, and CSV
export. Reports include validation result, preference score, and per-project
assignments with student names and choice rankings.
"""
from typing import Dict, List

from .config import Config
from .constraints import score_assignment, validate_assignment
from .models import Student


def generate_report(
    project_to_members: Dict[str, List[str]],
    students: List[Student],
    config: Config,
) -> str:
    """
    Generate a plain-text report of the assignment for file output.

    Includes validation result, preference score, and per-project member list
    with choice rank (e.g., [choice #1]).

    Args:
        project_to_members: Map project name -> list of assigned NetIDs
        students: All students (for name/rank lookup)
        config: Configuration (for validation)

    Returns:
        Multi-line string report
    """
    net_id_to_student = {s.net_id: s for s in students}
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("CSE403 Project Team Assignment Report")
    lines.append("=" * 60)

    valid, errors = validate_assignment(project_to_members, students, config)
    lines.append(f"\nValidation: {'PASS' if valid else 'FAIL'}")
    if errors:
        lines.append(f"Errors: {len(errors)}")
        for e in errors[:10]:
            lines.append(f"  - {e}")
        if len(errors) > 10:
            lines.append(f"  ... and {len(errors) - 10} more")

    score = score_assignment(project_to_members, students, config)
    lines.append(f"\nPreference Score: {score:.0f} (higher = better)")

    lines.append("\n" + "-" * 60)
    lines.append("Project Assignments")
    lines.append("-" * 60)

    for proj in sorted(project_to_members.keys()):
        members = project_to_members[proj]
        lines.append(f"\n{proj} ({len(members)} members)")
        for net_id in members:
            s = net_id_to_student.get(net_id)
            name = s.name if s else net_id
            rank = s.rank_of_project(proj) if s else None
            rank_str = f" [choice #{rank}]" if rank else ""
            lines.append(f"  - {name} ({net_id}){rank_str}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def print_report_rich(
    project_to_members: Dict[str, List[str]],
    students: List[Student],
    config: Config,
) -> None:
    """
    Print a styled report to the console using Rich (panels, tables).

    Shows summary (validation, score, project count), any errors, and a
    table of project assignments.
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box

    console = Console()
    net_id_to_student = {s.net_id: s for s in students}

    valid, errors = validate_assignment(project_to_members, students, config)
    score = score_assignment(project_to_members, students, config)

    # Report header and summary panel
    console.print()

    # Summary
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column(style="dim")
    summary.add_column()
    valid_style = "green" if valid else "yellow"
    summary.add_row("Validation", f"[{valid_style}]{'PASS' if valid else 'FAIL'}[/]")
    summary.add_row("Preference Score", f"[bold]{score:.0f}[/] (higher = better)")
    summary.add_row("Projects", str(len(project_to_members)))
    summary.add_row("Students Assigned", str(sum(len(m) for m in project_to_members.values())))
    console.print(Panel(summary, title="Summary", border_style="blue", padding=(0, 1)))
    console.print()

    # Errors (if any)
    if errors:
        err_text = Text("\n".join(f"• {e}" for e in errors[:15]))
        if len(errors) > 15:
            err_text.append(f"\n... and {len(errors) - 15} more", style="dim")
        console.print(Panel(err_text, title=f"Warnings ({len(errors)})", border_style="yellow", padding=(0, 1)))
        console.print()

    # Project assignments table
    assignments_table = Table(
        title="Project Assignments",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
    )
    assignments_table.add_column("Project", style="cyan", no_wrap=True)
    assignments_table.add_column("Size", justify="right", style="dim")
    assignments_table.add_column("Members", style="white")

    for proj in sorted(project_to_members.keys()):
        members = project_to_members[proj]
        member_lines = []
        for net_id in members:
            s = net_id_to_student.get(net_id)
            name = s.name if s else net_id
            rank = s.rank_of_project(proj) if s else None
            if rank:
                member_lines.append(f"{name} ({net_id}) [dim]#{rank}[/]")
            else:
                member_lines.append(f"{name} ({net_id})")
        assignments_table.add_row(proj, str(len(members)), "\n".join(member_lines))

    console.print(assignments_table)
    console.print()


def generate_csv(
    project_to_members: Dict[str, List[str]],
    students: List[Student],
) -> str:
    """
    Generate CSV output with columns: NetID, Name, Assigned Project.

    Uses student list order; students not assigned get empty project.
    """
    net_id_to_project: Dict[str, str] = {}
    for proj, members in project_to_members.items():
        for mid in members:
            net_id_to_project[mid] = proj

    lines = ["NetID,Name,Assigned Project"]
    for s in students:
        proj = net_id_to_project.get(s.net_id, "")
        lines.append(f"{s.net_id},{s.name},{proj}")
    return "\n".join(lines)
