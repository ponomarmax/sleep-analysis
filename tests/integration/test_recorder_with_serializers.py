import time
import pytest
from recorder import Recorder
from serializers.json_serializer import JSONSerializer
from serializers.msgpack_serializer import MsgpackSerializer


@pytest.mark.parametrize("serializer_cls", [
    JSONSerializer,
    MsgpackSerializer,
])
def test_recorder_with_serializer(tmp_path, serializer_cls):

    serializer = serializer_cls()

    r = Recorder(
        serializers={"s": serializer},
        base_path=tmp_path
    )

    records = [{"i": i} for i in range(3)]

    for rec in records:
        r.write("s", rec["i"], rec)

    time.sleep(0.3)
    r.stop()

    file = list(r.session_path.glob("*"))[0]

    content = file.read_bytes()

    # JSON
    if serializer.file_extension() == "jsonl":
        lines = content.splitlines()
        parsed = [serializer.deserialize(line) for line in lines]

    # MSGPACK
    else:
        parsed = []
        i = 0
        while i < len(content):
            size = int.from_bytes(content[i:i+4], "little")
            chunk = content[i:i+4+size]
            parsed.append(serializer.deserialize(chunk))
            i += 4 + size

    assert [r["data"] for r in parsed] == records