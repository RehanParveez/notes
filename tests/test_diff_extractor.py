import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.diff_extractor import has_changes, unified_diff

def run():
  checks = {}

  old = "def calculate_yield(base, factor):\n    return base * factor\n"
  new = "def calculate_yield(base, factor):\n    adjusted = base * factor\n    return adjusted\n"

  checks["has_changes detects a real change"] = has_changes(old, new) is True
  checks["has_changes returns False for identical content"] = has_changes(old, old) is False

  diff = unified_diff(old, new, "apps/inventory/models.py")
  checks["diff is non-empty when content changed"] = len(diff) > 0
  checks["diff contains a correct position header"] = "@@ -1,2 +1,3 @@" in diff
  checks["diff shows the removed line"] = "-    return base * factor" in diff
  checks["diff shows both added lines"] = (
    "+    adjusted = base * factor" in diff and "+    return adjusted" in diff
  )

  empty_diff = unified_diff(old, old, "apps/inventory/models.py")
  checks["diff is empty when nothing changed"] = empty_diff == ""

  print("--- diff_extractor.py tests ---")
  all_passed = True
  for name, ok in checks.items():
    all_passed &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
  print(f"\ndiff_extractor.py: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
  return all_passed

if __name__ == "__main__":
    run()