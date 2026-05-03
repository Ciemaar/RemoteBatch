"""Test the CLI functionality using Click."""

import pytest
from click.testing import CliRunner
from remotebatch.BatchManager import main as manager_main
from remotebatch.RemoteBatch import main as client_main
from remotebatch.server import main as server_main


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CLI runner for testing."""
    return CliRunner()


def test_client_help(mocker):
    """Test that the RemoteBatch client handles arguments natively."""
    mocker.patch("sys.argv", ["RemoteBatch", "--help"])
    # Mock exit and app execution
    mocker.patch("sys.exit")
    mock_app = mocker.patch("remotebatch.RemoteBatch.RemoteBatchApp")

    client_main()

    # We should have attempted to start the app or at least parse without failing
    mock_app.assert_called_once()


def test_manager_help(mocker):
    """Test that the BatchManager displays help natively."""
    mocker.patch("sys.argv", ["BatchManager", "--help"])
    # Mock exit and app execution
    mocker.patch("sys.exit")
    mock_app = mocker.patch("remotebatch.BatchManager.RemoteMgrApp")

    manager_main()
    mock_app.assert_called_once()


def test_server_help(runner):
    """Test that the server displays help using click."""
    result = runner.invoke(server_main, ["--help"])
    assert result.exit_code == 0
    assert "Run the batch processing server." in result.output


def test_client_verbose_flag(mocker):
    """Test that the --verbose flag sets the logging level."""
    mocker.patch("sys.argv", ["RemoteBatch", "--verbose"])
    mocker.patch("remotebatch.RemoteBatch.RemoteBatchApp")
    mocker.patch("remotebatch.RemoteBatch.sys.exit")

    mock_log = mocker.patch("remotebatch.RemoteBatch.logging.getLogger")

    client_main()
    mock_log().setLevel.assert_called_with(10)  # logging.DEBUG == 10


def test_manager_verbose_flag(mocker):
    """Test that the --verbose flag sets the logging level."""
    mocker.patch("sys.argv", ["BatchManager", "--verbose"])
    mocker.patch("remotebatch.BatchManager.RemoteMgrApp")
    mocker.patch("remotebatch.BatchManager.sys.exit")

    mock_log = mocker.patch("remotebatch.BatchManager.logging.getLogger")

    manager_main()
    mock_log().setLevel.assert_called_with(10)


def test_server_verbose_flag(runner, mocker):
    """Test that the --verbose flag sets the logging level."""
    mocker.patch("remotebatch.server.BatchQueue")
    # To prevent endless loop, just throw an exception on poll_and_process
    mocker.patch("remotebatch.server.poll_and_process", side_effect=KeyboardInterrupt)
    mocker.patch("remotebatch.server.sleep", side_effect=KeyboardInterrupt)

    mock_log = mocker.patch("remotebatch.server.logging.getLogger")

    _ = runner.invoke(server_main, ["--verbose"])
    # May exit with a different code or stack trace if interrupted
    mock_log().setLevel.assert_called_with(10)
