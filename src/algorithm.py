# (C) Shreyan Mitra
"""
Greedy assignment algorithm for CSE403 project teams.

Places pitchers first, then iteratively assigns remaining students to the best
available project (preference + teammate rule). May relax teammate rule if no
valid option exists, producing warnings. Order-dependent: processing order
(CSV order) can affect the final assignment and score.
"""
from typing import Dict, List, Set, Tuple

from .config import Config
from .constraints import get_mandatory_pitchers
from .models import Student


def _all_projects_from_data(students: List[Student]) -> Set[str]:
    """Collect all unique project names from pitched projects and rankings."""
    projects = set()
    for s in students:
        if s.project_pitched:
            projects.add(s.project_pitched)
        for p in s.rankings:
            projects.add(p)
    return projects


def _project_demand(students: List[Student], project: str) -> int:
    """Count students who include this project in their rankings (top 5)."""
    return sum(1 for s in students if s.has_project_in_top5(project))


def _select_projects(
    students: List[Student],
    mandatory: Dict[str, List[str]],
    config: Config,
) -> List[str]:
    """
    Select which projects to run. Limits count based on student count and
    config so teams can satisfy min/max size. Prioritizes projects with
    mandatory pitchers and high demand.
    """
    n_students = len(students)
    min_projects = (n_students + config.preferred_team_size - 1) // config.preferred_team_size
    max_projects = (n_students + config.min_team_size - 1) // config.min_team_size

    if config.max_projects is not None:
        target_projects = min(max_projects, max(min_projects, config.max_projects))
    else:
        target_projects = min(max_projects, max(min_projects, min_projects + 2))

    all_projects = _all_projects_from_data(students)

    # Score projects: mandatory pitchers get high weight, then demand
    def score_proj(p: str) -> int:
        m = len(mandatory.get(p, [])) * 100
        d = _project_demand(students, p)
        return m + d

    sorted_projects = sorted(all_projects, key=score_proj, reverse=True)
    return sorted_projects[:target_projects]


def _satisfies_teammate_constraint(
    net_id: str,
    project_members: List[str],
    student: Student,
) -> bool:
    """Return True if placing the student on this project would satisfy the teammate rule."""
    if not student.preferred_teammates:
        return True
    teammates_on = set(project_members) & set(student.preferred_teammates)
    return len(teammates_on) >= 1


def _rank_preference_for_project(student: Student, project: str, config: Config) -> int:
    """Return preference score from config.rank_points; higher = better."""
    rank = student.rank_of_project(project)
    if rank is None or rank < 1 or rank > 5:
        return 0
    pts = config.rank_points
    idx = min(rank - 1, len(pts) - 1)
    return pts[idx]


def _project_needs_members(members: List[str], config: Config) -> bool:
    """Return True if project is below min_team_size (used to boost assignment priority)."""
    return len(members) < config.min_team_size


def assign_greedy(students: List[Student], config: Config) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Run the greedy assignment algorithm.

    Places mandatory pitchers first, then iterates over remaining students (in
    list order). For each student, prefers projects that (1) satisfy teammate
    rule and (2) maximize preference score. If no such project exists, relaxes
    teammate rule and assigns to best preference; adds a warning.

    Args:
        students: All students (order affects assignment)
        config: Configuration (team sizes, scoring, needs_members_boost)

    Returns:
        Tuple of (project_to_members dict, list of warning messages)
    """
    warnings: List[str] = []
    project_to_members: Dict[str, List[str]] = {}
    assigned: Set[str] = set()

    mandatory = get_mandatory_pitchers(students)
    selected_projects = _select_projects(students, mandatory, config)

    # Initialize projects and place mandatory pitchers
    for proj in selected_projects:
        project_to_members[proj] = []
    for proj, pitcher_net_ids in mandatory.items():
        if proj in selected_projects:
            project_to_members[proj] = list(pitcher_net_ids)
            assigned.update(pitcher_net_ids)

    remaining = [s for s in students if s.net_id not in assigned]
    max_iterations = len(remaining) * len(selected_projects) * 3  # prevent infinite loops
    it = 0

    # Iteratively assign remaining students (first pass: with teammate rule, then relax)
    while remaining and it < max_iterations:
        it += 1
        made_progress = False

        for s in list(remaining):
            best_project = None
            best_score = -1
            # First loop: only consider projects where teammate rule would be satisfied
            for proj in selected_projects:
                members = project_to_members[proj]
                if len(members) >= config.max_team_size:
                    continue
                if not _satisfies_teammate_constraint(s.net_id, members, s):
                    continue
                score = _rank_preference_for_project(s, proj, config)
                if _project_needs_members(members, config):
                    score += config.needs_members_boost
                if score > best_score:
                    best_score = score
                    best_project = proj

            if best_project is not None:
                project_to_members[best_project].append(s.net_id)
                assigned.add(s.net_id)
                remaining.remove(s)
                made_progress = True
                continue

            # Second loop: relax teammate rule, pick best preference
            for proj in selected_projects:
                members = project_to_members[proj]
                if len(members) >= config.max_team_size:
                    continue
                score = _rank_preference_for_project(s, proj, config)
                if _project_needs_members(members, config):
                    score += config.needs_members_boost
                if score > best_score:
                    best_score = score
                    best_project = proj
            if best_project is not None:
                project_to_members[best_project].append(s.net_id)
                assigned.add(s.net_id)
                remaining.remove(s)
                made_progress = True
                if s.preferred_teammates:
                    warnings.append(
                        f"Relaxed teammate rule for {s.net_id} "
                        "(no valid project with teammates)"
                    )

        if not made_progress and remaining:
            break

    if remaining:
        warnings.append(
            f"Could not assign {len(remaining)} students: {[s.net_id for s in remaining]}"
        )

    project_to_members = {p: m for p, m in project_to_members.items() if m}

    for proj, members in project_to_members.items():
        n = len(members)
        if n < config.min_team_size:
            warnings.append(
                f"Project '{proj}' has {n} members (minimum {config.min_team_size})"
            )
        if n > config.max_team_size:
            warnings.append(
                f"Project '{proj}' has {n} members (maximum {config.max_team_size})"
            )

    return project_to_members, warnings


def assign(students: List[Student], config: Config) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Run assignment algorithm based on config.algorithm.

    If "ortools": use OR-Tools CP-SAT solver. On failure (infeasible, timeout,
    import error), fall back to greedy and prepend a fallback warning.
    If "greedy": use greedy algorithm directly.
    """
    if config.algorithm == "ortools":
        try:
            from .algorithm_ortools import assign_ortools

            result, warnings = assign_ortools(
                students,
                config,
                timeout_seconds=config.ortools_timeout_seconds,
            )
            if result:
                return result, warnings
            # OR-Tools failed (infeasible, etc.) — fall back to greedy
            ortools_reason = (warnings[0] + " ") if warnings else ""
            fallback_msg = (
                f"OR-Tools could not find a feasible solution. {ortools_reason}"
                " Falling back to greedy algorithm (some teammate preferences may not be satisfied)."
            )
            result = assign_greedy(students, config)
            return result[0], [fallback_msg] + result[1]
        except ImportError:
            warnings = ["ortools not installed; using greedy algorithm."]
            result = assign_greedy(students, config)
            return result[0], warnings + result[1]
        except Exception as e:
            warnings = [f"OR-Tools error: {e}; falling back to greedy."]
            result = assign_greedy(students, config)
            return result[0], warnings + result[1]

    return assign_greedy(students, config)
