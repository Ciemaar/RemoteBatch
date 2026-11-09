"""Tests for the job processing server."""

import os
import tempfile

from remotebatch.model import Job, Results
from remotebatch.server import processJob


def test_process_job_povray(mocker):
    """Test processing a Povray job."""
    mock_subprocess = mocker.patch("subprocess.call", return_value=0)

    with tempfile.TemporaryDirectory() as job_dir:
        job_file_path = os.path.join(job_dir, "test.pov")
        with open(job_file_path, "w") as f:
            f.write("camera {}")

        job = Job(jobfile_or_path=job_dir, jobfile="test.pov")
        job.id = "pov-1"
        job.type = "povray"
        job.step = 0

        # We also need to mock getFiles since we are not putting it in a tarball
        mocker.patch.object(job, "getFiles", return_value=job_dir)
        mocker.patch.object(Results, "mkTar")

        result = processJob(job)

        assert result is not None
        assert isinstance(result, Results)
        assert result.id == "pov-1_1"
        assert result.status == 0
        mock_subprocess.assert_called_once()
        assert os.path.exists(os.path.join(job_dir, "output"))


def test_process_job_results():
    """Test processing a results job (should return None)."""
    job = Job()
    job.id = "res-1"
    job.type = "results"

    result = processJob(job)
    assert result is None


def test_process_job_unknown(mocker):
    """Test processing an unknown job type."""
    job = Job()
    job.id = "unk-1"
    job.type = "unknown_type"

    mocker.patch.object(job, "getFiles", return_value="/tmp/mockdir")
    mock_mark_complete = mocker.patch.object(job, "mark_complete")
    mocker.patch("os.listdir", return_value=[])

    result = processJob(job)
    assert result is None
    # type exists, so mark_complete isn't called based on code:
    # if not job.type: job.mark_complete()
    mock_mark_complete.assert_not_called()


def test_process_job_no_type(mocker):
    """Test processing a job with no type."""
    job = Job()
    job.id = "notype-1"
    job.type = None

    mocker.patch.object(job, "getFiles", return_value="/tmp/mockdir")
    mock_mark_complete = mocker.patch.object(job, "mark_complete")
    mocker.patch("os.listdir", return_value=[])

    result = processJob(job)
    assert result is None
    mock_mark_complete.assert_called_once()


def test_poll_and_process_already_complete(mocker):
    """Test poll_and_process skips already completed jobs."""
    batch_queue = mocker.MagicMock()
    result_queue = mocker.MagicMock()

    mock_job = mocker.MagicMock()
    mock_job.isComplete = True

    batch_queue.jobs.return_value = [mock_job]

    from remotebatch.server import poll_and_process

    poll_and_process(batch_queue, result_queue)

    # processJob should not be called since it's already complete
    mock_job.getFiles.assert_not_called()


def test_poll_and_process_success(mocker):
    """Test poll_and_process successfully executes and links next job."""
    batch_queue = mocker.MagicMock()
    result_queue = mocker.MagicMock()

    mock_job = mocker.MagicMock()
    mock_job.isComplete = False

    batch_queue.jobs.return_value = [mock_job]

    mocker.patch("remotebatch.server.processJob", return_value=mocker.MagicMock())

    from remotebatch.server import poll_and_process

    poll_and_process(batch_queue, result_queue)

    mock_job.mark_complete.assert_called_once()
    mock_job.cleanup.assert_called_once()
    result_queue.queue_job.assert_called_once()


def test_poll_and_process_exception(mocker):
    """Test poll_and_process handles exceptions smoothly."""
    batch_queue = mocker.MagicMock()
    result_queue = mocker.MagicMock()

    mock_job = mocker.MagicMock()
    mock_job.isComplete = False

    batch_queue.jobs.return_value = [mock_job]

    mocker.patch("remotebatch.server.processJob", side_effect=ValueError("Test Exception"))

    from remotebatch.server import poll_and_process

    poll_and_process(batch_queue, result_queue)

    # mark_complete should NOT be called on failure
    mock_job.mark_complete.assert_not_called()
    # but cleanup still runs
    mock_job.cleanup.assert_called_once()


def test_processJob_povray(mocker):
    """Test processJob with povray job type."""
    from remotebatch.server import processJob

    mock_job = mocker.MagicMock()
    mock_job.type = "povray"
    mock_job.jobfile = "test.ini"
    mock_job.path = "/tmp/test"
    mock_job.id = "123"
    mock_job.step = 0

    mock_subprocess = mocker.patch("remotebatch.server.subprocess.call", return_value=0)
    mock_results = mocker.patch("remotebatch.server.Results")
    mocker.patch("remotebatch.server.Path")

    result = processJob(mock_job)

    mock_job.getFiles.assert_called_once()
    mock_subprocess.assert_called_once_with(("/usr/bin/povray", "test.ini"), cwd="/tmp/test")
    mock_results.assert_called_once()
    assert mock_results.call_args[0][0] == "123_1"
    assert mock_results.call_args[0][2] == 0
    mock_results.return_value.mkTar.assert_called_once()
    assert result == mock_results.return_value


def test_processJob_results(mocker):
    """Test processJob skips results type."""
    from remotebatch.server import processJob

    mock_job = mocker.MagicMock()
    mock_job.type = "results"

    result = processJob(mock_job)
    assert result is None


def test_processJob_unknown(mocker):
    """Test processJob handles unknown job types."""
    from remotebatch.server import processJob

    mock_job = mocker.MagicMock()
    mock_job.type = "unknown"

    mock_job.getFiles.return_value = "/tmp/unzipped"

    result = processJob(mock_job)

    mock_job.getFiles.assert_called_once()
    # Since it does not match known types, it returns None
    assert result is None
