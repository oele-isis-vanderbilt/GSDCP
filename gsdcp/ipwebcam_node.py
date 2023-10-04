import cv2
import imutils
import requests
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
    ):
        super().__init__(name=name)
        self.url: str = url
        self.cap = None
        self.tag = tag
        self.save_name = save_name
        self.started = False

    def setup(self):
        self.cap = cv2.VideoCapture(f"{self.url}/video")
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def step(self) -> DataChunk:
        if not self.started:
            self._send_start_recording_request()
        data_chunk = DataChunk()
        ret, frame = self.cap.read()

        if not ret:
            return None

        if self.save_name is not None:
            self.save_video(
                self.save_name, frame, self.cap.get(cv2.CAP_PROP_FPS)
            )

        small_frame = imutils.resize(frame, width=640)
        data_chunk.add("frame", small_frame, "image")

        if self.state.fsm == "STOPPED":
            self._send_stop_recording_request()

        return data_chunk

    def _send_start_recording_request(self):
        path = (
            "/startvideo?force=1"
            if self.tag == ""
            else f"/startvideo?tag={self.tag}&force=1"
        )
        response = requests.get(f"{self.url}{path}")
        assert (
            response.status_code == 200
        ), f"Failed to start recording: {response.text}"
        self.started = True
        self.logger.info("Started recording")

    def _send_stop_recording_request(self):
        path = "/stopvideo?force=1"
        response = requests.get(f"{self.url}{path}")
        assert (
            response.status_code == 200
        ), f"Failed to stop recording: {response.text}"
        self.started = False
        self.logger.info("Stopped recording")

    def teardown(self):
        if self.cap is not None:
            self.cap.release()
