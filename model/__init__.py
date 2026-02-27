import io
import logging
import os
import pickle
import tarfile
import tempfile
import uuid
from collections.abc import Generator
from typing import Any, Dict, Optional, Union

# Try to import boto3, but allow it to fail if we are just testing local queue
try:
    import boto3
except ImportError:
    boto3 = None

from secrets import REMOTE_BATCH_BUCKET

log = logging.getLogger(__name__)


class Job:
    def __init__(self, jobfile_or_path: str = "./", jobfile: str | None = None, s3key: Any | None = None) -> None:
        """
        Initialize a Job.
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
        self._key: Any | None = s3key
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

            # Content length logic depends on whether s3key is Boto3 object or LocalKey
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

    def _get_metadata(self, key: Any) -> dict[str, Any]:
        if hasattr(key, "metadata"):
            return key.metadata
        # If it's a boto3 Object, we might need to reload it to get metadata if not present
        if hasattr(key, "load"):
            try:
                key.load()
                return key.metadata
            except Exception:
                pass
        return {}

    def __str__(self) -> str:
        ret = f"id: {self.id}"
        if self.path:
            ret += f"path:\n{self.path}"
        if self.jobfile:
            ret += f"\n{self.jobfile}"
        return ret

    def cleanup(self) -> None:
        if self.path:
            self.path = None

    def getFiles(self, to: str | None = None) -> str:
        """Get the files from this job, returns the path the files were placed at."""
        if self.jobroot is not None:
            return self.jobroot

        tmpTar = io.BytesIO()

        if self._key:
            if hasattr(self._key, "download_fileobj"):
                self._key.download_fileobj(tmpTar)
            else:
                pass

        tmpTar.seek(0)

        try:
            tar = tarfile.open(fileobj=tmpTar, mode="r:gz")
        except tarfile.ReadError:
            if not to:
                self.path = tempfile.mkdtemp()
            else:
                self.path = to
            self.jobroot = os.path.join(self.path, self._arcpath)
            return self.jobroot

        self.path = to
        if not to:
            self.path = tempfile.mkdtemp()

        tar.extractall(
            self.path,
            members=[member for member in tar.getmembers() if member.name.startswith(self._arcpath)],
            filter="data",
        )

        if self.jobfile:
            try:
                tar.extract(self.jobfile, self.path, filter="data")
            except KeyError:
                pass

        self.jobroot = os.path.join(self.path, self._arcpath)
        return self.jobroot

    def mark_complete(self, next_job: Optional["Job"] = None) -> None:
        self.cleanup()
        if next_job and self._key:
            # Stub for marking complete in S3
            pass

    @property
    def isComplete(self) -> bool:
        return False

    def delete(self) -> None:
        if self._key and hasattr(self._key, "delete"):
            self._key.delete()

    def store_in_key(self, s3key: Any) -> None:
        bundleFile = self.mkTar()
        metadata = {"jobid": self.id, "arcpath": self._arcpath}
        if self.jobfile:
            metadata["jobfile"] = self.jobfile
        if self.path:
            metadata["orig_path"] = self.path
        if self.type:
            metadata["jobtype"] = self.type

        if hasattr(s3key, "put"):
            with open(bundleFile, "rb") as data:
                # Boto3 expects Metadata as a dict of strings
                s3key.put(Body=data, Metadata={k: str(v) for k, v in metadata.items()})
        elif hasattr(s3key, "upload_file"):
            s3key.upload_file(bundleFile, ExtraArgs={"Metadata": {k: str(v) for k, v in metadata.items()}})

        self._key = s3key
        os.unlink(bundleFile)

    def set_jobfile(self, jobfile_or_path: str = "./", jobfile: str | None = None) -> None:
        if jobfile is None:
            if os.path.isdir(jobfile_or_path):
                self.jobfile = ""
                self.path = os.path.abspath(jobfile_or_path)
            else:
                self.path, self.jobfile = os.path.split(os.path.abspath(jobfile_or_path))
        else:
            self.path = jobfile_or_path
            self.jobfile = jobfile
        self.jobpath = self.path

    def mkTar(self) -> str:
        filename = os.path.expanduser(os.path.join("~", ".remotebatch", "outqueue", self.id + ".tar.gz"))
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with tarfile.open(filename, "w:gz") as tfile:
            if self.jobpath:
                tfile.add(self.jobpath, arcname=self._arcpath, recursive=True)
            if self.jobpath and self.jobfile:
                filepath = os.path.join(self.jobpath, self.jobfile)
                if os.path.exists(filepath):
                    tfile.add(filepath, arcname=self.jobfile)
        return filename


class QueuedJob(Job):
    pass


class BatchJob(Job):
    pass


class ClientJob(Job):
    """A specialized job for use in an interactive, sometimes disconnected client."""

    def __init__(self, jobfile_or_path: str = "./", jobfile: str | None = None, s3key: Any | None = None) -> None:
        super().__init__(jobfile_or_path, jobfile, s3key)
        self.pending_actions: set[str] = set()

    def __getstate__(self) -> dict[str, Any]:
        """The State for a job does not include it's s3 key"""
        ret = dict(self.__dict__)
        if "_key" in ret:
            ret.pop("_key")
        return ret

    @property
    def storage(self) -> str:
        if not hasattr(self, "_key") or self._key is None:
            return "cached"
        elif getattr(self._key, "bucket_name", None) == "local":
            return "local"
        else:
            return "remote"


class Results:
    def __init__(
        self, id: str | None = None, path: str | None = None, status: Any | None = None, s3key: Any | None = None
    ) -> None:
        """ """
        self.orig_path: str | None = None
        if s3key:
            metadata = s3key.metadata if hasattr(s3key, "metadata") else {}

            self.type = metadata.get("jobtype")
            self.id = metadata.get("jobid")
            self.path = None
            self.status = metadata.get("jobstatus")
            self._arcpath = metadata.get("arcpath")
            if not self._arcpath:
                self._arcpath = "output"
            self._key = s3key
        else:
            self.type = "results"
            self.id = id
            self.path = path
            self.status = status
            self._arcpath = "output"

    def mkTar(self) -> str:
        """ """
        filename = os.path.expanduser(
            os.path.join("~", ".remotebatch", "outqueue", "%s_%s.tar.gz" % (self.id, self.type))
        )
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with tarfile.open(filename, "w:gz") as tfile:
            if self.path:
                tfile.add(self.path, arcname=self._arcpath, recursive=True)
        return filename

    def store_in_key(self, key: Any) -> None:
        """ """
        print(f"Storing results for job {self.id} in {key}")
        bundleFile = self.mkTar()

        metadata = {"jobid": str(self.id), "jobstatus": str(self.status)}

        if hasattr(self, "orig_path") and self.orig_path:
            metadata["orig_path"] = self.orig_path
        if hasattr(self, "type") and self.type:
            metadata["jobtype"] = self.type
            metadata["arcpath"] = self._arcpath

        if hasattr(key, "put"):
            with open(bundleFile, "rb") as data:
                key.put(Body=data, Metadata={k: str(v) for k, v in metadata.items()})

        os.unlink(bundleFile)


class BatchQueue:
    def __init__(self, bucket: str = REMOTE_BATCH_BUCKET, job_class: type[Job] = QueuedJob) -> None:
        self.openJobs: dict[str, bool] = {}
        self.job_class = job_class
        self.bucket_name = bucket
        self.s3: Any = None
        self.bucket: Any = None
        if boto3:
            self.connect(bucket)

    def connect(self, bucket: str = REMOTE_BATCH_BUCKET) -> bool:
        if not boto3:
            return False
        try:
            self.s3 = boto3.resource("s3")
            self.bucket = self.s3.Bucket(bucket)
            # Verify bucket exists
            # self.bucket.create() # Avoid creating buckets in constructor for now
        except Exception:
            pass
        return True

    def queue_job(self, job: Job) -> None:
        """Add the given job to this queue"""
        if self.bucket:
            key = self.bucket.Object(job.id)
            job.store_in_key(key)

    def jobs(self) -> Generator[Job, None, None]:
        """A generator that returns jobs"""
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
                    except:
                        continue

                    job = self.job_class(s3key=full_obj)
                    self.openJobs[obj.key] = True
                    emptyBucket = False
                    yield job

    def allJobs(self) -> list[Job]:
        if not self.bucket:
            return []

        jobs = []
        for obj in self.bucket.objects.all():
            full_obj = self.bucket.Object(obj.key)
            try:
                full_obj.load()
            except:
                continue
            jobs.append(self.job_class(s3key=full_obj))
        return jobs

    def delete(self, job: Job) -> None:
        job.delete()


class ClientQueue(BatchQueue):
    """A specialized queue for use on the client side"""

    def __init__(
        self,
        local_path: str,
        bucket: str = REMOTE_BATCH_BUCKET,
        job_class: type[Job] = ClientJob,
        check_network: Any = lambda: True,
    ) -> None:
        """ """
        self.openJobs: dict[str, bool] = {}
        self.local_jobs: list[Job] = []
        self.cached_remote_jobs: list[Job] = []
        self.local_path = local_path
        self.job_class = job_class
        self.bucket: Any | None = None
        self.bucket_name = bucket
        self.check_network = check_network
        self.s3 = None

    def connect(self, bucket: str = REMOTE_BATCH_BUCKET) -> bool:
        if not self.check_network():
            return False
        return super().connect(self.bucket_name)

    def disconnect(self) -> None:
        self.bucket = None

    @property
    def isConnected(self) -> bool:
        return self.bucket is not None

    @property
    def remote_jobs(self) -> list[Job]:
        if self.isConnected:
            self.cached_remote_jobs = super().allJobs()
        return self.cached_remote_jobs

    def queue_job(self, job: Job) -> None:
        """Add the given job to this queue"""
        if self.isConnected and self.bucket:
            key = self.bucket.Object("%s_%s" % (job.id, job.type))
            job.store_in_key(key)
        else:
            self.local_jobs.append(job)

    def allJobs(self) -> list[Job]:
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
        """ """
        os.makedirs(self.local_path, exist_ok=True)
        with open(os.path.join(self.local_path, "index.pkl"), "wb") as f:
            pickle.dump({"remote_jobs": self.remote_jobs, "local_jobs": self.local_jobs}, f)

    def load(self) -> None:
        """ """
        try:
            with open(os.path.join(self.local_path, "index.pkl"), "rb") as f:
                state = pickle.load(f)
        except (OSError, EOFError, FileNotFoundError):
            pass
        else:
            self.local_jobs = state.get("local_jobs", [])
            self.cached_remote_jobs = state.get("remote_jobs", [])

    def delete(self, job: Job) -> None:
        """ """
        if job in self.local_jobs:
            self.local_jobs.remove(job)
        else:
            if isinstance(job, ClientJob):
                job.pending_actions.add("delete")
            if self.isConnected:
                super().delete(job)


class LocalKey:
    """Mock S3 Object for LocalQueue"""

    def __init__(self, root: str, key: str) -> None:
        self.root = root
        self.key = key
        self.data_path = os.path.join(root, key)
        self.meta_path = os.path.join(root, key + ".meta")
        self.metadata: dict[str, Any] = {}
        self.bucket_name = "local"
        self.content_length = 0
        self.load()

    def exists(self) -> bool:
        return os.path.exists(self.data_path)

    def put(self, Body: Any, Metadata: dict[str, Any] | None = None) -> None:
        with open(self.data_path, "wb") as f:
            if hasattr(Body, "read"):
                f.write(Body.read())
            else:
                f.write(Body)
        if Metadata:
            with open(self.meta_path, "wb") as f:
                pickle.dump(Metadata, f)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        if os.path.exists(self.data_path):
            self.content_length = os.path.getsize(self.data_path)

    def delete(self) -> None:
        if os.path.exists(self.data_path):
            os.unlink(self.data_path)
        if os.path.exists(self.meta_path):
            os.unlink(self.meta_path)

    def download_fileobj(self, fileobj: Any) -> None:
        with open(self.data_path, "rb") as f:
            fileobj.write(f.read())


class LocalQueue(BatchQueue):
    """
    A filesystem-based implementation of the Queue interface for testing/local use.
    It mimics S3 bucket behavior using a directory.
    """

    def __init__(self, root_path: str = "/tmp/localqueue", job_class: type[Job] = QueuedJob) -> None:
        self.root_path = root_path
        self.job_class = job_class
        os.makedirs(self.root_path, exist_ok=True)
        self.openJobs: dict[str, bool] = {}
        self.bucket: Any = "local"  # Mock bucket

    def connect(self, bucket: str = "") -> bool:
        return True

    def queue_job(self, job: Job) -> None:
        key = LocalKey(self.root_path, job.id)
        job.store_in_key(key)

    def jobs(self) -> Generator[Job, None, None]:
        for filename in os.listdir(self.root_path):
            if filename.endswith(".meta"):
                continue

            job_id = filename
            key = LocalKey(self.root_path, job_id)
            if key.exists():
                yield self.job_class(s3key=key)

    def allJobs(self) -> list[Job]:
        return list(self.jobs())

    def delete(self, job: Job) -> None:
        key = LocalKey(self.root_path, job.id)
        key.delete()
