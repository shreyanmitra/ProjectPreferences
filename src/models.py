# (C) Shreyan Mitra
"""
Data models for CSE403 Project Team Assignment.

Defines Student (preferences, rankings, teammates) and Project (name + members).
These are the core domain objects used by the parser, algorithms, and output.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Student:
    """
    Represents a student and their project/teammate preferences.

    Attributes:
        name: Display name.
        net_id: Unique identifier (e.g., UW NetID).
        project_pitched: Project this student pitched, or None if none.
        rankings: Ordered list of project names (1st through 5th choice). May be
            empty or sparse if fewer than 5 choices provided.
        preferred_teammates: List of NetIDs of preferred teammates (0-3 allowed).
    """

    name: str
    net_id: str
    project_pitched: Optional[str]
    rankings: List[str]
    preferred_teammates: List[str]

    def first_choice(self) -> Optional[str]:
        """Return the student's first-choice project, or None if no rankings."""
        return self.rankings[0] if self.rankings else None

    def has_project_in_top5(self, project: str) -> bool:
        """Return True if the project appears in the student's rankings (top 5)."""
        return project in self.rankings

    def rank_of_project(self, project: str) -> Optional[int]:
        """
        Return 1-based rank of project in preferences (1 = first choice).
        Returns None if project is not in the rankings.
        """
        if project not in self.rankings:
            return None
        return self.rankings.index(project) + 1

    def is_pitcher_for(self, project: str) -> bool:
        """Return True if this student pitched the given project."""
        return self.project_pitched == project if self.project_pitched else False

    def must_be_on_pitched_project(self) -> bool:
        """
        Return True if the pitcher rule applies: student pitched a project AND
        that project is their #1 choice. Such students must be placed on that project.
        """
        if not self.project_pitched:
            return False
        return self.first_choice() == self.project_pitched


@dataclass
class Project:
    """
    Represents a project and its assigned team.

    Attributes:
        name: Project name (must match names in student rankings).
        members: List of NetIDs assigned to this project.
    """

    name: str
    members: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Return the number of students assigned to this project."""
        return len(self.members)
