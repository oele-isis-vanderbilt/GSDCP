from multiprocessing import Queue
from pathlib import Path
from queue import Empty
from typing import List, Literal, Optional, Union

from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node

from gsdcp.files_watcher import SENTINEL, DirectoryObserver, ModifiedFileData


@source_node(name="GSDCP_FilesWatcher")
class FilesWatcher(Node):
    """
    Watcher Node for watching a set of files for changes.

    Parameters
    ----------
    target_directory : str
        The directory to watch for changes.
    chunk_key : str, optional, default="text"
        The key to use for the DataChunk, by default "text"
    """

    def __init__(
        self,
        target_directory: str,
        chunk_key: str = "text",
        name: str = "FileWatcher",
        patterns: Optional[List[str]] = None,
        observer_type: Literal[
            "inotify",
            "fsevents",
            "kqueue",
            "read_directory_changes",
            "fallback",
            "auto",
        ] = "auto",
    ) -> None:
        super().__init__(name=name)
        self.target_directory: str = target_directory
        self.observer: Optional[DirectoryObserver] = None
        self.data_queue: Optional[Queue] = None
        self.chunk_key: str = chunk_key
        self.started: bool = False
        self.patterns: Optional[List[str]] = patterns
        self.observer_type: Literal[
            "inotify",
            "fsevents",
            "kqueue",
            "read_directory_changes",
            "fallback",
            "auto",
        ] = observer_type

    def setup(self) -> None:
        """Initialize the observer and data queue."""
        self.observer = DirectoryObserver(
            self.target_directory,
            patterns=self.patterns,
            observer_type=self.observer_type,
        )
        self.data_queue = Queue()
        self.observer.setup(clients=[self.data_queue])
        self.logger.info("FileWatcher setup complete.")

    def step(self) -> Union[DataChunk, None]:
        """
        Step through the observer events, and return data chunks for modifications.

        Returns
        -------
        Union[DataChunk, None]
            DataChunk for modifications, or None for no modification or teardown.
        """
        if not self.started:
            self.observer.start(blocking=False)
            self.started = True

        try:
            modification_data: Optional[ModifiedFileData] = self.data_queue.get(
                timeout=1
            )

            if modification_data is SENTINEL:
                return None

            save_name: str = Path(modification_data.path).stem
            suffix: str = Path(modification_data.path).suffix[1:]
            text: str = "".join(modification_data.new_lines)

            self.save_text(
                name=save_name,
                data=text,
                suffix=suffix,
            )

            ret_chunk: DataChunk = DataChunk()
            self.logger.debug("Changed file: %s", modification_data.path)
            ret_chunk.add(self.chunk_key, text)
            return ret_chunk

        except Empty:
            return None

    def teardown(self) -> None:
        """Tear down the observer."""
        self.observer.teardown()
