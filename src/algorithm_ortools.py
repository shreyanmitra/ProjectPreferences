# (C) Shreyan Mitra
"""
OR-Tools assignment algorithm for CSE403 project teams.

Uses Google OR-Tools CP-SAT solver to find an optimal assignment subject to:
team size bounds, pitcher rule, and teammate rule. Maximizes total preference
score. Returns empty dict and a warning on failure (infeasible, timeout);
caller typically falls back to greedy.
"""
from typing import Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

from .config import Config
from .constraints import get_mandatory_pitchers
from .models import Student

from .algorithm import _select_projects


def _preference_score(student: Student, project: str, config: Config) -> int:
    """Return preference score for assigning student to project. Higher = better."""
    rank = student.rank_of_project(project)
    if rank is None or rank < 1 or rank > 5:
        return 0
    pts = config.rank_points
    idx = min(rank - 1, len(pts) - 1)
    return pts[idx]


def assign_ortools(
    students: List[Student],
    config: Config,
    timeout_seconds: Optional[int] = 60,
) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Run OR-Tools CP-SAT assignment algorithm.

    Uses shared project selection, then builds a CP-SAT model with binary
    variables x[i][j] = 1 if student i assigned to project j. Enforces:
    each student to exactly one project, team size bounds, pitcher rule,
    teammate rule. Maximizes total preference score.

    Args:
        students: All students
        config: Configuration (team sizes, rank_points)
        timeout_seconds: Solver timeout. None = no limit.

    Returns:
        Tuple of (project_to_members, warnings). Empty dict and non-empty
        warning on failure (infeasible, timeout).
    """
    warnings: List[str] = []
    mandatory = get_mandatory_pitchers(students)
    selected_projects = _select_projects(students, mandatory, config)

    net_ids = [s.net_id for s in students]
    net_id_to_idx = {nid: i for i, nid in enumerate(net_ids)}
    n_students = len(students)
    n_projects = len(selected_projects)
    proj_to_idx = {p: j for j, p in enumerate(selected_projects)}
    idx_to_proj = selected_projects

    model = cp_model.CpModel()

    # Decision variables: x[i][j] = 1 iff student i is assigned to project j
    x = []
    for i in range(n_students):
        row = []
        for j in range(n_projects):
            row.append(model.NewBoolVar(f"x_{i}_{j}"))
        x.append(row)

    # Constraint: each student assigned to exactly one project
    for i in range(n_students):
        model.Add(sum(x[i][j] for j in range(n_projects)) == 1)

    # Constraint: team size per project within min/max
    for j in range(n_projects):
        model.Add(sum(x[i][j] for i in range(n_students)) >= config.min_team_size)
        model.Add(sum(x[i][j] for i in range(n_students)) <= config.max_team_size)

    # Constraint: pitcher rule — mandatory pitchers must be on their project
    for proj, pitcher_net_ids in mandatory.items():
        if proj not in proj_to_idx:
            continue
        j = proj_to_idx[proj]
        for nid in pitcher_net_ids:
            if nid in net_id_to_idx:
                i = net_id_to_idx[nid]
                model.Add(x[i][j] == 1)

    # Constraint: teammate rule — if student i on project j, at least one preferred teammate on j
    for i, s in enumerate(students):
        if not s.preferred_teammates:
            continue
        # Teammates that are in our student set (and not self)
        t_indices = [
            net_id_to_idx[t]
            for t in s.preferred_teammates
            if t in net_id_to_idx and t != s.net_id
        ]
        if not t_indices:
            continue
        for j in range(n_projects):
            # x[i,j] = 1 implies at least one teammate t has x[t,j] = 1
            model.Add(x[i][j] <= sum(x[t][j] for t in t_indices))

    # Objective: maximize total preference score
    coeffs = []
    vars_list = []
    for i, s in enumerate(students):
        for j, proj in enumerate(selected_projects):
            score = _preference_score(s, proj, config)
            if score > 0:
                coeffs.append(score)
                vars_list.append(x[i][j])
    if coeffs:
        model.Maximize(cp_model.LinearExpr.WeightedSum(vars_list, coeffs))

    solver = cp_model.CpSolver()
    if timeout_seconds is not None:
        solver.parameters.max_time_in_seconds = float(timeout_seconds)

    status = solver.Solve(model)

    # On failure (INFEASIBLE, etc.), return empty result and warning
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {}, [f"OR-Tools failed (status={status}). Use greedy fallback."]

    # Extract assignment from solver solution
    project_to_members: Dict[str, List[str]] = {p: [] for p in selected_projects}
    for i in range(n_students):
        for j in range(n_projects):
            if solver.Value(x[i][j]) == 1:
                project_to_members[idx_to_proj[j]].append(net_ids[i])
                break

    project_to_members = {p: m for p, m in project_to_members.items() if m}

    return project_to_members, warnings
