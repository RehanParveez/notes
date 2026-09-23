from __future__ import annotations
import os
import re
from pathlib import Path

SECTION_OPEN = re.compile(r"<!--\s*section:([^\s]+)\s*-->", re.IGNORECASE)
SECTION_CLOSE = re.compile(r"<!--\s*/section:([^\s]+)\s*-->", re.IGNORECASE)

def _read(path: Path) -> str:
  if not path.exists():
    return ""
  return path.read_text(encoding="utf-8", newline="")

def _write_atomic(path: Path, content: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_suffix(path.suffix + ".tmp")
  with open(tmp, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
  os.replace(tmp, path)

def extract_section(notes_content: str, section: str) -> str | None:
  open_pat = re.compile(
    rf"<!--\s*section:{re.escape(section)}\s*-->", re.IGNORECASE
  )
  close_pat = re.compile(
    rf"<!--\s*/section:{re.escape(section)}\s*-->", re.IGNORECASE
  )
  open_m = open_pat.search(notes_content)
  if not open_m:
    return None
  close_m = close_pat.search(notes_content, open_m.end())
  if not close_m:
    return notes_content[open_m.end():].strip()
  return notes_content[open_m.end(): close_m.start()].strip()

def apply_section_patch(
  notes_file: str | Path,
  section: str,
  new_body: str,
  project_root: str | Path | None = None,
) -> Path: 
  notes_path = Path(notes_file)
  if project_root is not None and not notes_path.is_absolute():
        notes_path = Path(project_root) / notes_path

  current = _read(notes_path)
  new_body = new_body.strip()

  open_pat = re.compile(
    rf"(<!--\s*section:{re.escape(section)}\s*-->)", re.IGNORECASE
  )
  close_pat = re.compile(
    rf"(<!--\s*/section:{re.escape(section)}\s*-->)", re.IGNORECASE
  )

  open_m = open_pat.search(current)
  if open_m:
    close_m = close_pat.search(current, open_m.end())
    if close_m:
      updated = (
        current[: open_m.end()]
        + "\n"
        + new_body
        + "\n"
        + current[close_m.start():]
      )
    else:
      updated = (
        current[: open_m.end()]
        + "\n"
        + new_body
        + "\n"
        + f"<!-- /section:{section} -->\n"
      )
  else:
    block = (
      f"\n<!-- section:{section} -->\n"
      f"{new_body}\n"
      f"<!-- /section:{section} -->\n"
    )
    if current and not current.endswith("\n"):
      current += "\n"
    updated = current + block
  _write_atomic(notes_path, updated)
  return notes_path.resolve()

def list_sections(notes_content: str) -> list[str]:
  return SECTION_OPEN.findall(notes_content)