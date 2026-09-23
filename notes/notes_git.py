from __future__ import annotations
import subprocess
from pathlib import Path

def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
  return subprocess.run(
    args, cwd=str(cwd), capture_output=True, text=True, check=check
  )

def ensure_notes_repo(notes_dir: str | Path) -> Path:
  notes_dir = Path(notes_dir)
  notes_dir.mkdir(parents=True, exist_ok=True)
  if not (notes_dir / ".git").exists():
    _run(["git", "init"], cwd=notes_dir)
    _run(["git", "config", "user.email", "notes-sync@local"], cwd=notes_dir)
    _run(["git", "config", "user.name", "notes-sync"], cwd=notes_dir)
  return notes_dir.resolve()

def commit_notes(
  notes_dir: str | Path,
  message: str,
  paths: list[str] | None = None,
) -> bool:
  """Stage + commit. Returns True if a commit was created."""
  notes_dir = ensure_notes_repo(notes_dir)
  if paths:
    for p in paths:
      _run(["git", "add", "--", p], cwd=notes_dir, check=False)
  else:
    _run(["git", "add", "-A"], cwd=notes_dir, check=False)

  status = _run(["git", "status", "--porcelain"], cwd=notes_dir, check=False)
  if not status.stdout.strip():
    return False

  _run(["git", "commit", "-m", message], cwd=notes_dir)
  return True

def notes_dir_for_project(project_root: str | Path) -> Path:
    return Path(project_root) / "notes"