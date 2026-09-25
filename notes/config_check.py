from __future__ import annotations
from pathlib import Path
import yaml
from notes import db

REQUIRED_MAPPING_KEYS = {"pattern", "notes_file", "section"}

def validate_project(project: dict) -> list[str]:
  """Return a list of problem strings for one project row. Empty list = OK."""
  problems: list[str] = []
  root = Path(project["root_path"])

  if not root.is_dir():
    problems.append(f"root path does not exist: {root}")
    return problems

  map_path = root / "notes-map.yml"
  if not map_path.exists():
    problems.append(f"missing notes-map.yml at {map_path}")
    return problems

  try:
    raw = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
  except yaml.YAMLError as e:
    problems.append(f"notes-map.yml is not valid YAML: {e}")
    return problems

  mappings = raw.get("mappings", [])
  if not mappings:
    problems.append("notes-map.yml has no 'mappings' entries")

  for i, m in enumerate(mappings):
    missing = REQUIRED_MAPPING_KEYS - set(m.keys())
    if missing:
      problems.append(f"mapping #{i} is missing keys: {sorted(missing)}")

  return problems

def validate_all(status: str = "active", db_path: str | None = None) -> dict[str, list[str]]:
  """Returns {project_name: [problems]} — only entries that have problems."""
  kwargs = {"db_path": db_path} if db_path else {}
  projects = db.list_projects(status=status, **kwargs)
  report: dict[str, list[str]] = {}
  for p in projects:
    problems = validate_project(p)
    if problems:
      report[p["name"]] = problems
  return report