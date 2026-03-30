# (C) Shreyan Mitra
"""
CSV parser for student preference data.

Reads a CSV with columns for Name, NetID, Project Pitched, First through Fifth
Choice, and preferred teammate NetIDs. Handles header variations (e.g., extra
spaces). Returns a list of Student objects and any parse/validation warnings.
"""
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from .models import Student


# Expected column names (normalized for matching; handles "Second (2)  Choice" etc.)
COL_NAME = "Name"
COL_NETID = "NetID"
COL_PROJECT_PITCHED = "Project Pitched"
COL_CHOICES = [
    "First (1) Choice",
    "Second (2) Choice",
    "Third (3) Choice",
    "Fourth (4) Choice",
    "Fifth (5) Choice",
]
COL_TEAM_MEMBERS = ["Team Member #1 UW NetID", "Team Member #2 UW NetID", "Team Member #3 UW NetID"]


def _normalize_header(col: str) -> str:
    """Normalize column header for matching: collapse multiple spaces, strip."""
    return re.sub(r"\s+", " ", col.strip())


def _normalize_value(val) -> str:
    """Convert value to string and strip. Return empty string for NaN/None."""
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()


def _normalize_project_name(name: str) -> str:
    """Normalize project name (e.g., trim, consistent whitespace)."""
    return name.strip() if name else ""


def parse_csv(csv_path: str | Path) -> Tuple[List[Student], List[str]]:
    """
    Parse the input CSV into Student objects.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Tuple of (list of Student objects, list of warning messages).
        Warnings may include: missing NetID, invalid teammate references.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)

    # Map normalized header names to actual column names (handles variations)
    normalized_cols = {_normalize_header(c): c for c in df.columns}

    def get_col(key: str) -> str:
        key_norm = _normalize_header(key)
        if key_norm in normalized_cols:
            return normalized_cols[key_norm]
        # Fallback: find column that matches when normalized
        for c in df.columns:
            if _normalize_header(c) == key_norm:
                return c
        raise KeyError(f"Expected column not found: {key}")

    # Resolve column names (may differ from expected due to spacing)
    name_col = get_col(COL_NAME)
    netid_col = get_col(COL_NETID)
    pitched_col = get_col(COL_PROJECT_PITCHED)
    choice_cols = [get_col(c) for c in COL_CHOICES]
    team_cols = [get_col(c) for c in COL_TEAM_MEMBERS]

    students: List[Student] = []
    warnings: List[str] = []
    net_ids_in_file: set = set()

    # Build Student objects from each row
    for idx, row in df.iterrows():
        name = _normalize_value(row[name_col])
        net_id = _normalize_value(row[netid_col])
        if not net_id:
            warnings.append(f"Row {idx + 2}: Missing NetID, skipping")
            continue
        net_ids_in_file.add(net_id)

        project_pitched_raw = _normalize_value(row[pitched_col])
        project_pitched = _normalize_project_name(project_pitched_raw) or None

        rankings = []
        for col in choice_cols:
            val = _normalize_project_name(_normalize_value(row[col]))
            if val:
                rankings.append(val)

        preferred_teammates = []
        for col in team_cols:
            tm = _normalize_value(row[col])
            if tm:
                preferred_teammates.append(tm)

        students.append(
            Student(
                name=name,
                net_id=net_id,
                project_pitched=project_pitched,
                rankings=rankings,
                preferred_teammates=preferred_teammates,
            )
            )

    # Validate that preferred teammate NetIDs exist in the file
    for s in students:
        for tm in s.preferred_teammates:
            if tm not in net_ids_in_file:
                warnings.append(
                    f"Student {s.net_id}: preferred teammate '{tm}' not in file"
                )

    return students, warnings
