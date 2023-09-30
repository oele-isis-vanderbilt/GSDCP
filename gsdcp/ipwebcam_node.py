import imutils
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node
from vidgear.gears import CamGear


@source_node(name="GSDCP_IPWebCam")
class IPWebCam(Node):
    def __init__(
        self, rtsp_url: str, save_name: str = None, name: str = "IPWebCam"
    ):
        super().__init__(name=name)
        self.rtsp_url = rtsp_url
        self.cap = None
        self.save_name = save_name
        self.started = False

    def setup(self):
        self.cap = CamGear(self.rtsp_url)

    def step(self) -> DataChunk:
        if not self.started:
            print("starting")
            self.cap.start()
            self.started = True
        data_chunk = DataChunk()
        frame = self.cap.read()

        if self.save_name is not None:
            self.save_video(self.save_name, frame, self.cap.framerate)

        small_frame = imutils.resize(frame, width=640)
        data_chunk.add("frame", small_frame, "image")
        return data_chunk

    def teardown(self):
        if self.started:
            self.cap.stop()
