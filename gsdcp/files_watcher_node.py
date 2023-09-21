from multiprocessing import Queue
from pathlib import Path
from queue import Empty
from typing import Dict, List, Optional, Union

from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node

from gsdcp.files_watcher import DirectoryObserver, ModifiedFileData


@source_node(name="GSDCP_FilesWatcher")
class FilesWatcher(Node):
    """Watcher Node for watching a set of files for changes.

    Parameters
    ----------
    target_directory : str
        The directory to watch for changes.
    """

    def __init__(
        self,
        target_directory: str,
        chunk_key: str = "text",
        name: str = "FileWatcher",
    ) -> None:
        super().__init__(name=name)
        self.target_directory = target_directory
        self.observer: Optional[DirectoryObserver] = None
        self.data_queue: Optional[Queue] = None
        self.chunk_key = chunk_key
        self.started = False

    def setup(self) -> None:
        self.observer = DirectoryObserver(self.target_directory)
        self.data_queue = Queue()
        self.observer.setup(clients=[self.data_queue])
        self.logger.info("FileWatcher setup complete.")

    def step(self) -> Union[DataChunk, None]:
        if not self.started:
            self.observer.start(blocking=False)
            self.started = True
        try:
            modification_data: Optional[ModifiedFileData] = self.data_queue.get(
                timeout=1
            )

            save_name = Path(modification_data.path).stem
            suffix = Path(modification_data.path).suffix[1:]
            text = "".join(modification_data.new_lines)

            self.save_text(
                name=save_name,
                data=text,
                suffix=suffix,
            )

            ret_chunk = DataChunk()
            self.logger.debug("Changed file: %s", modification_data.path)
            ret_chunk.add("text", text)
            return ret_chunk
        except Empty:
            return None

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
        self.observer.teardown()
