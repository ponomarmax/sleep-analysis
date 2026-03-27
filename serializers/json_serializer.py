from datetime import datetime
import json

# from rich.pretty import data
from .serializer import Serializer


class JSONSerializer(Serializer):

    def serialize(self, record) -> bytes:
        record = self.normalize(record)
        # return (json.dumps(record, cls=self.UniversalEncoder) + "\n").encode()
        return (json.dumps(record) + "\n").encode()
    def deserialize(self, data: bytes):
        return json.loads(data)

    def file_extension(self):
        return "jsonl"

    # class UniversalEncoder(json.JSONEncoder):
    #     def default(self, obj):
    #         # використовуємо normalize із базового класу
    #         if isinstance(obj, datetime):
    #             return obj.isoformat()
    #         return str(obj)
    



