import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.debounce import Debouncer

def run():
  checks = {}
  results: list[str] = []
  deb = Debouncer(delay=0.15)

  def cb(key, tag):
    results.append(f"{key}:{tag}")

  deb.call("a", cb, "v1")
  deb.call("a", cb, "v2")
  deb.call("a", cb, "v3")
  time.sleep(0.35)
  checks["collapses same key"] = results == ["a:v3"]

  results.clear()
  deb.call("a", cb, "x")
  deb.call("b", cb, "y")
  time.sleep(0.35)
  checks["independent keys"] = sorted(results) == ["a:x", "b:y"]

  results.clear()
  deb.call("c", cb, "z")
  deb.cancel("c")
  time.sleep(0.35)
  checks["cancel works"] = results == []

  print("--- debounce ---")
  all_ok = True
  for name, ok in checks.items():
    all_ok &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
  print("ALL PASSED" if all_ok else "SOME FAILED")
  return all_ok

if __name__ == "__main__":
    run()