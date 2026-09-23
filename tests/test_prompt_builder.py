import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from notes.prompt_builder import build_prompt

def run():
  sample_diff = """--- a/apps/inventory/models.py
+++ b/apps/inventory/models.py
@@ -68,7 +68,9 @@
 def calculate_yield(base, factor):
-    return base * factor
+    adjusted = apply_seasonal_correction(base, factor)
+    return adjusted
"""
  current_section = "- `calculate_yield` returns base * factor directly."
  prompt = build_prompt(sample_diff, current_section)

  checks = {
    "contains instructions": "Update ONLY this section" in prompt,
    "contains current section": "returns base * factor directly" in prompt,
    "contains the diff": "apply_seasonal_correction" in prompt,
    "has all three markers": all(
      marker in prompt
      for marker in [
        "--- Current section content ---",
        "--- Diff of the code change ---",
        "--- Updated section content ---",
      ]
    ),
  }

  empty_prompt = build_prompt(sample_diff, "")
  checks["handles empty section (new file case)"] = "empty — this is a new section" in empty_prompt

  print("--- prompt_builder.py tests ---")
  all_passed = True
  for name, ok in checks.items():
    all_passed &= ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    
  print(f"\nprompt_builder.py: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
  return all_passed


if __name__ == "__main__":
  run()