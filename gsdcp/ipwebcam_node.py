import cv2
import imutils
import numpy as np
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_IPWebCam")
class IPWebCam(Node):
    def __init__(
        self,
        url: str,
        tag: str = "",
        save_name: str = None,
        name: str = "IPWebCamRecorder",
    ) -> None:
        super().__init__(name=name)
        self.url: str = url
        self.cap = None
        self.tag = tag
        self.save_name = save_name
        self.started = False
        self.last_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def setup(self) -> None:
        # Timeout is set to 2 second to avoid blocking the main thread
        self.cap = cv2.VideoCapture(f"{self.url}")
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        # time.sleep(2)

    def step(self) -> DataChunk:
        data_chunk = DataChunk()
        ret, frame = self.cap.read()

        if not ret:
            data_chunk.add("frame", self.last_frame, "image")
            return data_chunk

        if self.save_name is not None:
            self.save_video(
                self.save_name, frame, self.cap.get(cv2.CAP_PROP_FPS)
            )

        small_frame = imutils.resize(frame, width=640)
        self.last_frame = small_frame
        data_chunk.add("frame", small_frame, "image")

        return data_chunk

    def teardown(self):
        if self.cap is not None:
            self.cap.release()
