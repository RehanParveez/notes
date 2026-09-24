from __future__ import annotations
import argparse
from pathlib import Path
from notes import db

def _find_by_name(name: str, db_path: str | Path | None = None) -> dict | None:
  kwargs = {"db_path": db_path} if db_path is not None else {}
  for p in db.list_projects(**kwargs):
    if p["name"] == name:
      return p
  return None

def cmd_status(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}

  if args.lessons:
    project = _find_by_name(args.lessons, **kwargs)
    if not project:
      print(f"No project named '{args.lessons}' found.")
      return
    lessons = db.list_lessons(project["id"], **kwargs)
    if not lessons:
      print(f"No lessons recorded for '{project['name']}'.")
      return
    print(f"Lessons for '{project['name']}' (id={project['id']}):\n")
    for i, les in enumerate(lessons, 1):
      print(f"  {i}. [{les['created_at']}] {les['note_text']}")
    return

  if args.project:
    project = _find_by_name(args.project, **kwargs)
    if not project:
            print(f"No project named '{args.project}' found.")
            return
    print(f"Project: {project['name']}")
    print(f"  id:            {project['id']}")
    print(f"  status:        {project['status']}")
    print(f"  root:          {project['root_path']}")
    print(f"  created_at:    {project['created_at']}")
    print(f"  last_active:   {project['last_active_at']}")

    with db.get_connection(**kwargs) as conn:
      rows = conn.execute(
        "SELECT file_path, status, detail, timestamp "
        "FROM activity_log WHERE project_id = ? "
        "ORDER BY timestamp DESC LIMIT 15",
          (project["id"],),
      ).fetchall()
    if rows:
      print("\n  Recent activity:")
      for r in rows:
        path = r["file_path"] or "(none)"
        print(f"    [{r['timestamp']}] {r['status']:<8} {path}  {r['detail'] or ''}")
    else:
      print("\n  No activity logged yet.")

    lessons = db.list_lessons(project["id"], **kwargs)
    if lessons:
      print(f"\n  Lessons ({len(lessons)}):")
      for les in lessons[:5]:
        print(f"    - {les['note_text'][:80]}")
      if len(lessons) > 5:
        print(f"    ... and {len(lessons) - 5} more (use --lessons)")
    return

  projects = db.list_projects(**kwargs)
  if not projects:
    print("No projects registered yet.")
    return

  print(f"{'ID':<4} {'Name':<25} {'Status':<10} {'Last active':<28} Root")
  print("-" * 100)
  for p in projects:
    print(
      f"{p['id']:<4} {p['name']:<25} {p['status']:<10} "
      f"{(p['last_active_at'] or '-'):<28} {p['root_path']}"
    )

def cmd_add_lesson(args) -> None:
  kwargs = {"db_path": args.db} if args.db else {}
  project = _find_by_name(args.project, **kwargs)
  if not project:
    print(f"No project named '{args.project}' found.")
    return
  lesson_id = db.add_lesson(project["id"], args.text, **kwargs)
  print(f"Added lesson #{lesson_id} to '{project['name']}'.")

def main() -> None:
  parser = argparse.ArgumentParser(description="Query notes-sync status and lessons.")
  parser.add_argument("--db", default=None, help="Override DB path")
  sub = parser.add_subparsers(dest="command")

  parser.add_argument("--project", default=None, help="Detail for one project by name")
  parser.add_argument("--lessons", default=None, help="List lessons for a project by name")

  p_lesson = sub.add_parser("add-lesson", help="Manually add a lesson for a project")
  p_lesson.add_argument("--project", required=True, help="Project name")
  p_lesson.add_argument("--text", required=True, help="Lesson text")
  p_lesson.add_argument("--db", default=None)
  p_lesson.set_defaults(func=cmd_add_lesson)
  args = parser.parse_args()
  if getattr(args, "command", None) == "add-lesson":
    args.func(args)
  else:
    cmd_status(args)

if __name__ == "__main__":
    main()