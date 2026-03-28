import pytest
import json

from serializers.msgpack_serializer import MsgpackSerializer
from serializers.json_serializer import JSONSerializer
from streaming_session_loader import StreamingSessionLoader

@pytest.fixture
def json_serializer():
    return JSONSerializer()


@pytest.fixture
def msgpack_serializer():
    return MsgpackSerializer()


@pytest.fixture(params=["json", "msgpack"])
def loader_and_serializer(request, tmp_path, json_serializer, msgpack_serializer):
    """Параметризований fixture — DRY для обох форматів."""
    if request.param == "json":
        serializer = json_serializer
    else:
        serializer = msgpack_serializer

    loader = StreamingSessionLoader(str(tmp_path), ["stream1", "stream2"], serializer)
    return loader, serializer, request.param


def test_init(loader_and_serializer):
    loader, serializer, fmt = loader_and_serializer
    assert loader.streams == ["stream1", "stream2"]
    assert all(pos == 0 for pos in loader.positions.values())
    assert loader.serializer is serializer


def test_read_new_no_files(loader_and_serializer):
    loader, _, _ = loader_and_serializer
    assert loader.read_new() == {}


def test_streaming_scenario(loader_and_serializer, tmp_path):
    loader, serializer, fmt = loader_and_serializer
    session_path = tmp_path

    file1 = session_path / f"stream1.{serializer.file_extension()}"
    file2 = session_path / f"stream2.{serializer.file_extension()}"

    # Початкові дані
    records1 = [{"id": 1, "value": "first"}, {"id": 2}]
    records2 = [{"id": 10}]

    if fmt == "json":
        file1.write_text("".join(json.dumps(r) + "\n" for r in records1), encoding="utf-8")
        file2.write_text("".join(json.dumps(r) + "\n" for r in records2), encoding="utf-8")
    else:
        with open(file1, "wb") as f:
            for r in records1:
                f.write(serializer.serialize(r))
        with open(file2, "wb") as f:
            for r in records2:
                f.write(serializer.serialize(r))

    # Перше читання
    result = loader.read_new()
    assert "stream1" in result
    assert "stream2" in result
    assert len(result["stream1"]) == 2
    assert len(result["stream2"]) == 1

    # Додаємо нові дані (streaming)
    new_record = {"id": 3, "value": "new"}
    with open(file1, "ab" if fmt == "msgpack" else "a", encoding=None if fmt == "msgpack" else "utf-8") as f:
        if fmt == "json":
            f.write(json.dumps(new_record) + "\n")
        else:
            f.write(serializer.serialize(new_record))

    result2 = loader.read_new()
    assert result2 == {"stream1": [new_record]}

    # Немає нових даних
    assert loader.read_new() == {}


def test_error_handling(loader_and_serializer, tmp_path):
    """Перевіряємо graceful handling помилок: один поганий запис не ламає весь stream."""
    loader, serializer, fmt = loader_and_serializer
    bad_file = tmp_path / f"stream1.{serializer.file_extension()}"

    if fmt == "json":
        # Один валідний → поганий → ще один валідний
        bad_file.write_text(
            '{"valid": 1}\n'
            'this is not valid json at all\n'
            '{"valid": 2, "ok": true}\n',
            encoding="utf-8"
        )
    else:  # msgpack
        with open(bad_file, "wb") as f:
            f.write(serializer.serialize({"valid": 1}))
            f.write(b"this_is_truncated_and_invalid")   # симулюємо пошкодження
            # Другий валідний запис після пошкодженого вже не буде прочитаний (msgpack)
            # (бо після помилки ми break'аємося)

    result = loader.read_new()

    assert "stream1" in result
    records = result["stream1"]

    if fmt == "json":
        # Має прочитати обидва валідні записи, пропустивши поганий
        assert len(records) == 2
        assert records[0] == {"valid": 1}
        assert records[1] == {"valid": 2, "ok": True}
    else:
        # Для msgpack після першого валідного йде пошкодження → читаємо тільки перший
        assert len(records) == 1
        assert records[0] == {"valid": 1}