from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class StoredObject:
    object_key: str
    content_type: str
    size_bytes: int


class StorageService(Protocol):
    backend_name: str

    def initialize(self) -> None: ...

    def store_image(
        self, *, object_key: str, content: bytes, content_type: str
    ) -> StoredObject: ...

    def fetch_bytes(self, object_key: str) -> bytes: ...


class LocalStorageService:
    backend_name = "local"

    def __init__(self, root: Path):
        self.root = root

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def store_image(self, *, object_key: str, content: bytes, content_type: str) -> StoredObject:
        target = self.root / object_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return StoredObject(
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    def fetch_bytes(self, object_key: str) -> bytes:
        return (self.root / object_key).read_bytes()


class MemoryStorageService:
    backend_name = "memory"

    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def initialize(self) -> None:
        return None

    def store_image(self, *, object_key: str, content: bytes, content_type: str) -> StoredObject:
        self.objects[object_key] = bytes(content)
        return StoredObject(
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    def fetch_bytes(self, object_key: str) -> bytes:
        return self.objects[object_key]
