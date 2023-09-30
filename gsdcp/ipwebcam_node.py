import threading

import cv2
import imutils
import numpy as np
import requests
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node
from requests.adapters import HTTPAdapter


class VideoStream:
    def __init__(self, url, retries=5, timeout=5):
        self.cap = None
        self.url = url
        self.retries = retries
        self.timeout = timeout
        self.ret = False
        self.frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.update)
        self.read_thread.daemon = True
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.session = None

    def setup(self):
        self.session = requests.Session()
        # Setup Retry Strategy
        retry = HTTPAdapter(max_retries=self.retries)
        self.session.mount(self.url, retry)
        self.cap = self.session.get(self.url, stream=True, timeout=self.timeout)
        assert (
            self.cap.status_code == 200
        ), f"Received unexpected status code {self.cap.status_code}"
        self.read_thread.start()

    def update(self):
        while not self.stop_event.is_set():
            byte_stream = bytes()
            for chunk in self.cap.iter_content(chunk_size=1024):
                byte_stream += chunk
                a = byte_stream.find(b"\xff\xd8")
                b = byte_stream.find(b"\xff\xd9")

                if a != -1 and b != -1:
                    jpg = byte_stream[a : b + 2]
                    byte_stream = byte_stream[b + 2 :]

                    try:
                        i = cv2.imdecode(
                            np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR
                        )
                        with self.lock:
                            self.ret = i is not None
                            self.frame = i
                    except Exception as e:
                        print(f"Error encountered: {e}")
                        i = None

    def read(self):
        with self.lock:
            ret = self.ret
            frame = self.frame.copy() if self.frame is not None else None
        return ret, frame

    def teardown(self):
        self.stop_event.set()
        self.session.close()


@source_node(name="GSDCP_IPWebCam")
class IPWebCam(Node):
    def __init__(
        self, rtsp_url: str, save_name: str = None, name: str = "IPWebCam"
    ):
        super().__init__(name=name)
        self.rtsp_url = rtsp_url
        self.cap = None
        self.save_name = save_name

    def setup(self):
        self.cap = VideoStream(self.rtsp_url)
        self.cap.setup()

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
