import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.patch_applier import apply_section_patch, extract_section, list_sections

def run():
  checks = {}
  with tempfile.TemporaryDirectory() as tmp:
    notes = Path(tmp) / "notes" / "inventory.md"

    apply_section_patch(notes, "inventory-app", "First version.")
    content = notes.read_text(encoding="utf-8")
    checks["creates markers"] = (
      "<!-- section:inventory-app -->" in content
      and "<!-- /section:inventory-app -->" in content
    )
    checks["extract body"] = extract_section(content, "inventory-app") == "First version."
    checks["list sections"] = list_sections(content) == ["inventory-app"]

    notes.write_text(
      "# Header\n\n" + content + "\nFooter\n", encoding="utf-8"
    )
    apply_section_patch(notes, "inventory-app", "Updated body.")
    content2 = notes.read_text(encoding="utf-8")
    checks["preserves outside text"] = (
      content2.startswith("# Header") and "Footer" in content2
    )
    checks["body replaced"] = (
      extract_section(content2, "inventory-app") == "Updated body."
    )
    checks["old body gone"] = "First version." not in content2

    apply_section_patch(notes, "orders-app", "Orders body.")
    content3 = notes.read_text(encoding="utf-8")
    checks["two sections"] = (
      extract_section(content3, "inventory-app") == "Updated body."
      and extract_section(content3, "orders-app") == "Orders body."
    )
    checks["missing is None"] = extract_section(content3, "nope") is None
    checks["no tmp left"] = not any(notes.parent.glob("*.tmp"))

    print("--- patch_applier ---")
    all_ok = True
    for name, ok in checks.items():
      all_ok &= ok
      print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("ALL PASSED" if all_ok else "SOME FAILED")
    return all_ok

if __name__ == "__main__":
    run()