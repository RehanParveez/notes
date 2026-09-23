from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
import yaml
 
def _pattern_to_regex(pattern: str) -> re.Pattern:
  """
  Translate a gitignore-style glob pattern into a compiled regex that
  matches a forward-slash relative path.
 
  - '**/'  -> matches zero or more path segments
  - '**'   -> matches anything, including slashes
  - '*'    -> matches anything except a slash
  - '?'    -> matches a single non-slash character
  """
  pattern = pattern.replace("\\", "/")
  parts: list[str] = []
  i, n = 0, len(pattern)
  while i < n:
    if pattern[i:i + 3] == "**/":
      parts.append("(?:.*/)?")
      i += 3
    elif pattern[i:i + 2] == "**":
      parts.append(".*")
      i += 2
    elif pattern[i] == "*":
      parts.append("[^/]*")
      i += 1
    
    elif pattern[i] == "?":
      parts.append("[^/]")
      i += 1
    else:
      parts.append(re.escape(pattern[i]))
      i += 1
  return re.compile("^" + "".join(parts) + "$")
 
@dataclass
class MappingRule:
  pattern: str
  notes_file: str
  section: str
  _regex: re.Pattern = field(init=False, repr=False)
 
  def __post_init__(self):
    self._regex = _pattern_to_regex(self.pattern)
    
  def matches(self, relative_path: str) -> bool:
    return bool(self._regex.match(relative_path))

class MappingResolver:
  def __init__(self, config_path: str | Path):
    self.config_path = Path(config_path)
    with open(self.config_path, "r", encoding="utf-8") as f:
      raw = yaml.safe_load(f) or {}
            
    self.rules = [
      MappingRule(pattern=m["pattern"], notes_file=m["notes_file"], section=m["section"])
      for m in raw.get("mappings", [])
    ]
    self._ignore_regexes = [_pattern_to_regex(p) for p in raw.get("ignore", [])]
 
  def is_ignored(self, relative_path: str) -> bool:
    relative_path = relative_path.replace("\\", "/")
    return any(rx.match(relative_path) for rx in self._ignore_regexes)

  def resolve(self, relative_path: str) -> tuple[str, str] | None:
    relative_path = relative_path.replace("\\", "/")
    if self.is_ignored(relative_path):
      return None
    for rule in self.rules:
      if rule.matches(relative_path):
        return rule.notes_file, rule.section
    return None