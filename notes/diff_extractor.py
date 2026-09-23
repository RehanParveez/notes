from __future__ import annotations
import difflib
 
def unified_diff(
  old_content: str,
  new_content: str,
  file_path: str,
  context_lines: int = 3,
) -> str:
  old_lines = old_content.splitlines(keepends=True)
  new_lines = new_content.splitlines(keepends=True)
 
  diff_lines = difflib.unified_diff(
    old_lines,
    new_lines,
    fromfile=f"a/{file_path}",
    tofile=f"b/{file_path}",
    n=context_lines,
   )
  return "".join(diff_lines)
 
def has_changes(old_content: str, new_content: str) -> bool:
  return old_content != new_content
 