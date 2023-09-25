import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, List, Literal, Optional, Set

from watchdog.events import FileSystemEventHandler

SENTINEL = None


@dataclass
class ModifiedFileData:
    """Data class to store information about a modified file."""

    path: str
    new_lines: List[str]


class Handler(FileSystemEventHandler):
    """Custom file system event handler."""

    def __init__(self, patterns: Optional[List[str]] = None):
        super().__init__()
        self.clients: Set[Queue] = set()  # A set of client queues
        self.patterns = set(patterns or [])
        self.handles: Dict[
            str, int
        ] = {}  # A dictionary to keep track of file positions

    def add_client(self, q: Queue) -> None:
        """Add a new client queue."""
        self.clients.add(q)

    def remove_client(self, q: Queue) -> None:
        """Remove an existing client queue."""
        self.clients.discard(q)

    def remove_all_clients(self) -> None:
        """Remove all client queues."""
        self.clients.clear()

    def on_any_event(self, event) -> None:
        """Handle any file system event."""
        if event.is_directory:
            return

        elif event.event_type == "created":
            if self.is_target_pattern(event.src_path):
                self.handles[event.src_path] = 0

        elif event.event_type == "modified":
            if self.is_target_pattern(event.src_path):
                if event.src_path not in self.handles:
                    self.handles[event.src_path] = 0

                lines = self._read_new_lines(event.src_path)
                self._broadcast_modified_file_data(event.src_path, lines)

    def _broadcast_modified_file_data(
        self, file: str, lines: List[str]
    ) -> None:
        """Broadcast file modification data to all client queues."""
        modification_event = ModifiedFileData(path=file, new_lines=lines)
        for q in self.clients:
            q.put_nowait(modification_event)

    def _read_new_lines(self, file: str) -> List[str]:
        """Read new lines from a modified file."""
        with open(file, "r") as f:
            f.seek(self.handles[file])
            new_lines = f.readlines()
            self.handles[file] = f.tell()

        return new_lines

    def enqueue_sentinel(self) -> None:
        """Enqueue a sentinel object to all client queues."""
        for q in self.clients:
            q.put_nowait(SENTINEL)

    def is_target_pattern(self, file_path: str) -> bool:
        """Check if a file matches any of the target patterns."""
        if self.patterns == set():
            return True
        else:
            return self._get_extension(file_path) in self.patterns

    def _get_extension(self, file_path) -> None:
        """Get the file extension of a file."""
        return Path(file_path).suffix


class DirectoryObserver:
    """Class to observe a directory for file changes."""

    def __init__(
        self,
        path: str,
        patterns: Optional[List[str]] = None,
        observer_type: Literal[
            "inotify",
            "fsevents",
            "kqueue",
            "read_directory_changes",
            "fallback",
            "auto",
        ] = "auto",
    ):
        self.path = path
        self.observer = None
        self.handler = Handler(patterns=patterns)
        self.observer_type = observer_type

    def setup(self, clients: Optional[List[Queue]] = None) -> None:
        """Setup the observer."""
        if self.observer_type == "auto":
            from watchdog.observers import Observer

        elif self.observer_type == "inotify":
            from watchdog.observers.inotify import InotifyObserver as Observer

        elif self.observer_type == "fsevents":
            from watchdog.observers.fsevents import FSEventsObserver as Observer

        elif self.observer_type == "kqueue":
            from watchdog.observers.kqueue import KqueueObserver as Observer

        elif self.observer_type == "read_directory_changes":
            from watchdog.observers.read_directory_changes import (
                WindowsApiObserver as Observer,
            )

        elif self.observer_type == "fallback":
            from watchdog.observers.polling import PollingObserver as Observer

        else:
            raise ValueError(f"Invalid observer type: {self.observer_type}")

        self.observer = Observer()

        if clients is not None:
            for q in clients:
                self.handler.add_client(q)
        self.observer.schedule(self.handler, self.path, recursive=True)

    def start(self, blocking: bool = True) -> None:
        """Start the observer."""
        self.observer.start()
        if blocking:
            try:
                while True:
                    time.sleep(5)
            except Exception:
                print("Stopping observer")
                self.teardown()

    def teardown(self) -> None:
        """Teardown the observer."""
        self.handler.enqueue_sentinel()
        self.observer.stop()
        self.observer.join()
