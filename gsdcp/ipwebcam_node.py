import cv2
from chimerapy.engine import Node, DataChunk
import imutils
import numpy as np

from chimerapy.orchestrator import source_node

@source_node(name="GSDCP_IPWebCam")
class IPWebCam(Node):
    def __init__(self, rtsp_url: str, save_name: str = None, name: str = "IPWebCam"):
        super().__init__(name=name)
        self.rtsp_url = rtsp_url
        self.cap = None
        self.save_name = save_name

    def setup(self):
        self.cap = cv2.VideoCapture(self.rtsp_url)

    def step(self) -> DataChunk:
        ret, frame = self.cap.read()
        data_chunk = DataChunk()
        if not ret:
            self.logger.error("Failed to capture frame from IPWebCam.")
            data_chunk.add("frame", np.random.randint(255, size=(640, 480, 3), dtype=np.uint8), "image")
            return data_chunk

        if self.save_name is not None:
            self.save_video(self.save_name, frame, 30)

        small_image = imutils.resize(frame, width=640)
        data_chunk.add("frame", small_image, "image")
        return data_chunk

    def retry_capture(self):
        if self.cap is not None:
            self.cap.release()
        self.logger.info("Retrying to connect to IPWebCam...")
        self.cap = cv2.VideoCapture(self.rtsp_url)

    def teardown(self):
        self.cap.release()
