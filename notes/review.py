from __future__ import annotations
from pathlib import Path
from notes import db
import argparse
from notes.patch_applier import apply_section_patch
from notes.notes_git import commit_notes, ensure_notes_repo, notes_dir_for_project

def _project_root(project_id: int, db_path: str | None) -> Path | None:
  kwargs = {"db_path": db_path} if db_path else {}
  p = db.get_project_by_id(project_id, **kwargs)
  return Path(p["root_path"]) if p else None

def cmd_list(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}
  patches = db.list_pending_patches(project_id=args.project_id, status="pending", **kwargs)
  if not patches:
    print("No pending patches.")
    return
  for p in patches:
    print(f"[{p['id']}] project={p['project_id']} {p['file_path']} -> {p['notes_file']}#{p['section']}  ({p['created_at']})")

def cmd_show(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}
  patch = db.get_pending_patch(args.id, **kwargs)
  if not patch:
    print(f"No pending patch #{args.id}")
    return
  print(f"Patch #{patch['id']}  project_id={patch['project_id']}")
  print(f"Source file: {patch['file_path']}")
  print(f"Target: {patch['notes_file']}#{patch['section']}\n")
  print("--- diff ---")
  print(patch["diff"])
  print("\n--- proposed section body ---")
  print(patch["proposed_body"])

def cmd_approve(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}
  patch = db.get_pending_patch(args.id, **kwargs)
  if not patch or patch["status"] != "pending":
    print(f"No pending patch #{args.id}")
    return
  root = _project_root(patch["project_id"], args.db)
  if root is None:
    print("Project no longer registered.")
    return

  apply_section_patch(
    notes_file=patch["notes_file"],
    section=patch["section"],
    new_body=patch["proposed_body"],
    project_root=root,
  )
  n_dir = notes_dir_for_project(root)
  ensure_notes_repo(n_dir)
  rel = Path(patch["notes_file"])
  if rel.parts and rel.parts[0] == "notes":
    rel = Path(*rel.parts[1:]) if len(rel.parts) > 1 else Path(".")
  commit_notes(
    n_dir,
    message=f"notes-sync: approved review patch #{patch['id']} ({patch['section']} from {patch['file_path']})",
    paths=[str(rel)] if str(rel) != "." else None,
  )
  db.resolve_pending_patch(args.id, "approved", **kwargs)
  db.upsert_notes_index(patch["project_id"], patch["notes_file"], patch["section"], **kwargs)
  print(f"Approved and applied patch #{args.id}.")

def cmd_reject(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}
  patch = db.get_pending_patch(args.id, **kwargs)
  if not patch or patch["status"] != "pending":
    print(f"No pending patch #{args.id}")
    return
  db.resolve_pending_patch(args.id, "rejected", **kwargs)
  print(f"Rejected patch #{args.id}.")

def main() -> None:
  parser = argparse.ArgumentParser(description="Review queued notes-sync patches.")
  parser.add_argument("--db", default=None)
  sub = parser.add_subparsers(dest="command", required=True)

  p_list = sub.add_parser("list", help="List pending patches")
  p_list.add_argument("--project-id", type=int, default=None, dest="project_id")
  p_list.set_defaults(func=cmd_list)

  p_show = sub.add_parser("show", help="Show a pending patch in full")
  p_show.add_argument("id", type=int)
  p_show.set_defaults(func=cmd_show)

  p_approve = sub.add_parser("approve", help="Apply a pending patch")
  p_approve.add_argument("id", type=int)
  p_approve.set_defaults(func=cmd_approve)

  p_reject = sub.add_parser("reject", help="Discard a pending patch")
  p_reject.add_argument("id", type=int)
  p_reject.set_defaults(func=cmd_reject)

  args = parser.parse_args()
  args.func(args)

if __name__ == "__main__":
  main()