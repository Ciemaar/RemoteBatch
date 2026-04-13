"""Tests for tabdialog.py."""

from PyQt6 import QtWidgets
from remotebatch.tabdialog import TabDialog


def test_tabdialog(qtbot, mocker):
    """Test that TabDialog instantiates and adds tabs correctly."""
    dialog = TabDialog("test.ini")
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Tab Dialog"
    # General, Permissions, Applications
    assert dialog.findChild(QtWidgets.QTabWidget).count() == 3


def test_tabdialog_cli(qtbot, mocker):
    """Test the CLI for tabdialog."""
    from click.testing import CliRunner
    from remotebatch.tabdialog import main

    runner = CliRunner()
    mocker.patch("remotebatch.tabdialog.QtWidgets.QApplication")
    mocker.patch("remotebatch.tabdialog.TabDialog.exec", return_value=0)
    mocker.patch("sys.exit")

    result = runner.invoke(main, ["test.ini"])
    assert result.exit_code == 0
