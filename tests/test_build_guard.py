import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.bulk_guard import BulkGuard

def run():
  checks = {}
  guard = BulkGuard(window_seconds=0.4, threshold=3, cooldown_seconds=0.6)
  checks["single file not bulk"] = guard.record(1, "a.py") is False
  checks["second different file still under threshold"] = guard.record(1, "b.py") is False

  checks["third file triggers bulk"] = guard.record(1, "c.py") is True

  flagged = guard.consume_flagged(1)
  checks["flagged contains the three paths"] = flagged == {"a.py", "b.py", "c.py"}
  checks["still in cooldown"] = guard.record(1, "d.py") is True
  checks["is_in_cooldown True"] = guard.is_in_cooldown(1) is True

  time.sleep(0.7)
  checks["cooldown expired"] = guard.is_in_cooldown(1) is False
  checks["after cooldown normal again"] = guard.record(1, "e.py") is False

  guard2 = BulkGuard(window_seconds=0.3, threshold=2)
  checks["project 1 alone not bulk"] = guard2.record(10, "x.py") is False
  checks["project 2 alone not bulk"] = guard2.record(20, "y.py") is False
  checks["project 1 second file is bulk"] = guard2.record(10, "z.py") is True

  print("--- bulk_guard ---")
  all_ok = True
  for name, ok in checks.items():
    all_ok &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
  print("ALL PASSED" if all_ok else "SOME FAILED")
  return all_ok

if __name__ == "__main__":
  run()