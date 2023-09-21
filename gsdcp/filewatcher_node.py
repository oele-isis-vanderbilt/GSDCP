import time
from typing import Dict, List

from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_FileWatcher")
class FileWatcher(Node):
    """Watcher Node for watching a set of files for changes.

    Parameters
    ----------
    target_files : List[str]
        The list of target files to watch for changes.
    """

    def __init__(
        self,
        target_files: List[str],
        step_delay: float = 1.0,
        name: str = "FileWatcher",
    ) -> None:
        super().__init__(name=name)
        self.target_files = target_files
        self.step_delay = step_delay
        self.handlers = {}

    def setup(self) -> None:
        for file in self.target_files:
            self.handlers[file] = 0

    def step(self) -> DataChunk:
        new_lines = self._read_new_lines()
        print(new_lines)
        time.sleep(self.step_delay)
        return DataChunk()

    def _read_new_lines(self) -> Dict[str, List[str]]:
        new_lines = {}

        for file in self.target_files:
            with open(file, "r") as f:
                f.seek(self.handlers[file])
                nl = f.readlines()
                self.handlers[file] = f.tell()
                new_lines[file] = nl

        return new_lines

    def teardown(self):
        self.observer.stop()
        self.observer.join()
