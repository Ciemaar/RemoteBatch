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


def test_client_help(runner):
    """Test that the RemoteBatch client displays help."""
    result = runner.invoke(client_main, ["--help"])
    assert result.exit_code == 0
    assert "Start the Remote Batch GUI application to submit jobs." in result.output


def test_manager_help(runner):
    """Test that the BatchManager displays help."""
    result = runner.invoke(manager_main, ["--help"])
    assert result.exit_code == 0
    assert "Start the Remote Batch Manager application." in result.output


def test_server_help(runner):
    """Test that the server displays help."""
    result = runner.invoke(server_main, ["--help"])
    assert result.exit_code == 0
    assert "Run the batch processing server." in result.output


def test_client_verbose_flag(runner, mocker):
    """Test that the --verbose flag sets the logging level."""
    # Since the CLI requires X11 to fully initialize the PyQt6 app if we actually run it without help,
    # we'll mock sys.exit or QApplication to prevent it from crashing in headless environments.
    # However, click.testing.CliRunner isolates sys.exit.
    # Let's mock the GUI app init.
    mocker.patch("remotebatch.RemoteBatch.RemoteBatchApp")
    mocker.patch("remotebatch.RemoteBatch.sys.exit")

    mock_log = mocker.patch("remotebatch.RemoteBatch.logging.getLogger")

    result = runner.invoke(client_main, ["--verbose"])
    assert result.exit_code == 0
    mock_log().setLevel.assert_called_with(10)  # logging.DEBUG == 10


def test_manager_verbose_flag(runner, mocker):
    """Test that the --verbose flag sets the logging level."""
    mocker.patch("remotebatch.BatchManager.RemoteMgrApp")
    mocker.patch("remotebatch.BatchManager.sys.exit")

    mock_log = mocker.patch("remotebatch.BatchManager.logging.getLogger")

    result = runner.invoke(manager_main, ["--verbose"])
    assert result.exit_code == 0
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
