from typing import Optional

import cv2
import imutils
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_DroidCam")
class DroidCam(Node):
    def __init__(
        self,
        phone_ip: str,
        droidcam_port: int = 4747,
        frame_key: str = "frame",
        force_suffix: Optional[str] = "/force/1920x1080",
        save_name: str = None,
        name: str = "DroidCam",
    ):
        super().__init__(name=name)
        self.phone_ip = phone_ip
        self.droidcam_port = droidcam_port
        self.frame_key = frame_key
        self.save_name = save_name
        self.force_suffix = force_suffix
        self.cap = None

    def setup(self):
        addr = f"http://{self.phone_ip}:{self.droidcam_port}/video"
        if self.force_suffix is not None:
            addr += self.force_suffix

        self.logger.info(f"Connecting to DroidCam... at {addr}")
        self.cap = cv2.VideoCapture(addr)

    def step(self) -> DataChunk:
        ret, frame = self.cap.read()

        if not ret:
            self.logger.error("Failed to capture frame from DroidCam.")
            self.retry_capture()
            ret, frame = self.cap.read()

        data_chunk = DataChunk()

        if self.save_name is not None:
            self.save_video(self.save_name, frame, 30)

        frame = imutils.resize(frame, width=640)
        data_chunk.add(self.frame_key, frame, "image")

        return data_chunk

    def retry_capture(self):
        if self.cap is not None:
            self.cap.release()
        self.logger.info("Retrying to connect to DroidCam...")
        addr = f"http://{self.phone_ip}:{self.droidcam_port}/video"

        if self.force_suffix is not None:
            addr += self.force_suffix

        self.cap = cv2.VideoCapture(addr)

    def teardown(self):
        self.cap.release()
