
from serializers.json_serializer import JSONSerializer


def test_json_line_format():
    s = JSONSerializer()

    data = s.serialize({"a": 1})

    assert data.endswith(b"\n")