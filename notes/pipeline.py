from __future__ import annotations
from pathlib import Path
from notes.mapping import MappingResolver
from notes import db
from notes.diff_extractor import has_changes, unified_diff
from notes.llm_client import generate
from notes.prompt_builder import build_prompt
from notes.patch_applier import apply_section_patch, extract_section
from notes.notes_git import commit_notes, ensure_notes_repo, notes_dir_for_project

def process_file_change(
  project_id: int,
  project_root: str | Path,
  relative_path: str,
  *,
  db_path: str | Path | None = None,
  template_path: str | Path | None = None,
  dry_run: bool = False,
) -> dict:
  """
  Full pipeline for one changed file.
  Returns {"status": "success"|"skipped"|"failed", "detail": "...", ...}
  """
  project_root = Path(project_root)
  relative_path = relative_path.replace("\\", "/")
  kwargs = {}
  if db_path is not None:
    kwargs["db_path"] = db_path

  result: dict = {
    "project_id": project_id,
    "file_path": relative_path,
    "status": "failed",
    "detail": "",
  }

  try:
    abs_path = project_root / relative_path
    if not abs_path.is_file():
      result["status"] = "skipped"
      result["detail"] = "file no longer exists"
      db.log_activity(project_id, relative_path, "skipped", result["detail"], **kwargs)
      return result

    new_content = abs_path.read_text(encoding="utf-8", errors="replace")
    old_content = db.get_snapshot(project_id, relative_path, **kwargs) or ""

    if not has_changes(old_content, new_content):
      result["status"] = "skipped"
      result["detail"] = "no content change vs last snapshot"
      db.log_activity(project_id, relative_path, "skipped", result["detail"], **kwargs)
      return result

    map_path = project_root / "notes-map.yml"
    if not map_path.exists():
      result["status"] = "skipped"
      result["detail"] = "no notes-map.yml in project root"
      db.log_activity(project_id, relative_path, "skipped", result["detail"], **kwargs)
      return result

    resolver = MappingResolver(map_path)
    mapping = resolver.resolve(relative_path)
    if mapping is None:
      result["status"] = "skipped"
      result["detail"] = "path ignored or unmatched by notes-map.yml"
      db.log_activity(project_id, relative_path, "skipped", result["detail"], **kwargs)
      if not dry_run:
        db.set_snapshot(project_id, relative_path, new_content, **kwargs)
      return result

    notes_file, section = mapping
    diff = unified_diff(old_content, new_content, relative_path)

    notes_abs = project_root / notes_file
    notes_content = notes_abs.read_text(encoding="utf-8") if notes_abs.exists() else ""
    current_section = extract_section(notes_content, section) or ""

    prompt = build_prompt(
      diff=diff,
      current_section=current_section,
      template_path=template_path,
    )

    if dry_run:
      result["status"] = "success"
      result["detail"] = "dry_run — prompt built, no LLM / write"
      result["prompt"] = prompt
      result["notes_file"] = notes_file
      result["section"] = section
      return result

    updated_body = generate(prompt)

    written = apply_section_patch(
      notes_file=notes_file,
      section=section,
      new_body=updated_body,
      project_root=project_root,
    )

    n_dir = notes_dir_for_project(project_root)
    ensure_notes_repo(n_dir)
    rel_in_notes = Path(notes_file)
    if rel_in_notes.parts and rel_in_notes.parts[0] == "notes":
      rel_in_notes = (
        Path(*rel_in_notes.parts[1:])
        if len(rel_in_notes.parts) > 1
        else Path(".")
      )
    committed = commit_notes(
      n_dir,
      message=f"notes-sync: update {section} from {relative_path}",
      paths=[str(rel_in_notes)] if str(rel_in_notes) != "." else None,
    )

    db.set_snapshot(project_id, relative_path, new_content, **kwargs)
    db.upsert_notes_index(project_id, notes_file, section, **kwargs)
    db.touch_project(project_id, **kwargs)
    db.log_activity(
      project_id,
      relative_path,
      "success",
        f"updated {notes_file}#{section}"
        + (" (committed)" if committed else " (no git change)"),
         **kwargs,
      )

    result["status"] = "success"
    result["detail"] = f"updated {written} section={section}"
    result["notes_file"] = notes_file
    result["section"] = section
    result["committed"] = committed
    return result

  except Exception as e:
    result["status"] = "failed"
    result["detail"] = str(e)
    try:
      db.log_activity(project_id, relative_path, "failed", str(e), **kwargs)
    except Exception:
      pass
    return result