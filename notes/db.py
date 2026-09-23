from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
 
DEFAULT_DB_PATH = Path.home() / ".notes" / "registry.db"
 
SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  root_path TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  last_active_at TEXT
);
 
CREATE TABLE IF NOT EXISTS snapshots (
  project_id INTEGER NOT NULL REFERENCES projects(id),
  file_path TEXT NOT NULL,
  content TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, file_path)
);
 
CREATE TABLE IF NOT EXISTS notes_index (
  project_id INTEGER NOT NULL REFERENCES projects(id),
  notes_file TEXT NOT NULL,
  section TEXT NOT NULL,
  last_updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, notes_file, section)
);
 
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  note_text TEXT NOT NULL,
  created_at TEXT NOT NULL
);
 
CREATE TABLE IF NOT EXISTS activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  file_path TEXT,
  status TEXT,
  detail TEXT,
  timestamp TEXT NOT NULL
);
"""
def _now() -> str:
  return datetime.now(timezone.utc).isoformat()
 
@contextmanager
def get_connection(db_path: str | Path = DEFAULT_DB_PATH):
  db_path = Path(db_path)
  db_path.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(db_path)
  conn.row_factory = sqlite3.Row
  conn.executescript(SCHEMA)
  try:
    yield conn
    conn.commit()
  finally:
    conn.close()
 
def add_project(name: str, root_path: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
  root_path = str(Path(root_path).resolve())
  with get_connection(db_path) as conn:
    existing = conn.execute(
      "SELECT id FROM projects WHERE root_path = ?", (root_path,)
    ).fetchone()
    if existing:
      return existing["id"]
  
    cur = conn.execute(
      "INSERT INTO projects (name, root_path, status, created_at, last_active_at) "
      "VALUES (?, ?, 'active', ?, ?)",
        (name, root_path, _now(), _now()),
    )
    return cur.lastrowid
 
def get_project_by_path(root_path: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
  root_path = str(Path(root_path).resolve())
  with get_connection(db_path) as conn:
    row = conn.execute(
     "SELECT * FROM projects WHERE root_path = ?", (root_path,)
    ).fetchone()
    return dict(row) if row else None
 
def list_projects(status: str | None = None, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
  with get_connection(db_path) as conn:
    if status:
      rows = conn.execute(
        "SELECT * FROM projects WHERE status = ? ORDER BY last_active_at DESC",
        (status,),
        ).fetchall()
    else:
      rows = conn.execute(
        "SELECT * FROM projects ORDER BY last_active_at DESC"
      ).fetchall()
    return [dict(r) for r in rows]
 
def set_project_status(project_id: int, status: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
  """status: 'active' | 'paused' | 'finished'"""
  with get_connection(db_path) as conn:
    conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
 
def touch_project(project_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
  with get_connection(db_path) as conn:
    conn.execute("UPDATE projects SET last_active_at = ? WHERE id = ?", (_now(), project_id))
 
def get_snapshot(project_id: int, file_path: str, db_path: str | Path = DEFAULT_DB_PATH) -> str | None:
  with get_connection(db_path) as conn:
    row = conn.execute(
      "SELECT content FROM snapshots WHERE project_id = ? AND file_path = ?",
      (project_id, file_path),
    ).fetchone()
    return row["content"] if row else None
 
def set_snapshot(project_id: int, file_path: str, content: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
  with get_connection(db_path) as conn:
    conn.execute(
      """
        INSERT INTO snapshots (project_id, file_path, content, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(project_id, file_path)
        DO UPDATE SET content = excluded.content, updated_at = excluded.updated_at
      """,
      (project_id, file_path, content, _now()),
    )
 
def add_lesson(project_id: int, note_text: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
   with get_connection(db_path) as conn:
    cur = conn.execute(
      "INSERT INTO lessons (project_id, note_text, created_at) VALUES (?, ?, ?)",
        (project_id, note_text, _now()),
    )
    return cur.lastrowid
 
def list_lessons(project_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
  with get_connection(db_path) as conn:
    rows = conn.execute(
      "SELECT * FROM lessons WHERE project_id = ? ORDER BY created_at DESC",
      (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]
 
def log_activity(
  project_id: int,
  file_path: str,
  status: str,
  detail: str = "",
  db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
  """status: 'success' | 'failed' | 'skipped'"""
  with get_connection(db_path) as conn:
    conn.execute(
      "INSERT INTO activity_log (project_id, file_path, status, detail, timestamp) "
      "VALUES (?, ?, ?, ?, ?)",
      (project_id, file_path, status, detail, _now()),
    )