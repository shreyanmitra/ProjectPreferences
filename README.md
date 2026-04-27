# CSE403 Project Team Assignment App

Assigns students to CSE403 project teams based on preferences (project rankings, pitched projects, preferred teammates).

## Repository layout

| Path | Purpose |
|------|---------|
| `app.py` | CLI entry point |
| `src/` | Models, CSV parsing, constraints, greedy + OR-Tools solvers, report/CSV output |
| `config.example.json` | Example settings (copy to `config.json` locally; `config.json` is gitignored) |
| `data/` | Sample and fixture CSVs (`sample_input.csv`, `sample_preferences_export.csv`, small OR-Tools vs greedy examples, etc.) |
| `DESIGN.md` | Algorithm and design notes |

Generated files from `-o` can go anywhere on your machine (for example next to your input CSV). The `output/` directory is gitignored if you use it locally.

## Requirements

- Python 3.8+
- pandas, ortools, rich (see `requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic

```bash
python app.py input.csv
```

Prints a styled report to stdout (colors, panels, tables). Use `--plain` for plain text.

**Windows:** UTF-8 is configured automatically. If you see encoding errors, set `$env:PYTHONIOENCODING="utf-8"` (PowerShell) before running.

### Output to file

```bash
python app.py input.csv -o report.txt
```

### CSV output

```bash
python app.py input.csv -o assignments.csv --format csv
```

### Configuration

**Config file (JSON):**

```bash
python app.py input.csv --config config.example.json
```

**CLI overrides:**

```bash
python app.py input.csv --min-team-size 4 --max-team-size 6 --max-projects 14
```

**Plain output** (no colors or formatting):

```bash
python app.py input.csv --plain
```

**Algorithm choice** (ortools or greedy; ortools is default):

```bash
python app.py input.csv --algorithm ortools
python app.py input.csv --algorithm greedy
python app.py input.csv --algorithm ortools --ortools-timeout 120
```

### Config options

| Option | Default | Description |
|--------|---------|-------------|
| `min_team_size` | 4 | Minimum students per team |
| `max_team_size` | 6 | Maximum students per team |
| `preferred_team_size` | 6 | Preferred team size |
| `max_projects` | 14 | Cap on number of projects to run (null = auto) |
| `rank_points` | [6,5,4,3,2] | Points for 1st–5th choice |
| `needs_members_boost` | 10 | Greedy: boost when project is below min size |
| `algorithm` | "ortools" | "ortools" or "greedy" |
| `ortools_timeout_seconds` | 60 | OR-Tools solver timeout (seconds) |

Copy `config.example.json` to `config.json` and edit as needed.

## Sample data

Bundled CSVs under `data/` are synthetic: a full-size preferences sheet (`sample_input.csv`, `sample_preferences_export.csv`) and smaller inputs for comparing algorithms (`sample_greedy_vs_ortools.csv`, `sample_ortools_success.csv`). To produce a report or assignment list from the full sample:

```bash
python app.py data/sample_input.csv -o report.txt
python app.py data/sample_input.csv -o assignments.csv --format csv
```

## UI Recommendation

**CLI** is the primary interface because:

- Staff run this periodically (once per quarter)
- Input is a single CSV; output is a report or CSV
- Easy to script and automate
- No hosting or deployment needed

**Website** is on the roadmap.

## Privacy and data

Input CSVs contain names and NetIDs. Do not commit real class rosters or production exports to a public repository. The bundled `data/` files use synthetic names and NetIDs for demonstration only.

## Copyright

(C) Shreyan Mitra
