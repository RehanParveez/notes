import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.notes_git import commit_notes, ensure_notes_repo, notes_dir_for_project

def run():
  checks = {}
  with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "project"
    root.mkdir()
    n_dir = notes_dir_for_project(root)
    checks["notes dir path"] = n_dir == root / "notes"

    ensure_notes_repo(n_dir)
    checks["git init"] = (n_dir / ".git").is_dir()

    (n_dir / "inventory.md").write_text("hello\n", encoding="utf-8")
    checks["first commit"] = commit_notes(n_dir, "init") is True
    checks["noop commit"] = commit_notes(n_dir, "noop") is False

    (n_dir / "inventory.md").write_text("updated\n", encoding="utf-8")
    checks["path commit"] = commit_notes(
      n_dir, "update", paths=["inventory.md"]
    ) is True

    print("--- notes_git ---")
    all_ok = True
    for name, ok in checks.items():
      all_ok &= ok
      print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("ALL PASSED" if all_ok else "SOME FAILED")
    return all_ok

if __name__ == "__main__":
  run()