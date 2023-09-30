import cv2
import imutils
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_IVCAM")
class IVCAM(Node):
    def __init__(
        self, video_src, save_name=None, res=(1920, 1080), name="IVCAM"
    ):
        super().__init__(name=name)
        self.src_id = video_src
        self.cap = None
        self.save_name = save_name
        self.res = res

    def setup(self):
        self.cap = cv2.VideoCapture(self.src_id)
        h, w = self.res
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def step(self) -> DataChunk:
        data_chunk = DataChunk()
        ret, frame = self.cap.read()
        if self.save_name is not None:
            self.save_video(self.save_name, frame, 30)

        frame_transmitted = imutils.resize(frame, width=320)

        data_chunk.add("frame", frame_transmitted, "image")

        return data_chunk

    def teardown(self):
        if self.cap is not None:
            self.cap.release()
