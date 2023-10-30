import platform
import time
from typing import Optional

import cv2
import numpy as np
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node
from PIL import ImageGrab


@source_node(name="GSDCP_EfficientScreenCapture")
class EfficientScreenCapture(Node):
    def __init__(
        self,
        scale: float = 0.5,
        fps: int = 30,
        name: str = "EfficientScreenCapture",
        save_name: Optional[str] = None,
        frames_key: str = "frame",
        save_timestamp: bool = False,
    ) -> None:
        super().__init__(name=name)
        self.scale = scale
        self.fps = fps
        self.save_name = save_name
        self.save_timestamp = save_timestamp
        self.frames_key = frames_key

    def setup(self) -> None:
        if platform.system() == "Windows":
            raise NotImplementedError("Windows is not supported yet.")

    def step(self) -> DataChunk:
        data_chunk = DataChunk()
        print("Capturing frame...")
        frame = np.array(ImageGrab.grab(), dtype=np.uint8)
        frame_opencv = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_resized = cv2.resize(
            frame_opencv, (0, 0), fx=self.scale, fy=self.scale
        )
        print(frame_resized.size)
        data_chunk.add(self.frames_key, frame_resized, "image")
        if self.save_name is not None:
            self.save_video(self.save_name, frame_resized, self.fps)
        time.sleep(1 / self.fps)
        return data_chunk

    def teardown(self):
        pass
