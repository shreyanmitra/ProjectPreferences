# CSE403 Project Team Assignment — Design Decisions

## Algorithm: OR-Tools (CP-SAT) vs Greedy

**Default:** OR-Tools (CP-SAT), with greedy as fallback.

**OR-Tools (CP-SAT):** Formulates the assignment as an integer linear program. Variables x[i,j] = student i on project j. Constraints: each student on one project; team sizes 4–6; pitcher rule (fixed assignments); teammate rule (x[i,j] <= sum of teammates on j). Objective: maximize preference score. OR-Tools finds an optimal or feasible solution that satisfies all constraints.

**Fallback:** If OR-Tools fails (infeasible, timeout, or not installed), the app falls back to the greedy algorithm. Greedy relaxes the teammate rule when necessary, so it always produces an assignment (possibly with violations).

**Greedy:** Assigns students one at a time. Simpler but not optimal; ~30 teammate-rule violations on the sample input. Use `--algorithm greedy` to force greedy.

---

## Project Selection

**Rule:** Pitcher rule applies only to *selected* projects. We choose which projects run.

**Approach:** Select a limited number of projects (e.g., 12–14) so that all students fit in teams of 4–6. Projects are scored by: (mandatory pitchers × 100) + (demand, i.e., students with project in top 5). Top-scoring projects are selected. If we selected every project with a pitcher, we would create too many small teams.

---

## Teammate Constraint Relaxation

**Rule:** Each student should have at least one preferred teammate on their assigned project.

**Relaxation:** If no project satisfies this (and has room), we place the student anyway and log a warning. Students with *no* preferred teammates are always treated as satisfying the rule.

**Result:** ~30 teammate-rule violations on the sample input. The greedy order of assignment leads to situations where later students cannot be placed with a preferred teammate.

---

## Team Size Exception (4-Person Teams)

**Rule:** Teams of 5–6 preferred, 4 allowed as exception.

**Implementation:** `min_team_size=4`, `max_team_size=6`, `preferred_team_size=6`. The algorithm prefers filling teams that are below `min_team_size` first (via a configurable boost).

---

## Project Model and `isSelected`

**Implementation:** There is no explicit `Project.isSelected` field. A project is treated as selected if it appears in the assignment map (`project_to_members`) with at least one member. Selection is derived from the assignment result, not stored separately.

---

## Data Handling

- **NetIDs not in file:** Preferred teammate references to NetIDs not in the CSV are flagged as warnings.
- **Project names:** Whitespace is normalized; distinct names (e.g., "EasyBook" vs "Project 22") remain distinct.
- **Empty cells:** Empty Project Pitched, rankings, or teammates are handled; students with no rankings are still assigned to a project.

---

## Configurability

All main parameters are configurable via:

- `config.example.json` (copy to `config.json` and edit)
- CLI overrides: `--min-team-size`, `--max-team-size`, `--preferred-team-size`, `--max-projects`

No hardcoded magic numbers in the algorithm.

---

## Google Sheets: Why Formulas Cannot Replace This

The assignment logic is a **constraint satisfaction and optimization** problem, not a simple lookup. Google Sheets functions (VLOOKUP, FILTER, etc.) can:

- Look up a value
- Filter rows by a condition
- Aggregate with SUM, COUNT, etc.

They cannot:

- Enforce global constraints (e.g., "each student on exactly one project", "each project 4–6 members")
- Enforce relationships like "each student has at least one preferred teammate on their project"
- Search over combinations of assignments to maximize a preference score

To implement this in Sheets, you would need **Google Apps Script** (JavaScript) to run the same greedy algorithm, or call an external API. Sheets would be suitable for input and output only; the core logic requires an algorithm, not formulas.
