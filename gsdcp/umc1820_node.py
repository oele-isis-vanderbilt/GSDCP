from datetime import datetime
from multiprocessing import Queue
from queue import Empty
from typing import Dict, Optional

import numpy as np
import pyaudio
from chimerapy.engine import DataChunk, Node
from chimerapy.engine.eventbus import TypedObserver
from chimerapy.orchestrator import source_node


@source_node(name="GSDCP_UMC1820")
class UMC1820(Node):
    """UMC1820 Interface for the Behringer U-Phoria UMC1820 audio interface.

    This class is a specialized Node for handling multi-channel audio recording
    through the U-Phoria UMC1820. It inherits from the base Node class and
    adds additional functionality specific to the UMC1820.

    Notes
    -----
    Tested and Used only with Linux(Ubuntu 22.04) and PyAudio.
    """

    SAMPLE_RATE = 44100
    CHUNK_SIZE = 4096
    CHANNELS = 10

    def __init__(self, name="GSDCP_UMC1820", save_name=None, chunk_key="audio"):
        super().__init__(name=name)
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.save_name = save_name or self.name
        self.started = False
        self.audio_queue: Optional[Queue] = None
        self.chunk_key = chunk_key
        self.observers: Dict[str, TypedObserver] = {}

    async def setup(self) -> None:
        """Setup the UMC1820 for recording.

        This method will setup the UMC1820 for recording. It will also
        initialize the audio stream and set the stream parameters.
        """
        device_index = self._locate_device()
        if device_index == -1:
            self.logger.error("UMC1820 device not found.")
            raise RuntimeError("UMC1820 device not found.")

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            start=False,
            frames_per_buffer=self.CHUNK_SIZE,
            stream_callback=self._save_multi_channel,
            input_device_index=device_index,
        )
        self.audio_queue = Queue()
        self.logger.info("UMC1820 setup complete.")

        self.observers = {
            "NodeState.changed": TypedObserver(
                "NodeState.changed",
                on_asend=self.a_start_stop_stream,
                handle_event="drop",
            )
        }

        for ob in self.observers.values():
            await self.eventbus.asubscribe(ob)

    async def a_start_stop_stream(self):
        self.logger.info(
            f"{self.__class__.__name__} state changed to {self.state.fsm} at: "
            f"{datetime.now().isoformat()}."
        )
        if self.state.fsm == "PREVIEWING":
            self.stream.start_stream()
            self.started = True
            self.logger.info(
                f"UMC1820 streaming started. State is {self.state.fsm}"
            )

        elif self.state.fsm == "STOPPED":
            self.stream.stop_stream()
            self.started = False
            self.logger.info(
                f"UMC1820 streaming stopped. State is {self.state.fsm}"
            )

    def step(self) -> DataChunk:
        """Step the UMC1820.

        This method will step the UMC1820 and return the recorded data.
        """
        try:
            audio_data = self.audio_queue.get(timeout=1)
            ret_chunk = DataChunk()
            ret_chunk.add(self.chunk_key, audio_data)
            return ret_chunk
        except Empty:
            self.logger.debug("UMC1820 queue empty.")
            return None
        except Exception as e:
            self.logger.error(f"{e.__class__.__name__} in UMC1820 step: {e}")
            return None

    def _save_multi_channel(self, in_data, frame_count, time_info, status):
        """Save the multi-channel audio data.

        This method will save the multi-channel audio data to a file.
        """
        numpy_data = np.frombuffer(in_data, dtype=np.int16)
        channels_dict = {}
        for j in range(self.CHANNELS):
            channel_data = numpy_data[j :: self.CHANNELS]
            channels_dict[j] = channel_data
            if self.save_name is not None:
                self.save_audio_v2(
                    name=f"{self.save_name}-input-{j+1}",
                    data=channel_data.tobytes(),
                    channels=1,
                    sampwidth=2,
                    framerate=self.SAMPLE_RATE,
                    nframes=self.CHUNK_SIZE,
                )

        if self.save_name is not None:
            self.save_audio_v2(
                name=f"{self.save_name}-combined",
                data=in_data,
                channels=self.CHANNELS,
                sampwidth=2,
                framerate=self.SAMPLE_RATE,
                nframes=self.CHUNK_SIZE,
            )

        self.audio_queue.put_nowait(channels_dict)

        return None, pyaudio.paContinue

    def teardown(self) -> None:
        self.audio.terminate()
        self.logger.info("UMC1820 teardown complete.")

    @staticmethod
    def _locate_device() -> int:
        """Locate the UMC1820 device index.

        This method will locate the UMC1820 device index and return it.
        """
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev["name"].upper().startswith("UMC1820"):
                return i
        return -1
