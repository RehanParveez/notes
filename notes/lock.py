from __future__ import annotations
from pathlib import Path
from notes.db import DEFAULT_DB_PATH

def _lock_path(db_path: str | Path | None = None) -> Path:
  base = Path(db_path).parent if db_path else DEFAULT_DB_PATH.parent
  return base / "PAUSED"

def pause(db_path: str | Path | None = None) -> None:
  path = _lock_path(db_path)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.touch()

def resume(db_path: str | Path | None = None) -> None:
  path = _lock_path(db_path)
  if path.exists():
    path.unlink()

def is_paused(db_path: str | Path | None = None) -> bool:
  return _lock_path(db_path).exists()