import os
from typing import Iterable


class ImageValidator:
    def __init__(self, allowed_extensions: Iterable[str]):
        self._allowed = set(allowed_extensions)

    def allowed_file(self, filename: str) -> bool:
        _, ext = os.path.splitext(filename.lower())
        return ext in self._allowed
