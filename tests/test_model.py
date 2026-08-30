"""Tests for the job model and local queue logic."""

import os
import shutil
import tempfile

import pytest
from remotebatch.model import Job, LocalKey, LocalQueue, Results


@pytest.fixture
def local_queue():
    """Provide a temporary local queue instance for testing.

    Yields:
        LocalQueue: A filesystem-backed queue initialized in a temp directory.
    """
    temp_dir = tempfile.mkdtemp()
    queue = LocalQueue(root_path=temp_dir)
    yield queue
    shutil.rmtree(temp_dir)


def test_job_lifecycle(local_queue):
    """Test the full lifecycle of a Job within a LocalQueue."""
    # Create a job content in a dedicated temporary directory
    with tempfile.TemporaryDirectory() as job_dir:
        job_file_path = os.path.join(job_dir, "test_job.txt")
        with open(job_file_path, "w") as f:
            f.write("test content")

        job_name = "test_job.txt"

        job = Job(jobfile_or_path=job_dir, jobfile=job_name)
        # Use an ID without underscores to avoid legacy parsing logic splitting it
        job.id = "test-job-1"
        job.type = "test"

        # Queue the job
        local_queue.queue_job(job)

        # Verify job is in queue
        jobs = local_queue.allJobs()

        found_job = None
        for j in jobs:
            if j.id == "test-job-1":
                found_job = j
                break

        assert found_job is not None, f"Jobs found: {[j.id for j in jobs]}"
        assert found_job.type == "test"

        # Retrieve files
        retrieve_path = tempfile.mkdtemp()
        try:
            found_job.getFiles(to=retrieve_path)
            # Check if jobfile exists in retrieved path
            expected_file = os.path.join(retrieve_path, job_name)
            assert os.path.exists(expected_file)
            with open(expected_file) as f:
                assert f.read() == "test content"

        finally:
            shutil.rmtree(retrieve_path)

        # Delete job
        local_queue.delete(found_job)

        # Verify deletion
        jobs_after = local_queue.allJobs()
        assert not any(j.id == "test-job-1" for j in jobs_after)


def test_results_lifecycle(local_queue):
    """Test the creation, storage, and retrieval of Results."""
    # Create results
    results = Results(job_id="res-1", status="success")
    results.type = "results"

    # Mock a path for results
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "output.txt"), "w") as f:
            f.write("result data")
        results.path = temp_dir

        # Store results using a key from local queue
        key = LocalKey(local_queue.root_path, "res-1")
        results.store_in_key(key)

    # Verify results are stored
    assert os.path.exists(os.path.join(local_queue.root_path, "res-1"))
    assert os.path.exists(os.path.join(local_queue.root_path, "res-1.meta"))

    # Load it back
    key_loaded = LocalKey(local_queue.root_path, "res-1")
    assert key_loaded.metadata.get("jobid") == "res-1"
    assert key_loaded.metadata.get("jobstatus") == "success"
