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
    from remotebatch.tabdialog import main

    mocker.patch("remotebatch.tabdialog.QtWidgets.QApplication")
    mocker.patch("remotebatch.tabdialog.TabDialog.exec", return_value=0)
    mocker.patch("sys.exit")
    mocker.patch("sys.argv", ["tabdialog", "test.ini"])

    mocker.patch("remotebatch.tabdialog.QCommandLineParser.process")
    mocker.patch("remotebatch.tabdialog.QCommandLineParser.positionalArguments", return_value=["test.ini"])

    # We replaced click with QCommandLineParser in the PR feedback, so we just call main directly
    main()
