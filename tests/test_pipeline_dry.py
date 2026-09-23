import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes import db
from notes.pipeline import process_file_change


def run():
  checks = {}
  with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    db_path = tmp / "test.db"
    root = tmp / "proj"
    root.mkdir()

    (root / "notes-map.yml").write_text(
            """
mappings:
  - pattern: "apps/inventory/**/*.py"
    notes_file: "notes/inventory.md"
    section: "inventory-app"
ignore:
  - "notes/**"
  - ".git/**"
""",
      encoding="utf-8",
    )
    notes = root / "notes"
    notes.mkdir()
    (notes / "inventory.md").write_text(
      "<!-- section:inventory-app -->\nOld desc.\n<!-- /section:inventory-app -->\n",
      encoding="utf-8",
    )
    src = root / "apps" / "inventory" / "models.py"
    src.parent.mkdir(parents=True)
    src.write_text("def f():\n    return 1\n", encoding="utf-8")

    pid = db.add_project("Dry", str(root), db_path=db_path)

    r = process_file_change(
      pid, root, "apps/inventory/models.py", db_path=db_path, dry_run=True
    )
    checks["dry success"] = r["status"] == "success"
    checks["has prompt"] = "Diff of the code change" in r.get("prompt", "")
    checks["correct mapping"] = (
      r.get("notes_file") == "notes/inventory.md"
      and r.get("section") == "inventory-app"
    )
    checks["prompt has old section"] = "Old desc." in r.get("prompt", "")

    other = root / "apps" / "other" / "x.py"
    other.parent.mkdir(parents=True)
    other.write_text("x\n", encoding="utf-8")
    r2 = process_file_change(
      pid, root, "apps/other/x.py", db_path=db_path, dry_run=True
    )
    checks["unmapped skipped"] = r2["status"] == "skipped"

    r3 = process_file_change(
      pid, root, "notes/inventory.md", db_path=db_path, dry_run=True
    )
    checks["notes path skipped"] = r3["status"] == "skipped"

    print("--- pipeline dry_run ---")
    all_ok = True
    for name, ok in checks.items():
      all_ok &= ok
      print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("ALL PASSED" if all_ok else "SOME FAILED")
    return all_ok

if __name__ == "__main__":
  run()