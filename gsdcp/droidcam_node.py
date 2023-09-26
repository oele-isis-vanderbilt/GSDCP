import cv2
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_DroidCam")
class DroidCam(Node):
    def __init__(
        self,
        phone_ip: str,
        droidcam_port: int = 4747,
        frame_key: str = "frame",
        save_name: str = None,
        name: str = "DroidCam",
    ):
        super().__init__(name=name)
        self.phone_ip = phone_ip
        self.droidcam_port = droidcam_port
        self.frame_key = frame_key
        self.save_name = save_name
        self.cap = None

    def setup(self):
        addr = f"http://{self.phone_ip}:{self.droidcam_port}/video"
        self.logger.info(f"Connecting to DroidCam... at {addr}")
        self.cap = cv2.VideoCapture(addr)

    def step(self) -> DataChunk:
        ret, frame = self.cap.read()

        if not ret:
            raise RuntimeError("Failed to read from DroidCam.")

        data_chunk = DataChunk()
        data_chunk.add(self.frame_key, frame, "image")

        if self.save_name is not None:
            self.save_video(self.save_name, frame, 30)

        return data_chunk

    def teardown(self):
        self.cap.release()
        cv2.destroyAllWindows()
