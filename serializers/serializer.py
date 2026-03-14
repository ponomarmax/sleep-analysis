import json
from dataclasses import asdict, is_dataclass
from datetime import datetime

class Serializer:
    """Базовий клас для всіх серіалізаторів"""

    def serialize(self, record) -> bytes:
        raise NotImplementedError

    def file_extension(self):
        """Розширення файлу за замовчуванням"""
        return "bin"

    def normalize(self, obj):
        """Рекурсивно приводимо об’єкти до простих типів, безпечних для серіалізації"""
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, "__dict__"):
            return {k: self.normalize(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, (list, tuple)):
            return [self.normalize(v) for v in obj]
        if isinstance(obj, dict):
            return {k: self.normalize(v) for k, v in obj.items()}
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj