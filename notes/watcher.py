from __future__ import annotations
import logging
from pathlib import Path
from notes.debounce import Debouncer
import threading
import time
from notes.pipeline import process_file_change
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from notes import db
from notes.bulk_guard import BulkGuard

log = logging.getLogger("notes.watcher")

class _ProjectHandler(FileSystemEventHandler):
  def __init__(
    self,
    project_id: int,
    project_root: Path,
    debouncer: Debouncer,
    bulk_guard: BulkGuard,
    db_path: str | Path | None = None,
    template_path: str | Path | None = None,
  ):
    super().__init__()

    self.project_id = project_id
    self.project_root = project_root
    self.debouncer = debouncer
    self.bulk_guard = bulk_guard
    self.db_path = db_path
    self.template_path = template_path

  def _relative_path(self, path: str | Path) -> str | None:
    try:
      relative = Path(path).resolve().relative_to(
        self.project_root.resolve()
      )
    except ValueError:
      return None

    return relative.as_posix()

  def _schedule(self, path: str | Path) -> None:
    relative_path = self._relative_path(path)

    if relative_path is None:
      return

    absolute_path = self.project_root / relative_path

    if not absolute_path.is_file():
      return
    
    if self.bulk_guard.record(self.project_id, relative_path):
  
      flagged = self.bulk_guard.consume_flagged(self.project_id)
      if flagged:
        detail = f"bulk change detected ({len(flagged)} files) — skipped AI, review manually"
        try:
          kwargs = {"db_path": self.db_path} if self.db_path is not None else {}
          db.log_activity(
            self.project_id,
            "(bulk)",
            "skipped",
            detail,
            **kwargs,
          )
          log.warning(
            "Bulk change project_id=%s files=%d — AI skipped",
              self.project_id,
              len(flagged),
          )
        except Exception:
          log.exception("Failed to log bulk-change event")
      return

    key = f"{self.project_id}:{relative_path}"
    self.debouncer.call(key, self._process_change, relative_path,
    )

  def _process_change(self, _key: str, relative_path: str) -> None:
    if self.bulk_guard.is_in_cooldown(self.project_id):
      log.debug(
        "Dropping debounced event during bulk cooldown project_id=%s file=%s",
        self.project_id,
        relative_path,
      )
      return

    try: 
      result = process_file_change( 
        project_id=self.project_id, 
        project_root=self.project_root, 
        relative_path=relative_path, 
        db_path=self.db_path, 
        template_path=self.template_path, 
      ) 
 
      log.info( 
        "Processed project_id=%s file=%s status=%s detail=%s", 
        self.project_id, 
        relative_path, 
        result.get("status"), 
        result.get("detail"), 
      ) 
 
    except Exception: 
      log.exception( 
        "Unhandled error processing project_id=%s file=%s", 
        self.project_id, 
        relative_path, 
      ) 

  def on_created(self, event) -> None:
    if event.is_directory:
      return

    log.debug(
      "File created project_id=%s path=%s",
      self.project_id,
      event.src_path,
    )

    self._schedule(event.src_path)

  def on_modified(self, event) -> None:
    if event.is_directory:
      return

    log.debug(
      "File modified project_id=%s path=%s",
      self.project_id,
      event.src_path,
    )

    self._schedule(event.src_path)

  def on_moved(self, event) -> None:
    if event.is_directory:
      return

    log.debug(
      "File moved project_id=%s from=%s to=%s",
      self.project_id,
      event.src_path,
      event.dest_path,
    )

    self._schedule(event.dest_path)

class MultiProjectWatcher:
  def __init__(
    self,
    debounce_seconds: float = 1.0,
    bulk_window: float = 3.0, 
    bulk_threshold: int = 8, 
    db_path: str | Path | None = None,
    template_path: str | Path | None = None,
    refresh_interval: float = 30.0,
  ):
    self.debounce_seconds = debounce_seconds
    self.db_path = db_path
    self.template_path = template_path
    self.refresh_interval = refresh_interval
    self._observer = Observer()
    self._debouncer = Debouncer(delay=debounce_seconds)
    self._bulk_guard = BulkGuard(window_seconds=bulk_window, threshold=bulk_threshold, 
    ) 
    self._watched: dict[int, object] = {}
    self._lock = threading.Lock()
    self._stop = threading.Event()
    self._refresh_thread: threading.Thread | None = None

  def _db_kwargs(self) -> dict:
    return {"db_path": self.db_path} if self.db_path is not None else {}

  def _sync_watches(self) -> None:
    active = db.list_projects(status="active", **self._db_kwargs())
    active_ids = {p["id"] for p in active}

    with self._lock:
      for pid in list(self._watched.keys()):
        if pid not in active_ids:
          handle = self._watched.pop(pid)
          try:
            self._observer.unschedule(handle)
          except Exception:
            pass
          log.info("Stopped watching project_id=%s", pid)

      for p in active:
        pid = p["id"]
        if pid in self._watched:
          continue
        root = Path(p["root_path"])
        if not root.is_dir():
          log.warning("Project %s root missing: %s", pid, root)
          continue
        handler = _ProjectHandler(
          project_id=pid,
          project_root=root,
          debouncer=self._debouncer,
          bulk_guard=self._bulk_guard,
          db_path=self.db_path,
          template_path=self.template_path,
        )
        handle = self._observer.schedule(handler, str(root), recursive=True)
        self._watched[pid] = handle
        log.info("Watching project_id=%s name=%s root=%s", pid, p["name"], root)

  def start(self) -> None:
    self._sync_watches()
    self._observer.start()
    self._stop.clear()

    def _refresh_loop():
      while not self._stop.wait(self.refresh_interval):
        try:
          self._sync_watches()
        except Exception:
          log.exception("Error refreshing watches")

    self._refresh_thread = threading.Thread(
      target=_refresh_loop, daemon=True, name="notes-watch-refresh"
    )
    self._refresh_thread.start()
    log.info(
      "Watcher started (debounce=%.1fs bulk_window=%.1fs bulk_threshold=%d refresh=%.0fs)", 
      self.debounce_seconds,
      self._bulk_guard.window_seconds, 
      self._bulk_guard.threshold, 
      self.refresh_interval,
    )

  def stop(self) -> None:
    self._stop.set()
    self._debouncer.cancel_all()
    self._bulk_guard.reset() 
    self._observer.stop()
    self._observer.join(timeout=5)
    log.info("Watcher stopped")

  def run_forever(self) -> None:
    self.start()
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      pass
    finally:
      self.stop()