"""Tests for queue implementations."""

from unittest.mock import MagicMock

import pytest
from remotebatch import model
from remotebatch.model import BatchQueue, ClientQueue, Job


@pytest.fixture
def mock_boto3(mocker):
    """Mock boto3 library."""
    mock_boto = mocker.patch("remotebatch.model.boto3")
    mock_s3 = MagicMock()
    mock_bucket = MagicMock()
    mock_boto.resource.return_value = mock_s3
    mock_s3.Bucket.return_value = mock_bucket

    # We must patch the boto3 imported at the top of model/__init__ too
    model.boto3 = mock_boto

    return mock_boto, mock_bucket


def test_batch_queue_connect(mock_boto3):
    """Test connecting to a batch queue."""
    _, mock_bucket = mock_boto3
    queue = BatchQueue(bucket="test-bucket")
    assert queue.s3 is not None
    assert queue.bucket == mock_bucket


def test_batch_queue_jobs_generator(mock_boto3, mocker):
    """Test iterating over jobs in BatchQueue."""
    _, mock_bucket = mock_boto3

    # Setup mock objects
    mock_obj1 = MagicMock()
    mock_obj1.key = "job1"
    mock_obj2 = MagicMock()
    mock_obj2.key = "job2"

    mock_bucket.objects.all.return_value = [mock_obj1, mock_obj2]

    mock_full_obj = MagicMock()
    mock_bucket.Object.return_value = mock_full_obj

    # Mock Job instantiation
    mocker.patch("remotebatch.model.QueuedJob")

    queue = BatchQueue()
    jobs = list(queue.jobs())

    expected_len = 2
    assert len(jobs) == expected_len
    assert "job1" in queue.openJobs
    assert "job2" in queue.openJobs


def test_client_queue_connect(mock_boto3):
    """Test ClientQueue connection with network check."""
    # Test online
    queue_online = ClientQueue("/tmp/cq", check_network=lambda: True)
    # The ClientQueue init calls connect on BatchQueue, which sets self.bucket.
    # Since check_network is True, it should connect.
    # We also need to explicitly call connect() if init failed?
    queue_online.connect()
    assert queue_online.isConnected

    # Test offline
    queue_offline = ClientQueue("/tmp/cq", check_network=lambda: False)
    assert not queue_offline.isConnected


def test_client_queue_queue_job_offline(mock_boto3, mocker):
    """Test queuing a job when offline."""
    queue = ClientQueue("/tmp/cq", check_network=lambda: False)
    job = Job()
    job.id = "cj-1"
    job.type = "test"

    # We can't actually store if offline, so ClientQueue caches it
    queue.queue_job(job)

    assert job in queue.local_jobs


def test_client_queue_queue_job_online(mock_boto3, mocker):
    """Test queuing a job when online."""
    _, mock_bucket = mock_boto3
    queue = ClientQueue("/tmp/cq", check_network=lambda: True)
    queue.connect()

    job = Job()
    job.id = "cj-1"
    job.type = "test"

    mock_store = mocker.patch.object(job, "store_in_key")

    queue.queue_job(job)

    mock_store.assert_called_once()
    assert job not in queue.local_jobs
