import queue
import threading
from datetime import datetime
from pathlib import Path


class Recorder:

    def __init__(self, serializers, base_path="data", queue_size=10000):

        ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")

        self.session_path = Path(base_path) / f"session-{ts}"
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.serializers = serializers

        self.queue = queue.Queue(maxsize=queue_size)

        self.files = {}

        self.running = True

        self.thread = threading.Thread(
            target=self._writer_loop,
            daemon=True
        )

        self.thread.start()

    def _get_file(self, stream):

        if stream not in self.files:

            serializer = self.serializers[stream]

            ext = serializer.file_extension()

            path = self.session_path / f"{stream}.{ext}"

            self.files[stream] = open(path, "ab")

        return self.files[stream]

    def write(self, stream, ts, data):

        record = {
            "ts": ts,
            "data": data
        }

        try:
            self.queue.put_nowait((stream, record))
        except queue.Full:
            print("Recorder queue overflow")

    def _writer_loop(self):

        while self.running or not self.queue.empty():

            try:

                stream, record = self.queue.get(timeout=1)

                serializer = self.serializers[stream]

                payload = serializer.serialize(record)

                f = self._get_file(stream)

                f.write(payload)

            except queue.Empty:
                continue

    def stop(self):

        self.running = False

        self.thread.join()

        for f in self.files.values():
            f.flush()
            f.close()