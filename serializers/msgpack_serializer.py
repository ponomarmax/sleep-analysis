import msgpack
from .serializer import Serializer


class MsgpackSerializer(Serializer):

    def serialize(self, record) -> bytes:
        record = self.normalize(record)
        payload = msgpack.packb(record, use_bin_type=True)
        size = len(payload).to_bytes(4, "little")
        return size + payload

    def file_extension(self):
        return "msgpack"