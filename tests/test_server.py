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
