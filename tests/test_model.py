import pytest
import os
import shutil
import tempfile
from model import LocalQueue, Job, Results, LocalKey

@pytest.fixture
def local_queue():
    temp_dir = tempfile.mkdtemp()
    queue = LocalQueue(root_path=temp_dir)
    yield queue
    shutil.rmtree(temp_dir)

def test_job_lifecycle(local_queue):
    # Create a job content in a dedicated temporary directory
    # The previous error was because we used NamedTemporaryFile which puts it in /tmp,
    # and then we tried to archive dirname(f.name) which is /tmp, hitting permission errors.

    with tempfile.TemporaryDirectory() as job_dir:
        job_file_path = os.path.join(job_dir, "test_job.txt")
        with open(job_file_path, "w") as f:
            f.write("test content")

        job_name = "test_job.txt"

        job = Job(jobfile_or_path=job_dir, jobfile=job_name)
        job.id = "test_job_1"
        job.type = "test"

        # Queue the job
        local_queue.queue_job(job)

        # Verify job is in queue
        jobs = local_queue.allJobs()

        found_job = None
        for j in jobs:
            if j.id == "test_job_1":
                found_job = j
                break

        assert found_job is not None
        assert found_job.type == "test"

        # Retrieve files
        retrieve_path = tempfile.mkdtemp()
        try:
             files_path = found_job.getFiles(to=retrieve_path)
             # Check if jobfile exists in retrieved path
             # The jobfile was added with arcname=self.jobfile, which is just the filename.
             # So jobfile should be at retrieve_path/job_name

             expected_file = os.path.join(retrieve_path, job_name)
             assert os.path.exists(expected_file)
             with open(expected_file, 'r') as f:
                 assert f.read() == "test content"

        finally:
             shutil.rmtree(retrieve_path)

        # Delete job
        local_queue.delete(found_job)

        # Verify deletion
        jobs_after = local_queue.allJobs()
        assert not any(j.id == "test_job_1" for j in jobs_after)


def test_results_lifecycle(local_queue):
    # Create results
    results = Results(id="res_1", status="success")
    results.type = "results"

    # Mock a path for results
    with tempfile.TemporaryDirectory() as temp_dir:
         with open(os.path.join(temp_dir, "output.txt"), "w") as f:
             f.write("result data")
         results.path = temp_dir

         # Store results using a key from local queue
         key = LocalKey(local_queue.root_path, "res_1")
         results.store_in_key(key)

    # Verify results are stored
    # Check if file exists
    assert os.path.exists(os.path.join(local_queue.root_path, "res_1"))
    assert os.path.exists(os.path.join(local_queue.root_path, "res_1.meta"))

    # Load it back
    key_loaded = LocalKey(local_queue.root_path, "res_1")
    assert key_loaded.metadata.get("jobid") == "res_1"
    assert key_loaded.metadata.get("jobstatus") == "success"
