from multiprocessing import Queue
from queue import Empty
from typing import Optional

import cv2
import imutils
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node

from .threaded_droidcam_streamer import DroidCamStreamer


@source_node(name="GSDCP_DroidCam")
class DroidCam(Node):
    def __init__(
        self,
        phone_ip: str,
        droidcam_port: int = 4747,
        frame_key: str = "frame",
        force_suffix: Optional[str] = "/mjpegfeed?1920x1080",
        save_name: str = None,
        name: str = "DroidCam",
    ):
        super().__init__(name=name)
        self.phone_ip = phone_ip
        self.droidcam_port = droidcam_port
        self.frame_key = frame_key
        self.save_name = save_name
        self.force_suffix = force_suffix
        self.streamer = None
        self.started = False
        self.data_queue = None

    def setup(self):
        addr = f"http://{self.phone_ip}:{self.droidcam_port}/video"
        if self.force_suffix is not None:
            addr += self.force_suffix

        self.logger.info(f"Connecting to DroidCam... at {addr}")
        self.streamer = DroidCamStreamer(addr)
        self.started = False
        self.data_queue = Queue()

    def step(self) -> Optional[DataChunk]:
        if not self.started and self.streamer is not None:
            self.streamer.start()
            self.streamer.add_client(self.data_queue)
            self.started = True

        try:
            img = self.data_queue.get(timeout=1)
            if img is None:
                return None
            frame = img
            self.save_video(self.save_name, frame, 30)
            data_chunk = DataChunk()
            small_image = imutils.resize(frame, width=640)
            data_chunk.add(self.frame_key, small_image, "image")
            return data_chunk
        except Empty:
            return None

    def teardown(self):
        self.streamer.shut_down()
