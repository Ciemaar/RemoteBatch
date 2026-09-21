"""Tests for view package."""

from remotebatch.model import Job
from remotebatch.view import AddJobDialog, ManagerMain


def test_add_job_dialog(qtbot, mocker):
    """Test AddJobDialog interactions."""
    mock_queue = mocker.MagicMock()
    # Use real Job object since PyQt strictly types parameters
    mock_job = Job("test.ini")
    mock_queue.job_class.return_value = mock_job
    dialog = AddJobDialog(mock_queue)
    qtbot.addWidget(dialog)

    dialog.generalTab.fileNameEdit.setText("povray.ini")
    dialog.generalTab.fileNameEdit.clearFocus()

    mocker.patch("PyQt6.QtWidgets.QDialog.exec", return_value=1)
    mock_notify = mocker.patch("remotebatch.view.notify")

    dialog.exec()
    mock_notify.assert_called_once()
    mock_queue.queue_job.assert_called_once_with(dialog.job)


def test_manager_main(qtbot, mocker):
    """Test ManagerMain interactions."""
    mock_queue = mocker.MagicMock()

    mock_job1 = mocker.MagicMock()
    mock_job1.id = "1"
    mock_job1.type = "povray"
    mock_job1.size = 100
    mock_job1.storage = "remote"

    mock_job2 = mocker.MagicMock()
    mock_job2.id = "2"
    mock_job2.type = "results"
    mock_job2.size = 200
    mock_job2.storage = "local"

    mock_queue.jobs.return_value = []
    mock_queue.allJobs.return_value = [mock_job1, mock_job2]

    window = ManagerMain(mock_queue)
    qtbot.addWidget(window)

    # We must explicitly call _refresh or refresh to load jobs since threaded=True is mocked or doesn't run event loop
    window.refilter()  # or directly call it if it was loaded
    window._refresh()

    assert window.jobListBox.count() == 2

    # filter by results
    window.resultsAct.setChecked(True)
    window.refilter()

    # The first item should be hidden
    assert window.jobListBox.item(0).isHidden()  # type: ignore
    assert not window.jobListBox.item(1).isHidden()  # type: ignore

    # check refresh sets threaded refresh
    mock_runme = mocker.patch("remotebatch.view.RunMe")
    window.refresh()
    assert window.refreshButton.text() == "Refreshing"  # type: ignore
    mock_runme.return_value.start.assert_called_once()


def test_retrieve_job(qtbot, mocker):
    """Test retrieving a job."""
    mock_queue = mocker.MagicMock()
    mock_job = mocker.MagicMock()
    mock_job.id = "123"
    mock_job.size = 100
    mock_job.type = "povray"
    mock_job.storage = "remote"
    mock_queue.allJobs.return_value = [mock_job]

    mock_queue.jobs.return_value = []
    window = ManagerMain(mock_queue)
    qtbot.addWidget(window)

    window._refresh()
    window.jobListBox.setCurrentRow(0)

    mock_notify = mocker.patch("remotebatch.view.notify")

    mocker.patch("remotebatch.view.QtWidgets.QFileDialog.getExistingDirectory", return_value="/tmp/test")
    mocker.patch("remotebatch.view.Path.iterdir", return_value=[])

    window.retrieve()
    mock_notify.assert_called()  # "Retrieving...", "unzipped to..."
    mock_job.getFiles.assert_called_once_with("/tmp/test")
