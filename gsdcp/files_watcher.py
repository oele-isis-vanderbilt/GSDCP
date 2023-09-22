import time
from dataclasses import dataclass
from queue import Queue
from typing import Dict, List, Optional, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SENTINEL = None


@dataclass
class ModifiedFileData:
    """Data class to store information about a modified file."""

    path: str
    new_lines: List[str]


class Handler(FileSystemEventHandler):
    """Custom file system event handler."""

    def __init__(self):
        super().__init__()
        self.clients: Set[Queue] = set()  # A set of client queues
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
            self.handles[event.src_path] = 0

        elif event.event_type == "modified":
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


class DirectoryObserver:
    """Class to observe a directory for file changes."""

    def __init__(self, path: str):
        self.path = path
        self.observer = Observer()
        self.handler = Handler()

    def setup(self, clients: Optional[List[Queue]] = None) -> None:
        """Setup the observer."""
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
