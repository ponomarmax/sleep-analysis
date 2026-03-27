import msgpack
from .serializer import Serializer


class MsgpackSerializer(Serializer):

    def serialize(self, record) -> bytes:
        record = self.normalize(record)
        payload = msgpack.packb(record, use_bin_type=True)
        size = len(payload).to_bytes(4, "little")
        return size + payload
    
    def deserialize(self, data: bytes):
        size = int.from_bytes(data[:4], "little")
        payload = data[4:4+size]
        return msgpack.unpackb(payload, raw=False)

    def file_extension(self):
        return "msgpack"