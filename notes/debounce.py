from __future__ import annotations
import threading
from typing import Callable

class Debouncer:
  def __init__(self, delay: float = 1.0):
    self.delay = delay
    self._timers: dict[str, threading.Timer] = {}
    self._lock = threading.Lock()

  def call(self, key: str, callback: Callable[..., None], *args, **kwargs) -> None:
    with self._lock:
      existing = self._timers.pop(key, None)
      if existing is not None:
        existing.cancel()

      def _fire():
        with self._lock:
          self._timers.pop(key, None)
        callback(key, *args, **kwargs)

      timer = threading.Timer(self.delay, _fire)
      timer.daemon = True
      self._timers[key] = timer
      timer.start()

  def cancel(self, key: str) -> None:
    with self._lock:
      existing = self._timers.pop(key, None)
      if existing is not None:
        existing.cancel()

  def cancel_all(self) -> None:
    with self._lock:
      for t in self._timers.values():
        t.cancel()
      self._timers.clear()

  def pending_count(self) -> int:
    with self._lock:
      return len(self._timers)