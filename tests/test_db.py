import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes import db

def run():
  checks = {}
  with tempfile.TemporaryDirectory() as tmp:
    db_path = Path(tmp) / "test_registry.db"

    project_id = db.add_project("Test Project", str(Path(tmp) / "project"), db_path=db_path)
    checks["add_project returns an id"] = isinstance(project_id, int)

    same_id = db.add_project("Test Project", str(Path(tmp) / "project"), db_path=db_path)
    checks["re-adding same path is a no-op"] = same_id == project_id

    projects = db.list_projects(db_path=db_path)
    checks["list_projects sees it"] = len(projects) == 1 and projects[0]["name"] == "Test Project"

    db.set_project_status(project_id, "paused", db_path=db_path)
    paused = db.list_projects(status="paused", db_path=db_path)
    checks["set_project_status works"] = len(paused) == 1 and paused[0]["id"] == project_id

    missing = db.get_snapshot(project_id, "some/file.py", db_path=db_path)
    checks["get_snapshot returns None when unseen"] = missing is None

    db.set_snapshot(project_id, "some/file.py", "print('v1')", db_path=db_path)
    v1 = db.get_snapshot(project_id, "some/file.py", db_path=db_path)
    checks["set_snapshot then get_snapshot round-trips"] = v1 == "print('v1')"

    db.set_snapshot(project_id, "some/file.py", "print('v2')", db_path=db_path)
    v2 = db.get_snapshot(project_id, "some/file.py", db_path=db_path)
    checks["set_snapshot overwrites, not duplicates"] = v2 == "print('v2')"
        
    db.add_lesson(project_id, "Remember to check timezone handling here.", db_path=db_path)
    lessons = db.list_lessons(project_id, db_path=db_path)
    checks["add_lesson + list_lessons works"] = (
      len(lessons) == 1 and "timezone" in lessons[0]["note_text"]
    )

    try:
      db.log_activity(project_id, "some/file.py", "success", "manual test", db_path=db_path)
      checks["log_activity doesn't raise"] = True
    except Exception:
      checks["log_activity doesn't raise"] = False

  print("--- db.py tests ---")
  all_passed = True
  for name, ok in checks.items():
    all_passed &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
  print(f"\ndb.py: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
  return all_passed

if __name__ == "__main__":
  run()