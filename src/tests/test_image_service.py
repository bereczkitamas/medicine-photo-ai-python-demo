import os
from datetime import datetime
from unittest.mock import Mock, call

import pytest
from werkzeug.datastructures import FileStorage

from app.models.image_entry import Stage
from app.services.image_service import ImageService


@pytest.fixture()
def mock_repo() -> Mock:
    repo = Mock()
    repo.load_all.return_value = []
    return repo


@pytest.fixture()
def mock_fs(tmp_path) -> Mock:
    fs = Mock()
    # ensure_storage should create directory and metadata file normally; mocked here
    fs.ensure_storage.side_effect = lambda upload_dir, metadata_file: None
    # file_size returns a fixed value in tests
    fs.file_size.return_value = 1234
    # save_file writes to a temp file path to make size checks plausible if needed
    def _save_file(file: FileStorage, path: str):
        # emulate writing
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(b"data")
    fs.save_file.side_effect = _save_file
    return fs


@pytest.fixture()
def mock_validator() -> Mock:
    v = Mock()
    v.allowed_file.side_effect = lambda fn: os.path.splitext(fn)[1].lower() in {'.png', '.jpg'}
    return v


@pytest.fixture()
def service(tmp_path, mock_repo, mock_fs, mock_validator) -> ImageService:
    return ImageService(upload_dir=str(tmp_path), repo=mock_repo, fs=mock_fs, validator=mock_validator)


def test_list_images_defaults_stage_to_uploaded(service: ImageService, mock_repo) -> None:
    mock_repo.load_all.return_value = [
        {'id': '1', 'medicine_name': 'foo', 'version': 1},  # no stage
        {'id': '2', 'medicine_name': 'bar', 'version': 2, 'stage': ''},  # empty stage
        {'id': '3', 'medicine_name': 'baz', 'version': 3, 'stage': Stage.PROCESSED.value},
    ]

    result = service.list_images()

    assert result[0]['stage'] == Stage.UPLOADED.value
    assert result[1]['stage'] == Stage.UPLOADED.value
    assert result[2]['stage'] == Stage.PROCESSED.value


def test_filter_images_by_medicine_and_stage(service: ImageService, mock_repo) -> None:
    mock_repo.load_all.return_value = [
        {'id': '1', 'medicine_name': 'Panadol', 'version': 1},
        {'id': '2', 'medicine_name': 'Aspirin', 'version': 1, 'stage': Stage.PROCESSED.value},
        {'id': '3', 'medicine_name': 'aspirin forte', 'version': 2},
        {'id': '4', 'medicine_name': 'Ibuprofen', 'version': 1, 'stage': Stage.ARCHIVED.value},
    ]

    # medicine substring, case-insensitive
    r1 = service.filter_images('spir', None)
    ids_r1 = {e['id'] for e in r1}
    assert ids_r1 == {'2', '3'}

    # stage filter (also defaults missing stages to UPLOADED)
    r2 = service.filter_images(None, Stage.ARCHIVED.value)
    assert [e['id'] for e in r2] == ['4']

    # both filters
    r3 = service.filter_images('asp', Stage.PROCESSED.value)
    assert [e['id'] for e in r3] == ['2']


def test_is_allowed_delegates_to_validator(service: ImageService, mock_validator) -> None:
    assert service.is_allowed('x.png') is True
    assert service.is_allowed('x.gif') is False
    # ensure called
    assert mock_validator.allowed_file.call_args_list == [call('x.png'), call('x.gif')]


def test_determine_version_happy_path(service: ImageService, mock_repo) -> None:
    mock_repo.load_all.return_value = [
        {'medicine_name': 'Aspirin', 'version': 1},
        {'medicine_name': 'aspirin', 'version': 3},
        {'medicine_name': 'Other', 'version': 10},
        {'medicine_name': 'aspirin', 'version': '2'},  # string int
        {'medicine_name': 'aspirin', 'version': 'oops'},  # invalid -> treated as 0
    ]

    assert service.determine_version('ASPIRIN') == 4


def test_determine_version_on_repo_error_returns_1(service: ImageService, mock_repo) -> None:
    mock_repo.load_all.side_effect = RuntimeError('disk error')
    assert service.determine_version('anything') == 1


class DummyFile(FileStorage):
    def __init__(self, filename: str, content: bytes = b'data', mimetype: str = 'image/png'):
        super().__init__(stream=None, filename=filename, content_type=mimetype)
        self._content = content

    def save(self, dst) -> None:
        # emulate writing content
        with open(dst, 'wb') as f:
            f.write(self._content)


def test_save_upload_success(service: ImageService, mock_repo, mock_fs) -> None:
    file = DummyFile('My Photo.PNG', content=b'abcdef', mimetype='image/png')

    # prepare repository to return some existing entries for version calculation
    mock_repo.load_all.return_value = [
        {'medicine_name': 'Panadol', 'version': 2},
        {'medicine_name': 'panadol', 'version': 5},
    ]

    result = service.save_upload(file, lambda name: f"/files/{name}", '  Panadol  ')

    # basic field assertions
    assert result['original_name'] == 'My_Photo.PNG'
    assert result['stored_name'] and result['stored_name'].lower().endswith('.png')
    assert result['url'].startswith('/files/')
    assert result['content_type'] == 'image/png'
    assert result['medicine_name'] == 'Panadol'
    assert result['version'] == 6  # next after max 5
    assert result['stage'] == Stage.UPLOADED.value

    # uploaded_at ISO-like
    dt = result['uploaded_at'].rstrip('Z')
    # This will raise if format invalid
    datetime.fromisoformat(dt)

    # verify the file saved and size queried
    assert mock_fs.ensure_storage.called
    assert mock_fs.save_file.called
    assert mock_fs.file_size.called
    # verify the repo append called with the created entry dict
    assert mock_repo.append.called


def test_save_upload_errors(service: ImageService) -> None:
    # empty filename
    with pytest.raises(ValueError, match='No selected file'):
        service.save_upload(DummyFile(''), lambda string: string, 'X')

    # unsupported extension
    with pytest.raises(ValueError, match='Unsupported file type'):
        service.save_upload(DummyFile('file.gif'), lambda string: string, 'X')

    # missing medicine name
    with pytest.raises(ValueError, match='Medicine name is required'):
        service.save_upload(DummyFile('file.png'), lambda string: string, '   ')


def test_promote_stage_and_persist(service: ImageService, mock_repo) -> None:
    entries = [
        {'id': '1', 'stage': Stage.UPLOADED},
        {'id': '2', 'stage': Stage.PROCESSED},
        {'id': '3', 'stage': Stage.ARCHIVED},
    ]
    mock_repo.load_all.return_value = entries

    updated = service.promote_stage('1')
    assert any(e['id'] == '1' and e['stage'] == Stage.PROCESSED.value for e in updated)
    assert mock_repo.save_all.called

    # promote processed to archived
    mock_repo.save_all.reset_mock()
    mock_repo.load_all.return_value = entries
    updated2 = service.promote_stage('2')
    assert any(e['id'] == '2' and e['stage'] == Stage.ARCHIVED.value for e in updated2)
    assert mock_repo.save_all.called

    # archived stays archived
    mock_repo.save_all.reset_mock()
    mock_repo.load_all.return_value = entries
    updated3 = service.promote_stage('3')
    assert any(e['id'] == '3' and e['stage'] == Stage.ARCHIVED.value for e in updated3)
    assert mock_repo.save_all.called


def test_promote_stage_id_not_found_no_persist(service: ImageService, mock_repo) -> None:
    entries = [
        {'id': '1'},  # missing stage -> defaults on return
    ]
    mock_repo.load_all.return_value = entries

    updated = service.promote_stage('nope')
    # no save_all
    assert not mock_repo.save_all.called
    # default stage applied on return
    assert updated[0]['stage'] == Stage.UPLOADED
