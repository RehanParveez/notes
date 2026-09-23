import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.mapping import MappingResolver
 
MAPPING_CONFIG = Path(__file__).resolve().parent.parent / "notes-map.yml"
 
def run():
  resolver = MappingResolver(MAPPING_CONFIG)
 
  cases = [
    ("apps/inventory/models.py", ("notes/inventory.md", "inventory-app")),
    ("apps/inventory/sub/deep/models.py", ("notes/inventory.md", "inventory-app")),
    ("apps/orders/views.py", ("notes/orders.md", "orders-app")),
    ("frontend/src/components/Button.tsx", ("notes/frontend.md", "components")),
    ("frontend/src/components/ui/Modal.tsx", ("notes/frontend.md", "components")),
    ("apps/inventory/migrations/0001_initial.py", None),
    ("poetry.lock", None),
    ("notes/inventory.md", None),
    ("apps/unmapped/thing.py", None),
  ]
 
  print("--- mapping.py tests ---")
  all_passed = True
  for path, expected in cases:
    result = resolver.resolve(path)
    ok = result == expected
    all_passed &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {path!r:50} -> {result} (expected {expected})")
 
  print(f"\nmapping.py: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
  return all_passed
 
if __name__ == "__main__":
  run()
 