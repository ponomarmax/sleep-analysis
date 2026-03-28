import json
from pathlib import Path
from typing import Any, Dict, List
import msgpack
from serializers.serializer import Serializer


class StreamingSessionLoader:
    """Supports pluggable serializers via composition."""

    def __init__(self, session_path: str, streams: List[str], serializer: Serializer):
        self.session_path = Path(session_path).resolve()
        self.streams = list(streams)
        self.serializer = serializer
        self.positions: Dict[str, int] = {s: 0 for s in streams}

        if not all(hasattr(serializer, m) for m in ("deserialize", "file_extension")):
            raise TypeError("Serializer must implement deserialize() and file_extension()")

    def _get_file(self, stream_name: str) -> Path | None:
        """Find file by exact extension."""
        ext = self.serializer.file_extension()
        candidates = list(self.session_path.glob(f"{stream_name}.{ext}"))
        if not candidates:
            return None
        if len(candidates) > 1:
            pass
        return candidates[0]

    def read_new(self) -> Dict[str, List[Any]]:
        """Return only new records since last read."""
        result: Dict[str, List[Any]] = {}

        for stream_name in self.streams:
            file_path = self._get_file(stream_name)
            if file_path is None:
                continue

            new_records: List[Any] = []

            try:
                self._read_stream(file_path, new_records, stream_name)
                if new_records:
                    result[stream_name] = new_records

            except (json.JSONDecodeError, msgpack.UnpackException, ValueError, OSError):
                continue

        return result

    def _read_stream(self, file_path: Path, new_records: List[Any], stream_name: str):
        """Unified read entrypoint."""
        is_binary = self.serializer.file_extension() == "msgpack"

        mode = "rb" if is_binary else "r"
        encoding = None if is_binary else "utf-8"

        with open(file_path, mode=mode, encoding=encoding) as f:
            f.seek(self.positions[stream_name])

            if is_binary:
                self._read_msgpack_stream(f, new_records, stream_name)
            else:
                self._read_jsonl_stream(f, new_records, stream_name)

            self.positions[stream_name] = f.tell()

    def _read_jsonl_stream(self, f, new_records: List[Any], stream_name: str):
        """Read JSONL line by line, skipping invalid lines."""
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            try:
                record = self.serializer.deserialize(line.encode("utf-8"))
                new_records.append(record)
            except (json.JSONDecodeError, ValueError):
                continue

    def _read_msgpack_stream(self, f, new_records: List[Any], stream_name: str):
        """Read msgpack records with length-prefix framing."""
        while True:
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                break

            try:
                size = int.from_bytes(size_bytes, "little")
                payload = f.read(size)

                if len(payload) < size:
                    break

                full_chunk = size_bytes + payload
                record = self.serializer.deserialize(full_chunk)
                new_records.append(record)

            except (msgpack.UnpackException, ValueError):
                break