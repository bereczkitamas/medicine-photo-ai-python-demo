import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from werkzeug.datastructures import FileStorage

from src.app import FileSystem


@pytest.fixture()
def fs() -> FileSystem:
    return FileSystem()


def test_ensure_storage_creates_dir_and_initializes_metadata(fs: FileSystem, tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    metadata = upload_dir / "metadata.json"

    # preconditions: nothing exists yet
    assert not upload_dir.exists()
    assert not metadata.exists()

    fs.ensure_storage(str(upload_dir), str(metadata))

    # directory is created and metadata file is initialized with []
    assert upload_dir.is_dir()
    assert metadata.is_file()
    content = metadata.read_text(encoding="utf-8")
    assert json.loads(content) == []


def test_ensure_storage_does_not_overwrite_existing_metadata(fs: FileSystem, tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    metadata = upload_dir / "metadata.json"

    # seed with non-empty content
    original = [{"id": 1}]
    metadata.write_text(json.dumps(original), encoding="utf-8")

    # Call ensure_storage again; should not overwrite metadata file
    fs.ensure_storage(str(upload_dir), str(metadata))

    after = json.loads(metadata.read_text(encoding="utf-8"))
    assert after == original


def test_save_file_delegates_to_filestorage_save(fs: FileSystem, tmp_path: Path) -> None:
    # Use a Mock that behaves like FileStorage with a .save method
    file_mock = Mock(spec=FileStorage)
    target_path = str(tmp_path / "saved.bin")

    fs.save_file(file_mock, target_path)

    file_mock.save.assert_called_once_with(target_path)


def test_file_size_returns_actual_bytes(fs: FileSystem, tmp_path: Path) -> None:
    # Create a file with known size
    data = b"hello world"  # 11 bytes
    p = tmp_path / "size.txt"
    p.write_bytes(data)

    size = fs.file_size(str(p))
    assert size == len(data)
