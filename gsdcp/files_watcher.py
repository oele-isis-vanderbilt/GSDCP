import time
from dataclasses import dataclass
from queue import Queue
from typing import List, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SENTINEL = None


@dataclass
class ModifiedFileData:
    path: str
    new_lines: List[str]


class Handler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.clients = set()
        self.handles = {}

    def add_client(self, q: Queue):
        self.clients.add(q)

    def remove_client(self, q: Queue):
        self.clients.discard(q)

    def remove_all_clients(self):
        self.clients.clear()

    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == "created":
            self.handles[event.src_path] = 0

        elif event.event_type == "modified":
            if event.src_path not in self.handles:
                self.handles[event.src_path] = 0

            lines = self._read_new_lines(event.src_path)
            self._broadcast_modified_file_data(event.src_path, lines)

    def _broadcast_modified_file_data(self, file: str, lines: List[str]):
        modification_event = ModifiedFileData(path=file, new_lines=lines)

        for q in self.clients:
            q.put_nowait(modification_event)

    def _read_new_lines(self, file: str) -> List[str]:
        with open(file, "r") as f:
            f.seek(self.handles[file])
            nl = f.readlines()
            self.handles[file] = f.tell()

        return nl

    def enqueue_sentinel(self):
        for q in self.clients:
            q.put_nowait(SENTINEL)


class DirectoryObserver:
    def __init__(self, path):
        self.path = path
        self.observer = Observer()
        self.handler = Handler()

    def setup(self, clients: Optional[List[Queue]] = None):

        if clients is not None:
            for q in clients:
                self.handler.add_client(q)

        self.observer.schedule(self.handler, self.path, recursive=True)

    def start(self, blocking=True):
        self.observer.start()
        if blocking:
            try:
                while True:
                    time.sleep(5)
            except Exception:
                print("Stopping observer")
                self.teardown()

    def teardown(self):
        self.handler.enqueue_sentinel()
        self.observer.stop()
        self.observer.join()


if __name__ == "__main__":
    observer = DirectoryObserver(path="/home/umesh/isis/oele/GSDCP/watch_dir")
    observer.setup()
    observer.start(blocking=False)
    time.sleep(10)
    observer.teardown()
