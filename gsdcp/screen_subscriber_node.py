import simplejpeg
import zmq.asyncio
from chimerapy.engine import DataChunk, Node
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_ScreenSubscriber")
class ScreenSubscriber(Node):
    def __init__(
        self, host, port, save_name=None, fps=30, name="ScreenSubscriberNode"
    ):
        super().__init__(name=name)
        self.host = host
        self.port = port
        self.fps = fps
        self.context = None
        self.socket = None
        self.save_name = save_name

    async def setup(self):
        self.context = zmq.asyncio.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.socket.subscribe("")
        self.logger.info(f"Connected to tcp://{self.host}:{self.port}")

    async def step(self) -> DataChunk:
        data_chunk = DataChunk()
        frame = await self.socket.recv()
        image = simplejpeg.decode_jpeg(frame, colorspace="RGB", fastdct=True)

        if self.save_name is not None:
            self.save_video(self.save_name, image, self.fps)

        data_chunk.add("frame", image, "image")
        return data_chunk

    async def teardown(self):
        self.socket.close()
