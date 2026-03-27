import time
import pytest
from recorder import Recorder


class DummySerializer:
    def __init__(self):
        self.calls = []

    def file_extension(self):
        return "bin"

    def serialize(self, record):
        self.calls.append(record)
        return b"data"


@pytest.fixture
def serializer():
    return DummySerializer()


@pytest.fixture
def serializers(serializer):
    return {"stream": serializer}


# ========================
# INIT
# ========================

class TestRecorderInit:

    def test_session_created(self, tmp_path):

        r = Recorder(serializers={}, base_path=tmp_path)

        assert r.session_path.exists()
        assert r.session_path.is_dir()

        r.stop()


# ========================
# WRITE
# ========================

class TestRecorderWrite:

    def test_write_adds_to_queue(self, serializers, tmp_path):

        r = Recorder(serializers=serializers, base_path=tmp_path)

        r.write("stream", 123, {"x": 1})

        stream, record = r.queue.get(timeout=1)

        assert stream == "stream"
        assert record["ts"] == 123
        assert record["data"] == {"x": 1}

        r.stop()


# ========================
# WRITER LOOP
# ========================

class TestRecorderWriter:

    def test_writer_serializes(self, serializer, serializers, tmp_path):

        r = Recorder(serializers=serializers, base_path=tmp_path)

        r.write("stream", 1, {"x": 1})

        time.sleep(0.2)

        r.stop()

        assert len(serializer.calls) == 1

    def test_multiple_writes(self, serializer, serializers, tmp_path):

        r = Recorder(serializers=serializers, base_path=tmp_path)

        for i in range(5):
            r.write("stream", i, {})

        time.sleep(0.3)

        r.stop()

        assert len(serializer.calls) == 5


# ========================
# STOP
# ========================

class TestRecorderStop:

    def test_stop_terminates_thread(self, serializers, tmp_path):

        r = Recorder(serializers=serializers, base_path=tmp_path)

        r.stop()

        assert not r.thread.is_alive()

    def test_files_closed(self, serializer, serializers, tmp_path):

        r = Recorder(serializers=serializers, base_path=tmp_path)

        r.write("stream", 1, {})

        time.sleep(0.2)

        r.stop()

        for f in r.files.values():
            assert f.closed


# ========================
# ERRORS
# ========================

class TestRecorderErrors:

    def test_queue_overflow(self, serializers, tmp_path, caplog):
        r = Recorder(serializers=serializers, base_path=tmp_path, queue_size=1)

        with caplog.at_level("ERROR"):
            r.write("stream", 1, {})
            r.write("stream", 2, {})

        assert "Recorder queue overflow" in caplog.text

        r.stop()