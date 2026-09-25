from __future__ import annotations
import argparse
import logging
from notes.watcher import MultiProjectWatcher
from pathlib import Path
import sys
from notes import db
from notes.pipeline import process_file_change
from notes.config_check import validate_all
from notes.lock import pause as lock_pause, resume as lock_resume

def setup_logging(verbose: bool = False) -> None:
  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
  )

def cmd_watch(args) -> None:
  setup_logging(args.verbose)
  report = validate_all()
  for name, problems in report.items():
    for p in problems:
      logging.getLogger("notes.main").warning("[%s] %s", name, p)
  watcher = MultiProjectWatcher(
    debounce_seconds=args.debounce,
    template_path=args.template,
  )
  print("notes-sync watcher running. Ctrl+C to stop.")
  watcher.run_forever()

def cmd_once(args) -> None:
  setup_logging(args.verbose)
  project_root = Path(args.project).resolve()
  rel = args.file.replace("\\", "/")

  project = db.get_project_by_path(str(project_root))
  if not project:
    print(f"Project not registered: {project_root}")
    print("Register first: python -m notes.registry add <path> --name 'Name'")
    sys.exit(1)

  result = process_file_change(
    project_id=project["id"],
    project_root=project_root,
    relative_path=rel,
    template_path=args.template,
    dry_run=args.dry_run,
  )
  print(f"status:  {result['status']}")
  print(f"detail:  {result.get('detail', '')}")
  if result.get("prompt"):
    print("\n--- prompt ---\n")
    print(result["prompt"])

def cmd_validate(args) -> None:
  setup_logging(args.verbose)
  report = validate_all()
  if not report:
    print("All active projects look good.")
    return
  print("Problems found:\n")
  for name, problems in report.items():
    print(f"{name}:")
    for p in problems:
      print(f"  - {p}")
      
def cmd_pause(args) -> None:
  lock_pause()
  print("notes-sync paused globally — file changes will be ignored until you resume.")

def cmd_resume(args) -> None:
  lock_resume()
  print("notes-sync resumed.")

def main() -> None:
  parser = argparse.ArgumentParser(description="notes-sync")
  parser.add_argument("--debounce", type=float, default=1.0)
  parser.add_argument("--template", default=None)
  parser.add_argument("-v", "--verbose", action="store_true")
  sub = parser.add_subparsers(dest="command")
  p_once = sub.add_parser("once", help="Process one file once")
  p_once.add_argument("--project", required=True)
  p_once.add_argument("--file", required=True)
  p_once.add_argument("--dry-run", action="store_true")
  p_once.add_argument("--template", default=None)
  p_once.add_argument("-v", "--verbose", action="store_true")
  p_once.set_defaults(func=cmd_once)

  p_validate = sub.add_parser("validate", help="Check all active projects' notes-map.yml")
  p_pause = sub.add_parser("pause", help="Globally pause all AI processing")
  p_pause.set_defaults(func=cmd_pause)

  p_resume = sub.add_parser("resume", help="Resume after a global pause")
  p_resume.set_defaults(func=cmd_resume)
  p_validate.add_argument("-v", "--verbose", action="store_true")
  p_validate.set_defaults(func=cmd_validate)

  args = parser.parse_args()
  command = getattr(args, "command", None)
  if command in ("once", "pause", "resume", "validate"):
    args.func(args)
  else:
    cmd_watch(args)

if __name__ == "__main__":
  main()