from __future__ import annotations
import threading
from dataclasses import dataclass, field
import time
from collections import deque

@dataclass
class BulkGuard:
  """
  Detects a burst of many distinct files changing in a short window
  (branch switch, mass refactor, git checkout, etc.) and suppresses
  per-file AI processing in favour of a single "flag for review" action.

  Usage:
    guard = BulkGuard(window_seconds=3.0, threshold=8)

    # On every raw file event (before debounce):
    if guard.record(project_id, relative_path):
      # True → this event is part of a bulk change; skip AI
      ...
    else:
      # Normal path → continue to debouncer / pipeline
      ...
  """

  window_seconds: float = 3.0
  threshold: int = 8          
  cooldown_seconds: float = 10.0 

  _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
  _events: dict[int, deque] = field(default_factory=dict, init=False, repr=False)
  _cooldown_until: dict[int, float] = field(default_factory=dict, init=False, repr=False)
  _flagged: dict[int, set[str]] = field(default_factory=dict, init=False, repr=False)

  def record(self, project_id: int, relative_path: str) -> bool:
    """
    Record a file-change event.

    Returns True if this event should be treated as part of a bulk
    change (caller should skip the AI pipeline and only log a flag).
    Returns False for normal single-file changes.
    """
    now = time.monotonic()
    relative_path = relative_path.replace("\\", "/")

    with self._lock:
      if now < self._cooldown_until.get(project_id, 0.0):
        return True

      events = self._events.setdefault(project_id, deque())
      events.append((now, relative_path))

      cutoff = now - self.window_seconds
      while events and events[0][0] < cutoff:
        events.popleft()

      distinct = {p for _, p in events}

      if len(distinct) >= self.threshold:
        self._cooldown_until[project_id] = now + self.cooldown_seconds
        flagged = self._flagged.setdefault(project_id, set())
        flagged.update(distinct)
        events.clear()
        return True

      return False

  def is_in_cooldown(self, project_id: int) -> bool:
    with self._lock:
      return time.monotonic() < self._cooldown_until.get(project_id, 0.0)

  def consume_flagged(self, project_id: int) -> set[str]:
    """Return and clear the set of paths that were part of the last bulk event."""
    with self._lock:
      return self._flagged.pop(project_id, set())

  def reset(self, project_id: int | None = None) -> None:
    with self._lock:
      if project_id is None:
        self._events.clear()
        self._cooldown_until.clear()
        self._flagged.clear()
      else:
        self._events.pop(project_id, None)
        self._cooldown_until.pop(project_id, None)
        self._flagged.pop(project_id, None)