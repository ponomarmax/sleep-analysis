class Serializer:
    def serialize(self, record) -> bytes:
        raise NotImplementedError
    
import json
from dataclasses import asdict, is_dataclass

class JSONSerializer:
    def serialize(self, record) -> bytes:
        return (json.dumps(record, cls=self.UniversalEncoder) + "\n").encode()

    class UniversalEncoder(json.JSONEncoder):
        def default(self, obj):
            if is_dataclass(obj):
                return asdict(obj)
            if hasattr(obj, "__dict__"):
                # рекурсивно перетворюємо усі поля
                return {k: self.default(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, (list, tuple)):
                return [self.default(v) for v in obj]
            if isinstance(obj, dict):
                return {k: self.default(v) for k, v in obj.items()}
            return str(obj)
    
import struct

class BinaryPPGSerializer:

    def serialize(self, record):

        ts = record["ts"]
        samples = record["data"]["samples"]

        payload = struct.pack("<QH", ts, len(samples))

        for s in samples:
            payload += struct.pack("<H", s)

        return payload