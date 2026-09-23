from __future__ import annotations
from notes import db
from pathlib import Path
import argparse

def cmd_add(args):
  project_id = db.add_project(name=args.name, root_path=args.path)
  print(f"Registered '{args.name}' (id={project_id}) at {Path(args.path).resolve()}")
 
def cmd_list(args):
  projects = db.list_projects(status=args.status)
  if not projects:
    print("No projects registered yet.")
    return
  for p in projects:
    print(f"[{p['id']}] {p['name']:<25} {p['status']:<10} {p['root_path']}")
 
def _find_by_name(name: str) -> dict | None:
  for p in db.list_projects():
    if p["name"] == name:
      return p
  return None
 
def cmd_pause(args):
  project = _find_by_name(args.name)
  if not project:
    print(f"No project named '{args.name}' found.")
    return
  db.set_project_status(project["id"], "paused")
  print(f"Paused '{args.name}'.")
 
def cmd_finish(args):
  project = _find_by_name(args.name)
  if not project:
    print(f"No project named '{args.name}' found.")
    return
  db.set_project_status(project["id"], "finished")
  print(f"Marked '{args.name}' as finished. Its notes, snapshots, and lessons stay in the database.")
 
def main():
  parser = argparse.ArgumentParser(description="Manage projects tracked by notes-sync.")
  sub = parser.add_subparsers(dest="command", required=True)
  
  p_add = sub.add_parser("add", help="Register a new project")
  p_add.add_argument("path", help="Path to the project's root folder")
  p_add.add_argument("--name", required=True, help="Display name for the project")
  p_add.set_defaults(func=cmd_add)
  
  p_list = sub.add_parser("list", help="List registered projects")
  p_list.add_argument("--status", choices=["active", "paused", "finished"], default=None)
  p_list.set_defaults(func=cmd_list)
  
  p_pause = sub.add_parser("pause", help="Pause tracking for a project")
  p_pause.add_argument("name")
  p_pause.set_defaults(func=cmd_pause)
  
  p_finish = sub.add_parser("finish", help="Mark a project as finished (its data is kept)")
  p_finish.add_argument("name")
  p_finish.set_defaults(func=cmd_finish)
  
  args = parser.parse_args()
  args.func(args)
 
if __name__ == "__main__":
  main()
 