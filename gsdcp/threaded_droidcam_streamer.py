import time
from threading import Thread, ThreadError
from uuid import uuid4

import cv2
import numpy as np
import requests


class DroidCamStreamer:
    def __init__(self, url):
        self.stream = requests.get(url, stream=True)
        self.thread_cancelled = False
        self.thread = Thread(target=self.run)
        self.clients = set()

    def start(self):
        self.thread.start()

    def run(self):
        bytes = b""
        while not self.thread_cancelled:
            try:
                bytes += self.stream.raw.read(1024)
                a = bytes.find(b"\xff\xd8")
                b = bytes.find(b"\xff\xd9")
                if a != -1 and b != -1:
                    jpg = bytes[a : b + 2]
                    bytes = bytes[b + 2 :]
                    img = cv2.imdecode(
                        np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR
                    )
                    print(img.shape)
                    for client in self.clients:
                        client.put_nowait(img)
            except ThreadError:
                print("Camera thread error")
                self.thread_cancelled = True

    def is_running(self):
        return self.thread.is_alive()

    def shut_down(self):
        self.thread_cancelled = True
        # block while waiting for thread to terminate
        while self.thread.is_alive():
            time.sleep(1)

        for client in self.clients:
            client.put_nowait(None)

        return True

    def add_client(self, client):
        self.clients.add(client)

    def remove_client(self, client):
        self.clients.remove(client)
