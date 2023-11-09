from mss import mss

import numpy as np
import simplejpeg
import cv2
import imutils
from argparse import ArgumentParser
import zmq
import asyncio
import zmq.asyncio
import cv2
from datetime import datetime


def append_timestamp(arr):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cv2.putText(
        arr,
        timestamp,
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2,
    )
    return arr


async def publish_screen(capture, socket, scale, monitor, save_timestamp):
    img = capture.grab(capture.monitors[monitor])
    arr = np.array(img)
    arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    arr = imutils.resize(arr, width=int(arr.shape[1] * scale))

    if save_timestamp:
        arr = append_timestamp(arr)

    await socket.send(simplejpeg.encode_jpeg(arr, quality=80))


async def run(args):
    cap = mss()
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://*:{args.port}")
    # HWM
    socket.sndhwm = 1
    socket.rcvhwm = 1

    while True:
        await publish_screen(cap, socket, args.scale, args.monitor, args.save_timestamp)
        await asyncio.sleep(1 / args.fps)


if __name__ == "__main__":
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description="Publish screen to ZMQ socket.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port",
        "-p",
        help="The port to publish on.",
        type=int,
        default=8080
    )

    parser.add_argument(
        "--scale",
        "-s",
        help="The scale to resize the image to.",
        type=float,
        default=0.5
    )

    parser.add_argument(
        "--monitor",
        "-m",
        help="The monitor to capture.",
        type=int,
        default=0
    )

    parser.add_argument(
        "--fps",
        "-f",
        help="The FPS to capture at.",
        type=int,
        default=50
    )

    parser.add_argument(
        "--save-timestamp",
        "-t",
        help="Save timestamp on image.",
        action="store_true",
        default=True
    )

    args = parser.parse_args()
    asyncio.run(run(args))



