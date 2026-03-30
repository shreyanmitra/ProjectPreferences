# (C) Shreyan Mitra
"""
Constraint validation and scoring for CSE403 project team assignments.

Validates assignments against: (1) every student assigned, (2) team size bounds,
(3) pitcher rule (pitchers on their #1 choice project), (4) teammate rule (at
least one preferred teammate per student). Also provides scoring and mandatory
pitcher lookup.

Assignment format: Dict[project_name, List[net_id]]
"""
from typing import Dict, List, Tuple

from .config import Config
from .models import Student


def validate_assignment(
    project_to_members: Dict[str, List[str]],
    students: List[Student],
    config: Config,
) -> Tuple[bool, List[str]]:
    """
    Validate an assignment against all rules: all assigned, team sizes, pitcher
    rule, teammate rule.

    Args:
        project_to_members: Map project name -> list of assigned NetIDs
        students: All students (for lookup)
        config: Configuration (min/max team size)

    Returns:
        Tuple of (is_valid, list of error messages). Empty errors if valid.
    """
    errors: List[str] = []
    net_id_to_student = {s.net_id: s for s in students}
    net_id_to_project: Dict[str, str] = {}
    for proj, members in project_to_members.items():
        for mid in members:
            net_id_to_project[mid] = proj

    # Rule 1: Every student must be assigned
    assigned = set(net_id_to_project.keys())
    all_net_ids = {s.net_id for s in students}
    unassigned = all_net_ids - assigned
    if unassigned:
        errors.append(f"Unassigned students: {sorted(unassigned)}")

    # Rule 2: Team sizes must be within min_team_size and max_team_size
    for proj, members in project_to_members.items():
        n = len(members)
        if n < config.min_team_size or n > config.max_team_size:
            errors.append(
                f"Project '{proj}' has {n} members "
                f"(valid: {config.min_team_size}-{config.max_team_size})"
            )

    # Rule 3: Pitcher rule — pitchers whose #1 choice is their pitched project must be on that project
    for s in students:
        if not s.must_be_on_pitched_project():
            continue
        proj = s.project_pitched
        if proj not in project_to_members:
            continue
        if s.net_id not in project_to_members[proj]:
            errors.append(
                f"Pitcher rule: {s.net_id} pitched {proj} (their #1 choice) but is not on {proj}"
            )

    # Rule 4: Teammate rule — each student with preferred teammates must have at least one on their project
    for s in students:
        if not s.preferred_teammates:
            continue
        proj = net_id_to_project.get(s.net_id)
        if not proj:
            continue
        teammates_on_project = set(project_to_members.get(proj, [])) - {s.net_id}
        has_teammate = any(tm in teammates_on_project for tm in s.preferred_teammates)
        if not has_teammate:
            errors.append(
                f"Teammate rule: {s.net_id} has no preferred teammate on {proj}"
            )

    return len(errors) == 0, errors


def score_assignment(
    project_to_members: Dict[str, List[str]],
    students: List[Student],
    config: Config,
) -> float:
    """
    Compute total preference score for an assignment. Higher is better.
    Uses config.rank_points: rank 1 -> pts[0], rank 2 -> pts[1], etc.

    Args:
        project_to_members: Map project name -> list of assigned NetIDs
        students: All students
        config: Configuration (rank_points tuple)

    Returns:
        Total score (sum of points for each student's assigned project rank)
    """
    net_id_to_project: Dict[str, str] = {}
    for proj, members in project_to_members.items():
        for mid in members:
            net_id_to_project[mid] = proj

    total = 0.0
    pts = config.rank_points
    for s in students:
        proj = net_id_to_project.get(s.net_id)
        if not proj:
            continue
        rank = s.rank_of_project(proj)
        if rank is not None and 1 <= rank <= 5:
            idx = min(rank - 1, len(pts) - 1)
            total += pts[idx]
    return total


def get_mandatory_pitchers(students: List[Student]) -> Dict[str, List[str]]:
    """
    Return mapping of project -> NetIDs who must be on that project (pitcher rule).
    Includes only students who pitched the project AND ranked it as #1 choice.
    """
    result: Dict[str, List[str]] = {}
    for s in students:
        if s.must_be_on_pitched_project() and s.project_pitched:
            proj = s.project_pitched
            if proj not in result:
                result[proj] = []
            result[proj].append(s.net_id)
    return result
