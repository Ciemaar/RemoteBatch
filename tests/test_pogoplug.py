from unittest.mock import MagicMock

import pytest

from pogoplug import Connection, Directory, File, PogoplugError


# Mocking requests
@pytest.fixture
def mock_requests(monkeypatch):
    mock_get = MagicMock()
    monkeypatch.setattr("requests.get", mock_get)
    return mock_get


def test_connection_login(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"valtoken": "mock_token"}'
    mock_requests.return_value = mock_response

    c = Connection("test@example.com", "password")
    assert c.valtoken == "mock_token"


def test_connection_login_failure(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"HB-EXCEPTION": {"ecode": "100", "message": "Login failed"}}'
    mock_requests.return_value = mock_response

    with pytest.raises(PogoplugError):
        Connection("test@example.com", "password")


def test_drives(mock_requests):
    # getUser response
    mock_response_user = MagicMock()
    mock_response_user.status_code = 200
    mock_response_user.text = '{"user": {"email": "test@example.com"}}'

    mock_response_drives = MagicMock()
    mock_response_drives.status_code = 200
    mock_response_drives.text = '{"services": [{"deviceid": "d1", "serviceid": "s1"}]}'

    mock_requests.side_effect = [mock_response_user, mock_response_drives]

    c = Connection("token")
    drives = c.drives
    assert len(drives) == 1
    assert isinstance(drives[0], Directory)
    assert drives[0].deviceid == "d1"


def test_files(mock_requests):
    # getUser response
    mock_response_user = MagicMock()
    mock_response_user.status_code = 200
    mock_response_user.text = '{"user": {"email": "test@example.com"}}'

    # First call for drives, second for files
    mock_response_drives = MagicMock()
    mock_response_drives.status_code = 200
    mock_response_drives.text = '{"services": [{"deviceid": "d1", "serviceid": "s1"}]}'

    mock_response_files = MagicMock()
    mock_response_files.status_code = 200
    mock_response_files.text = '{"files": [{"type": "0", "filename": "file1.txt", "fileid": "f1"}]}'

    mock_requests.side_effect = [mock_response_user, mock_response_drives, mock_response_files]

    c = Connection("token")
    drives = c.drives
    files = drives[0].files
    assert "file1.txt" in files
    assert isinstance(files["file1.txt"], File)
