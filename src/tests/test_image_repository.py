import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.app import ImageMetadataRepository
from src.app import AppConfig


@pytest.fixture()
def tmp_metadata_file(tmp_path: Path) -> Path:
    # create a temporary metadata file path under tmp directory
    p = tmp_path / "metadata.json"
    # initialize with empty list like FileSystem.ensure_storage would
    p.write_text("[]", encoding="utf-8")
    return p


def test_load_all_reads_json_and_calls_ensure_storage(tmp_metadata_file: Path) -> None:
    # Arrange
    entries = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    tmp_metadata_file.write_text(json.dumps(entries), encoding="utf-8")

    fs = Mock()

    repo = ImageMetadataRepository(str(tmp_metadata_file), fs)

    # Act
    result = repo.load_all()

    # Assert
    assert result == entries
    # ensure_storage must be called with upload dir and metadata path
    fs.ensure_storage.assert_called_once_with(AppConfig.UPLOAD_DIR, str(tmp_metadata_file))


def test_save_all_writes_with_indent(tmp_metadata_file: Path) -> None:
    fs = Mock()
    repo = ImageMetadataRepository(str(tmp_metadata_file), fs)

    data = [{"x": 1}, {"y": 2}]

    repo.save_all(data)

    content = tmp_metadata_file.read_text(encoding="utf-8")
    # verify JSON round-trip and that it looks indented (contains newline and spaces)
    loaded = json.loads(content)
    assert loaded == data
    assert "\n" in content  # pretty printed

    # save_all does not call ensure_storage itself
    fs.ensure_storage.assert_not_called()


def test_append_loads_appends_and_saves(tmp_metadata_file: Path) -> None:
    # seed with existing entries
    tmp_metadata_file.write_text(json.dumps([{"id": 1}]), encoding="utf-8")

    fs = Mock()
    repo = ImageMetadataRepository(str(tmp_metadata_file), fs)

    repo.append({"id": 2})

    # final content should include both entries
    content = tmp_metadata_file.read_text(encoding="utf-8")
    assert json.loads(content) == [{"id": 1}, {"id": 2}]

    # append uses load_all once, which should ensure storage
    fs.ensure_storage.assert_called_once_with(AppConfig.UPLOAD_DIR, str(tmp_metadata_file))
