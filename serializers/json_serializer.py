from datetime import datetime
import json
from .serializer import Serializer


class JSONSerializer(Serializer):

    def serialize(self, record) -> bytes:
        record = self.normalize(record)
        return (json.dumps(record, cls=self.UniversalEncoder) + "\n").encode()

    def file_extension(self):
        return "jsonl"

    class UniversalEncoder(json.JSONEncoder):
        def default(self, obj):
            # використовуємо normalize із базового класу
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
    



