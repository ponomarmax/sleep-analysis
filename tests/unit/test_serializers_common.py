import pytest
from datetime import datetime
from serializers.json_serializer import JSONSerializer
from serializers.msgpack_serializer import MsgpackSerializer

@pytest.mark.parametrize("serializer", [
    JSONSerializer(),
    MsgpackSerializer(),
])
def test_round_trip(serializer):
    record = {"a": 1, "b": [1, 2, 3]}

    data = serializer.serialize(record)
    restored = serializer.deserialize(data)

    assert restored == record

@pytest.mark.parametrize("serializer", [
    JSONSerializer(),
    MsgpackSerializer(),
])
def test_handles_datetime(serializer):
    record = {"ts": datetime(2020, 1, 1)}

    data = serializer.serialize(record)
    restored = serializer.deserialize(data)

    assert restored["ts"] == "2020-01-01T00:00:00"