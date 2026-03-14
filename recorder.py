import queue
import threading
from datetime import datetime
from pathlib import Path


class Recorder:

    def __init__(self, serializers, base_path="data"):

        ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")

        self.session_path = Path(base_path) / f"session-{ts}"
        self.session_path.mkdir(parents=True)

        self.serializers = serializers

        self.queue = queue.Queue()
        self.files = {}

        self.running = True

        self.thread = threading.Thread(
            target=self._writer_loop,
            daemon=True
        )
        self.thread.start()

    def _get_file(self, stream):

        if stream not in self.files:

            path = self.session_path / f"{stream}.bin"

            self.files[stream] = open(path, "ab")

        return self.files[stream]

    def write(self, stream, ts, data):

        record = {
            "ts": ts,
            "data": data
        }

        self.queue.put((stream, record))

    def _writer_loop(self):

        while self.running or not self.queue.empty():

            stream, record = self.queue.get()

            serializer = self.serializers[stream]

            payload = serializer.serialize(record)

            f = self._get_file(stream)

            f.write(payload)

    def stop(self):

        self.running = False
        self.thread.join()

        for f in self.files.values():
            f.close()