# (C) Shreyan Mitra
"""
Configuration for CSE403 project team assignment.

Loads settings from JSON (optional) and supports CLI overrides. All parameters
affecting team sizes, scoring, and algorithm behavior are defined here.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """
    Configurable parameters for team assignment.

    Attributes:
        min_team_size: Minimum students per project (default 4).
        max_team_size: Maximum students per project (default 6).
        preferred_team_size: Target team size for project count calculation.
        max_projects: Cap on number of projects to run. None = auto from student count.
        rank_points: Points for rank 1, 2, 3, 4, 5 (index 0 = 1st choice). Default (6,5,4,3,2).
        needs_members_boost: Extra score when assigning to a project below min_team_size.
        algorithm: "ortools" (default) or "greedy".
        ortools_timeout_seconds: Solver timeout. None = no limit.
    """

    min_team_size: int = 4
    max_team_size: int = 6
    preferred_team_size: int = 6
    max_projects: Optional[int] = 14
    rank_points: tuple = (6, 5, 4, 3, 2)
    needs_members_boost: int = 10
    algorithm: str = "ortools"
    ortools_timeout_seconds: Optional[int] = 60

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        """Create Config from a dictionary (e.g., loaded from JSON)."""
        return cls(
            min_team_size=d.get("min_team_size", 4),
            max_team_size=d.get("max_team_size", 6),
            preferred_team_size=d.get("preferred_team_size", 6),
            max_projects=d.get("max_projects"),
            rank_points=tuple(d.get("rank_points", [6, 5, 4, 3, 2])),
            needs_members_boost=d.get("needs_members_boost", 10),
            algorithm=d.get("algorithm", "ortools"),
            ortools_timeout_seconds=d.get("ortools_timeout_seconds", 60),
        )

    def to_dict(self) -> dict:
        """Export Config to a dictionary for JSON serialization."""
        return {
            "min_team_size": self.min_team_size,
            "max_team_size": self.max_team_size,
            "preferred_team_size": self.preferred_team_size,
            "max_projects": self.max_projects,
            "rank_points": list(self.rank_points),
            "needs_members_boost": self.needs_members_boost,
            "algorithm": self.algorithm,
            "ortools_timeout_seconds": self.ortools_timeout_seconds,
        }


def load_config(path: Optional[Path] = None) -> Config:
    """Load Config from a JSON file. Returns default Config if path is None or missing."""
    if path is None or not Path(path).exists():
        return Config()
    with open(path) as f:
        d = json.load(f)
    return Config.from_dict(d)


def merge_config(base: Config, overrides: dict) -> Config:
    """Return a new Config with overrides applied. None values in overrides are skipped."""
    d = base.to_dict()
    for k, v in overrides.items():
        if v is not None and k in d:
            d[k] = v
    return Config.from_dict(d)
