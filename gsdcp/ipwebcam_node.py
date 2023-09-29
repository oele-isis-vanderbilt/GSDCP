import cv2
from chimerapy.engine import Node, DataChunk
import imutils
import numpy as np

from chimerapy.orchestrator import source_node

import cv2
import threading


class VideoStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.ret = False
        self.frame = None
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.update)
        self.read_thread.daemon = True
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.read_thread.start()

    def update(self):
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            ret = self.ret
            frame = self.frame.copy() if self.frame is not None else None
        return ret, frame

    def teardown(self):
        self.stop_event.set()
        self.cap.release()


@source_node(name="GSDCP_IPWebCam")
class IPWebCam(Node):
    def __init__(self, rtsp_url: str, save_name: str = None, name: str = "IPWebCam"):
        super().__init__(name=name)
        self.rtsp_url = rtsp_url
        self.cap = None
        self.save_name = save_name

    def setup(self):
        self.cap = VideoStream(self.rtsp_url)

    def step(self) -> DataChunk:
        ret, frame = self.cap.read()

        if self.save_name is not None:
            self.save_video(self.save_name, frame, 30)

        data_chunk = DataChunk()
        small_image = imutils.resize(frame, width=640)
        data_chunk.add("frame", small_image, "image")

        return data_chunk

    def teardown(self):
        if self.cap is not None:
            self.cap.teardown()
