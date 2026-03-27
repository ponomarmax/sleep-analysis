from serializers.msgpack_serializer import MsgpackSerializer

def test_msgpack_has_length_prefix():
    s = MsgpackSerializer()

    data = s.serialize({"a": 1})

    size = int.from_bytes(data[:4], "little")

    assert size == len(data) - 4