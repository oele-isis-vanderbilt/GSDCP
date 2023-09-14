import struct
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import pyaudio
from chimerapy.engine.records import AudioRecord
from pvrecorder import PvRecorder


def list_devices(using="pvrecorder") -> None:
    if using == "pvrecorder":
        devices = PvRecorder.get_available_devices()
        for idx, device in enumerate(devices):
            print(f"Index {idx}: {device}")
    elif using == "pyaudio":
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            if p.get_device_info_by_index(i)["maxInputChannels"] > 0:
                print(p.get_device_info_by_index(i))


def get_name_by_device_index(device_index: int, using="pvrecorder") -> str:
    if using == "pvrecorder":
        devices = PvRecorder.get_available_devices()
        dev_name = devices[device_index]
    elif using == "pyaudio":
        p = pyaudio.PyAudio()
        dev_name = p.get_device_info_by_index(device_index)["name"]
    else:
        raise ValueError(f"Invalid backend: {using}")

    return dev_name.replace(" ", "_")


def record_pv_recorder(
    device_index: int, record_time: int, save_path: str
) -> None:
    recorder = PvRecorder(frame_length=512, device_index=device_index)

    audio_writer = AudioRecord(
        dir=Path(save_path),
        name=f"pvrecorder-test-dev_index_{device_index}-dev_name_{get_name_by_device_index(device_index)}",
    )
    print(f"Recording for {record_time} seconds using pvrecorder.")
    recorder.start()
    start_time = datetime.now()
    while (datetime.now() - start_time).total_seconds() < record_time:
        frame = recorder.read()
        data = struct.pack("h" * len(frame), *frame)
        data_chunk = {
            "uuid": uuid.uuid4(),
            "name": "pvrecorder-test",
            "data": data,
            "dtype": "audio",
            "channels": 1,
            "sampwidth": 2,
            "framerate": recorder.sample_rate,
            "nframes": recorder.frame_length,
            "recorder_version": 2,
            "timestamp": datetime.now(),
        }
        audio_writer.write(data_chunk)

    recorder.delete()
    audio_writer.close()
    print(
        f"Finished recording for {record_time} seconds using pvrecorder. "
        f"Saved to {audio_writer.audio_file_path}"
    )


def record_pyaudio_channels(
    device_index: int, record_time: int, save_path: str, channel: int = 3
) -> None:
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=10,
        rate=44100,
        input=True,
        frames_per_buffer=512,
        input_device_index=device_index,
        start=False,
    )
    writers = {}
    for j in range(10):
        audio_writer = AudioRecord(
            dir=Path(save_path),
            name=f"pyaudio-test-dev_index_{device_index}-dev_name_{get_name_by_device_index(device_index, using='pyaudio')}-channel_{j+1}",
        )
        writers[j] = audio_writer

    print(f"Recording for {record_time} seconds using pyaudio.")
    start_time = datetime.now()
    stream.start_stream()
    while (datetime.now() - start_time).total_seconds() < record_time:
        data = stream.read(512)
        numpy_data = np.frombuffer(data, dtype=np.int16)
        for j in range(10):
            data = numpy_data[j::10].tobytes()
            data_chunk = {
                "uuid": uuid.uuid4(),
                "name": "pyaudio-test",
                "data": data,
                "dtype": "audio",
                "channels": 1,
                "sampwidth": 2,
                "framerate": 44100,
                "nframes": 512,
                "recorder_version": 2,
                "timestamp": datetime.now(),
            }
            writers[j].write(data_chunk)
        # audio_writer.write(data_chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()
    for audio_writer in writers.values():
        audio_writer.close()
    print(
        f"Finished recording for {record_time} seconds using pyaudio. "
        f"Saved to {save_path}"
    )


def record_pyaudio(device_index: int, record_time: int, save_path: str) -> None:
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=512,
        input_device_index=device_index,
        start=False,
    )

    audio_writer = AudioRecord(
        dir=Path(save_path),
        name=f"pyaudio-test-dev_index_{device_index}-dev_name_{get_name_by_device_index(device_index, using='pyaudio')}",
    )
    print(f"Recording for {record_time} seconds using pyaudio.")
    start_time = datetime.now()
    stream.start_stream()
    while (datetime.now() - start_time).total_seconds() < record_time:
        data = stream.read(512)
        data_chunk = {
            "uuid": uuid.uuid4(),
            "name": "pyaudio-test",
            "data": data,
            "dtype": "audio",
            "channels": 1,
            "sampwidth": 2,
            "framerate": 16000,
            "nframes": 512,
            "recorder_version": 2,
            "timestamp": datetime.now(),
        }
        audio_writer.write(data_chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()
    audio_writer.close()
    print(
        f"Finished recording for {record_time} seconds using pyaudio. "
        f"Saved to {audio_writer.audio_file_path}"
    )


if __name__ == "__main__":
    import sys
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

    parser = ArgumentParser(
        description="Test the audio recorder in ChimeraPy.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "command",
        choices=["record", "list-devices"],
    )

    parser.add_argument(
        "--using",
        default="pvrecorder",
        choices=["pvrecorder", "pyaudio"],
        help="Which audio recorder to use.",
    )

    parser.add_argument(
        "--device-index",
        type=int,
        required="record" in sys.argv,
        help="Which audio device(microphone) to use.",
    )

    parser.add_argument(
        "--save-path",
        default=".",
        type=str,
        help="Where to save the audio file.",
    )

    parser.add_argument(
        "--time",
        default=10,
        type=int,
        help="How long to record for(in seconds).",
    )

    parser.add_argument(
        "--channel",
        default=None,
        type=int,
        help="Which channel to record from.",
    )

    args = parser.parse_args()
    if args.command == "list-devices":
        list_devices(using=args.using)
    elif args.command == "record":
        if args.using == "pvrecorder":
            record_pv_recorder(
                device_index=args.device_index,
                record_time=args.time,
                save_path=args.save_path,
            )
        elif args.using == "pyaudio":
            if args.channel is not None:
                record_pyaudio_channels(
                    device_index=args.device_index,
                    record_time=args.time,
                    save_path=args.save_path,
                    channel=args.channel,
                )
            else:
                record_pyaudio(
                    device_index=args.device_index,
                    record_time=args.time,
                    save_path=args.save_path,
                )

    else:
        parser.print_help()
