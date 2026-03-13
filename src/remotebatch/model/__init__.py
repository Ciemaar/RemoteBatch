"""Model package containing core Queue and Job logic."""

import contextlib
import io
import logging
import pickle
import tarfile
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path

# Try to import boto3, but allow it to fail if we are just testing local queue
try:
    import boto3
except ImportError:
    boto3 = None

from remotebatch.app_secrets import REMOTE_BATCH_BUCKET

log = logging.getLogger(__name__)


class Job:
    """Represents a unit of work or payload to be processed.

    A Job encapsulates the data files required for execution,
    metadata about the job type, and logic for serialization
    into a tarball format for storage in a queue.
    """

    def __init__(self, jobfile_or_path: str = "./", jobfile: str | None = None, s3key: object | None = None) -> None:
        """Initialize a Job.

        Args:
            jobfile_or_path (str, optional): The base path or the specific file for the job. Defaults to "./".
            jobfile (str | None, optional): The specific job file within the path. Defaults to None.
            s3key (object | None, optional): An existing S3 key or LocalKey. Defaults to None.
        """
        self.step = 0
        self.id: str
        self.type: str | None
        self.size: int
        self._arcpath: str
        self.next_job: str | None
        self.path: str | None = None
        self.jobroot: str | None = None
        self.jobfile: str | None = None
        self._key: object | None = s3key
        self.jobpath: str | None = None
        self.status: str | None = None

        if s3key:
            metadata = self._get_metadata(s3key)

            self.jobfile = metadata.get("jobfile")
            self.id = metadata.get("jobid", "unknown")
            if "_" in self.id:
                parts = self.id.split("_")
                self.id = parts[0]
                if len(parts) > 1 and parts[1].isdigit():
                    self.step = int(parts[1])
                else:
                    self.step = 0

            self.type = metadata.get("jobtype")
            self.next_job = metadata.get("next_job")

            if hasattr(s3key, "content_length"):
                self.size = s3key.content_length
            else:
                self.size = 0

            self._arcpath = metadata.get("arcpath", "")
            if not self._arcpath:
                if self.type == "results":
                    self._arcpath = "output"
                else:
                    self._arcpath = "jobroot"

        else:
            self.id = str(uuid.uuid1())
            self.size = 0
            self.type = None
            self.set_jobfile(jobfile_or_path, jobfile)
            self._arcpath = "jobroot"
            self.next_job = None

    def _get_metadata(self, key: object) -> dict[str, object]:
        """Extract metadata from an S3 key or LocalKey.

        Args:
            key (object): The storage key object.

        Returns:
            dict[str, object]: The extracted metadata dictionary.
        """
        if hasattr(key, "metadata"):
            return key.metadata
        if hasattr(key, "load"):
            with contextlib.suppress(Exception):
                key.load()
                return key.metadata
        return {}

    def __str__(self) -> str:
        """Return a string representation of the Job.

        Returns:
            str: Formatted string containing the job ID, path, and job file.
        """
        ret = f"id: {self.id}"
        if self.path:
            ret += f"path:\n{self.path}"
        if self.jobfile:
            ret += f"\n{self.jobfile}"
        return ret

    def cleanup(self) -> None:
        """Clean up local temporary files associated with the job."""
        if self.path:
            self.path = None

    def getFiles(self, to: str | None = None) -> str:
        """Retrieve and extract the files from this job.

        Downloads the job payload from storage and extracts the tarball
        into the specified directory or a temporary directory.

        Args:
            to (str | None, optional): The destination path for extraction. Defaults to None,
                which creates a temporary directory.

        Returns:
            str: The path where the job files were extracted (the job root).
        """
        if self.jobroot is not None:
            return self.jobroot

        tmpTar = io.BytesIO()

        if self._key and hasattr(self._key, "download_fileobj"):
            self._key.download_fileobj(tmpTar)

        tmpTar.seek(0)

        try:
            with tarfile.open(fileobj=tmpTar, mode="r:gz") as tar:
                if not to:
                    self.path = tempfile.mkdtemp()
                else:
                    self.path = to

                tar.extractall(
                    self.path,
                    members=[member for member in tar.getmembers() if member.name.startswith(self._arcpath)],
                    filter="data",
                )

                if self.jobfile:
                    with contextlib.suppress(KeyError):
                        tar.extract(self.jobfile, self.path, filter="data")

                self.jobroot = str(Path(self.path) / self._arcpath)
                return self.jobroot
        except tarfile.ReadError:
            if not to:
                self.path = tempfile.mkdtemp()
            else:
                self.path = to
            self.jobroot = str(Path(self.path) / self._arcpath)
            return self.jobroot

    def mark_complete(self, next_job: "Job | None" = None) -> None:
        """Mark the job as complete and link the next step if applicable.

        Args:
            next_job (Job | None, optional): The job representing the next processing step. Defaults to None.
        """
        self.cleanup()

    @property
    def isComplete(self) -> bool:
        """Check if the job processing is complete.

        Returns:
            bool: True if complete, False otherwise.
        """
        return False

    def delete(self) -> None:
        """Delete the job from the storage queue."""
        if self._key and hasattr(self._key, "delete"):
            self._key.delete()

    def store_in_key(self, s3key: object) -> None:
        """Serialize the job payload and upload it to the storage queue.

        Args:
            s3key (object): The storage key object (e.g., boto3 Object or LocalKey) to upload to.
        """
        bundleFile = self.mkTar()
        metadata = {"jobid": self.id, "arcpath": self._arcpath}
        if self.jobfile:
            metadata["jobfile"] = self.jobfile
        if self.path:
            metadata["orig_path"] = self.path
        if self.type:
            metadata["jobtype"] = self.type

        if hasattr(s3key, "put"):
            with Path(bundleFile).open("rb") as data:
                s3key.put(Body=data, Metadata={k: str(v) for k, v in metadata.items()})
        elif hasattr(s3key, "upload_file"):
            s3key.upload_file(bundleFile, ExtraArgs={"Metadata": {k: str(v) for k, v in metadata.items()}})

        self._key = s3key
        Path(bundleFile).unlink()

    def set_jobfile(self, jobfile_or_path: str = "./", jobfile: str | None = None) -> None:
        """Set the target file and path for the job.

        Args:
            jobfile_or_path (str, optional): The base directory or the file path. Defaults to "./".
            jobfile (str | None, optional): The specific file name within the path. Defaults to None.
        """
        if jobfile is None:
            p = Path(jobfile_or_path).resolve()
            if p.is_dir():
                self.jobfile = ""
                self.path = str(p)
            else:
                self.path = str(p.parent)
                self.jobfile = p.name
        else:
            self.path = jobfile_or_path
            self.jobfile = jobfile
        self.jobpath = self.path

    def mkTar(self) -> str:
        """Create a compressed tarball containing the job files.

        Returns:
            str: The local file path to the created tarball.
        """
        filename = Path.home() / ".remotebatch" / "outqueue" / f"{self.id}.tar.gz"
        filename.parent.mkdir(parents=True, exist_ok=True)

        with tarfile.open(filename, "w:gz") as tfile:
            if self.jobpath:
                tfile.add(self.jobpath, arcname=self._arcpath, recursive=True)
            if self.jobpath and self.jobfile:
                filepath = Path(self.jobpath) / self.jobfile
                if filepath.exists():
                    tfile.add(filepath, arcname=self.jobfile)
        return str(filename)


class QueuedJob(Job):
    """A standard Job stored in the processing queue."""
    pass


class BatchJob(Job):
    """A Job executed as part of a batch process."""
    pass


class ClientJob(Job):
    """A specialized job for use in an interactive, sometimes disconnected client.

    Handles actions that are pending execution when offline.
    """

    def __init__(self, jobfile_or_path: str = "./", jobfile: str | None = None, s3key: object | None = None) -> None:
        """Initialize a ClientJob.

        Args:
            jobfile_or_path (str, optional): The base path or file. Defaults to "./".
            jobfile (str | None, optional): The specific file name. Defaults to None.
            s3key (object | None, optional): The storage key. Defaults to None.
        """
        super().__init__(jobfile_or_path, jobfile, s3key)
        self.pending_actions: set[str] = set()

    def __getstate__(self) -> dict[str, object]:
        """Serialize state, excluding non-pickleable attributes like the storage key.

        Returns:
            dict[str, object]: The object state for serialization.
        """
        ret = dict(self.__dict__)
        if "_key" in ret:
            ret.pop("_key")
        return ret

    @property
    def storage(self) -> str:
        """Determine the current storage location status.

        Returns:
            str: The storage status ("cached", "local", or "remote").
        """
        if not hasattr(self, "_key") or self._key is None:
            return "cached"
        elif getattr(self._key, "bucket_name", None) == "local":
            return "local"
        else:
            return "remote"


class Results:
    """Represents the output and execution status of a completed Job."""

    def __init__(
        self,
        job_id: str | None = None,
        path: str | None = None,
        status: object | None = None,
        s3key: object | None = None,
    ) -> None:
        """Initialize the Results object.

        Args:
            job_id (str | None, optional): The ID of the original job. Defaults to None.
            path (str | None, optional): The local path containing the output files. Defaults to None.
            status (object | None, optional): The execution status or exit code. Defaults to None.
            s3key (object | None, optional): The storage key containing stored results. Defaults to None.
        """
        self.orig_path: str | None = None
        if s3key:
            metadata = getattr(s3key, "metadata", {})

            self.type = metadata.get("jobtype")
            self.id = metadata.get("jobid")
            self.path = None
            self.status = metadata.get("jobstatus")
            self._arcpath = metadata.get("arcpath", "output")
            self._key = s3key
        else:
            self.type = "results"
            self.id = job_id
            self.path = path
            self.status = status
            self._arcpath = "output"

    def mkTar(self) -> str:
        """Archive the output files into a tarball.

        Returns:
            str: The path to the created results tarball.
        """
        filename = Path.home() / ".remotebatch" / "outqueue" / f"{self.id}_{self.type}.tar.gz"
        filename.parent.mkdir(parents=True, exist_ok=True)

        with tarfile.open(filename, "w:gz") as tfile:
            if self.path:
                tfile.add(self.path, arcname=self._arcpath, recursive=True)
        return str(filename)

    def store_in_key(self, key: object) -> None:
        """Upload the results tarball and metadata to the queue storage.

        Args:
            key (object): The storage key to upload to.
        """
        print(f"Storing results for job {self.id} in {key}")
        bundleFile = self.mkTar()

        metadata = {"jobid": str(self.id), "jobstatus": str(self.status)}

        if hasattr(self, "orig_path") and self.orig_path:
            metadata["orig_path"] = self.orig_path
        if hasattr(self, "type") and self.type:
            metadata["jobtype"] = self.type
            metadata["arcpath"] = self._arcpath

        if hasattr(key, "put"):
            with Path(bundleFile).open("rb") as data:
                key.put(Body=data, Metadata={k: str(v) for k, v in metadata.items()})

        Path(bundleFile).unlink()


class BatchQueue:
    """Manages interactions with a remote processing queue (e.g., AWS S3)."""

    def __init__(self, bucket: str = REMOTE_BATCH_BUCKET, job_class: type[Job] = QueuedJob) -> None:
        """Initialize the BatchQueue.

        Args:
            bucket (str, optional): The name of the S3 bucket to use. Defaults to REMOTE_BATCH_BUCKET.
            job_class (type[Job], optional): The class to instantiate for retrieved jobs. Defaults to QueuedJob.
        """
        self.openJobs: dict[str, bool] = {}
        self.job_class = job_class
        self.bucket_name = bucket
        self.s3: object | None = None
        self.bucket: object | None = None
        if boto3:
            self.connect(bucket)

    def connect(self, bucket: str = REMOTE_BATCH_BUCKET) -> bool:
        """Connect to the remote S3 bucket.

        Args:
            bucket (str, optional): The S3 bucket name. Defaults to REMOTE_BATCH_BUCKET.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if not boto3:
            return False
        with contextlib.suppress(Exception):
            self.s3 = boto3.resource("s3")
            self.bucket = self.s3.Bucket(bucket)
        return True

    def queue_job(self, job: Job) -> None:
        """Upload and add a job to the remote queue.

        Args:
            job (Job): The job object to queue.
        """
        if self.bucket:
            key = self.bucket.Object(job.id)
            job.store_in_key(key)

    def jobs(self) -> Generator[Job, None, None]:
        """Yield unhandled jobs from the remote queue.

        Yields:
            Job: A job object instantiated from the remote storage.
        """
        if not self.bucket:
            return

        emptyBucket = False
        while not emptyBucket:
            emptyBucket = True
            for obj in self.bucket.objects.all():
                if obj.key not in self.openJobs:
                    full_obj = self.bucket.Object(obj.key)
                    try:
                        full_obj.load()
                    except Exception:
                        continue

                    job = self.job_class(s3key=full_obj)
                    self.openJobs[obj.key] = True
                    emptyBucket = False
                    yield job

    def allJobs(self) -> list[Job]:
        """Retrieve all jobs currently present in the queue.

        Returns:
            list[Job]: A list of all available jobs.
        """
        if not self.bucket:
            return []

        jobs = []
        for obj in self.bucket.objects.all():
            full_obj = self.bucket.Object(obj.key)
            try:
                full_obj.load()
            except Exception:
                continue
            jobs.append(self.job_class(s3key=full_obj))
        return jobs

    def delete(self, job: Job) -> None:
        """Remove a job from the queue.

        Args:
            job (Job): The job to remove.
        """
        job.delete()


class ClientQueue(BatchQueue):
    """A specialized queue for client-side applications.

    Handles offline caching and syncing of jobs when the network is unavailable.
    """

    def __init__(
        self,
        local_path: str,
        bucket: str = REMOTE_BATCH_BUCKET,
        job_class: type[Job] = ClientJob,
        check_network: object = lambda: True,
    ) -> None:
        """Initialize the ClientQueue.

        Args:
            local_path (str): The local directory path for caching jobs offline.
            bucket (str, optional): The S3 bucket name. Defaults to REMOTE_BATCH_BUCKET.
            job_class (type[Job], optional): The job class to instantiate. Defaults to ClientJob.
            check_network (object, optional): Verify network connectivity. Defaults to always returning True.
        """
        self.openJobs: dict[str, bool] = {}
        self.local_jobs: list[Job] = []
        self.cached_remote_jobs: list[Job] = []
        self.local_path = Path(local_path)
        self.job_class = job_class
        self.bucket: object | None = None
        self.bucket_name = bucket
        self.check_network = check_network
        self.s3 = None

    def connect(self, bucket: str = REMOTE_BATCH_BUCKET) -> bool:
        """Connect to the remote queue if the network is available.

        Args:
            bucket (str, optional): The S3 bucket name. Defaults to REMOTE_BATCH_BUCKET.

        Returns:
            bool: True if connected successfully, False otherwise.
        """
        if not callable(self.check_network) or not self.check_network():
            return False
        return super().connect(self.bucket_name)

    def disconnect(self) -> None:
        """Disconnect from the remote queue."""
        self.bucket = None

    @property
    def isConnected(self) -> bool:
        """Check if currently connected to the remote queue.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.bucket is not None

    @property
    def remote_jobs(self) -> list[Job]:
        """Fetch the jobs from the remote queue and cache them.

        Returns:
            list[Job]: A list of jobs retrieved from the remote queue.
        """
        if self.isConnected:
            self.cached_remote_jobs = super().allJobs()
        return self.cached_remote_jobs

    def queue_job(self, job: Job) -> None:
        """Add a job to the queue, caching it locally if offline.

        Args:
            job (Job): The job to queue.
        """
        if self.isConnected and self.bucket:
            key = self.bucket.Object(f"{job.id}_{job.type}")
            job.store_in_key(key)
        else:
            self.local_jobs.append(job)

    def allJobs(self) -> list[Job]:
        """Retrieve a combined list of local and remote jobs.

        Returns:
            list[Job]: A list of all known jobs.
        """
        if not self.isConnected:
            try:
                if self.connect():
                    print("running in connected mode.")
                else:
                    print("no connection")
            except Exception as e:
                print(f"{type(e)} {e} Failed to create/get s3 bucket, running local only.")
        return self.local_jobs + self.remote_jobs

    def save(self) -> None:
        """Save the local queue state to disk."""
        self.local_path.mkdir(parents=True, exist_ok=True)
        with (self.local_path / "index.pkl").open("wb") as f:
            pickle.dump({"remote_jobs": self.remote_jobs, "local_jobs": self.local_jobs}, f)

    def load(self) -> None:
        """Load the local queue state from disk."""
        try:
            with (self.local_path / "index.pkl").open("rb") as f:
                state = pickle.load(f)
        except (OSError, EOFError):
            pass
        else:
            self.local_jobs = state.get("local_jobs", [])
            self.cached_remote_jobs = state.get("remote_jobs", [])

    def delete(self, job: Job) -> None:
        """Delete a job, queuing deletion locally if offline.

        Args:
            job (Job): The job to delete.
        """
        if job in self.local_jobs:
            self.local_jobs.remove(job)
        else:
            if isinstance(job, ClientJob):
                job.pending_actions.add("delete")
            if self.isConnected:
                super().delete(job)


class LocalKey:
    """Mock S3 Object for LocalQueue.

    Simulates the behavior of a boto3 S3 object by reading and writing
    files directly to the local filesystem.
    """

    def __init__(self, root: str, key: str) -> None:
        """Initialize a LocalKey.

        Args:
            root (str): The root directory for the local queue.
            key (str): The object key (file name).
        """
        self.root = Path(root)
        self.key = key
        self.data_path = self.root / key
        self.meta_path = self.root / f"{key}.meta"
        self.metadata: dict[str, object] = {}
        self.bucket_name = "local"
        self.content_length = 0
        self.load()

    def exists(self) -> bool:
        """Check if the mocked object data exists on disk.

        Returns:
            bool: True if the data file exists.
        """
        return self.data_path.exists()

    def put(self, Body: object, Metadata: dict[str, object] | None = None) -> None:
        """Simulate uploading data to S3.

        Args:
            Body (object): The file content.
            Metadata (dict[str, object] | None, optional): The associated metadata. Defaults to None.
        """
        with self.data_path.open("wb") as f:
            if hasattr(Body, "read"):
                f.write(Body.read())
            else:
                f.write(Body)  # type: ignore
        if Metadata:
            with self.meta_path.open("wb") as f:
                pickle.dump(Metadata, f)
        self.load()

    def load(self) -> None:
        """Load metadata and calculate content length from disk."""
        if self.meta_path.exists():
            with self.meta_path.open("rb") as f:
                self.metadata = pickle.load(f)
        if self.data_path.exists():
            self.content_length = self.data_path.stat().st_size

    def delete(self) -> None:
        """Delete the mocked object data and metadata from disk."""
        if self.data_path.exists():
            self.data_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()

    def download_fileobj(self, fileobj: object) -> None:
        """Download the mocked object content to a file-like object.

        Args:
            fileobj (object): The file-like object to write to.
        """
        with self.data_path.open("rb") as f:
            fileobj.write(f.read())


class LocalQueue(BatchQueue):
    """A filesystem-based implementation of the Queue interface for testing.

    Mimics S3 bucket behavior using a local directory. Useful for local
    development and unit tests where AWS access is unavailable or undesired.
    """

    def __init__(self, root_path: str = "/tmp/localqueue", job_class: type[Job] = QueuedJob) -> None:
        """Initialize the LocalQueue.

        Args:
            root_path (str, optional): The directory path to use as the simulated queue. Defaults to "/tmp/localqueue".
            job_class (type[Job], optional): The job class to instantiate. Defaults to QueuedJob.
        """
        self.root_path = Path(root_path)
        self.job_class = job_class
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.openJobs: dict[str, bool] = {}
        self.bucket: object = "local"  # Mock bucket

    def connect(self, bucket: str = "") -> bool:
        """Simulate connecting to a bucket.

        Args:
            bucket (str, optional): Ignored parameter. Defaults to "".

        Returns:
            bool: Always True.
        """
        return True

    def queue_job(self, job: Job) -> None:
        """Store a job locally in the simulated queue directory.

        Args:
            job (Job): The job to store.
        """
        key = LocalKey(str(self.root_path), job.id)
        job.store_in_key(key)

    def jobs(self) -> Generator[Job, None, None]:
        """Yield unhandled jobs from the local queue directory.

        Yields:
            Job: A job retrieved from the local directory.
        """
        for item in self.root_path.iterdir():
            if item.suffix == ".meta":
                continue

            job_id = item.name
            key = LocalKey(str(self.root_path), job_id)
            if key.exists():
                yield self.job_class(s3key=key)

    def allJobs(self) -> list[Job]:
        """Retrieve all jobs in the local queue directory.

        Returns:
            list[Job]: A list of all available jobs.
        """
        return list(self.jobs())

    def delete(self, job: Job) -> None:
        """Delete a job from the local queue directory.

        Args:
            job (Job): The job to remove.
        """
        key = LocalKey(str(self.root_path), job.id)
        key.delete()
