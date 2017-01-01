import cPickle as pickle
import os.path
import tarfile
import tempfile
import uuid
from StringIO import StringIO

import boto
from boto.s3.key import Key
from secrets import REMOTE_BATCH_BUCKET


class Job(object):
    def __str__(self):
        ret = "id: %s" % self.id
        if getattr(self, "path", False):
            ret += "path:\n%s" % (self.path)
        if getattr(self, "jobfile", False):
            ret += "\n" + self.jobfile
        return ret

    def cleanup(self):
        if self.path:
            self.path = None

    def __init__(self, jobfile_or_path="./", jobfile=None, s3key=None):
        """

        """
        self.step = 0
        if s3key:
            s3key.open_read()
            self.jobfile = s3key.get_metadata("jobfile")
            self.id = s3key.get_metadata("jobid")
            if "_" in self.id:
                self.id, self.step = self.id.split("_")
                if self.step.isdigit():
                    self.step = int(self.step)
                else:
                    self.step = 0

            self.type = s3key.get_metadata("jobtype")
            self.next_job = s3key.get_metadata("next_job")
            self.size = int(s3key.size)
            self._arcpath = s3key.get_metadata("arcpath")
            if not self._arcpath:
                if self.type == "results":
                    self._arcpath = "output"
                else:
                    self._arcpath = "jobroot"
            self._key = s3key
            self.path = None
            self.jobroot = None
        else:
            self.id = str(uuid.uuid1())
            self.size = 0
            self.type = None
            self.set_jobfile(jobfile_or_path, jobfile)
            self._arcpath = "jobroot"
            self.next_job = None

    def getFiles(self, to=None):
        """Get the files from this job, returns the path the files were placed at. """
        if self.jobroot is not None:
            return self.jobroot
        tmpTar = StringIO()

        self._key.get_contents_to_file(tmpTar)
        tmpTar.seek(0)
        tar = tarfile.open(fileobj=tmpTar, mode="r:gz")
        self.path = to
        if not to:
            self.path = tempfile.mkdtemp()
            # print tar.getmembers()
        tar.extractall(self.path, [member for member in tar.getmembers() if member.name.startswith(self._arcpath)])
        if self.jobfile:
            tar.extract(self.jobfile, self.path)
        self.jobroot = os.path.join(self.path, self._arcpath)
        return self.jobroot

    def mark_complete(self, next_job=None):
        self.cleanup()
        # self.delete()
        if next_job:
            self._key.set_metadata("next_job", next_job.id)

    @property
    def isComplete(self):
        return self._key.bucket.get_key("%s_%d" % (self.id, self.step + 1)) is not None

    def delete(self):
        self._key.delete()

    def store_in_key(self, s3key):
        bundleFile = self.mkTar()
        if self.jobfile:
            s3key.set_metadata("jobfile", self.jobfile)
        s3key.set_metadata("jobid", self.id)
        s3key.set_metadata("orig_path", self.path)
        if self.type:
            s3key.set_metadata("jobtype", self.type)
        s3key.set_metadata("arcpath", self._arcpath)
        s3key.set_contents_from_filename(bundleFile)
        self._key = s3key
        os.unlink(bundleFile)

    def set_jobfile(self, jobfile_or_path="./", jobfile=None):
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

    def mkTar(self):
        filename = os.path.expanduser(os.path.join("~", ".remotebatch", "outqueue", self.id + ".tar.gz"))
        tfile = tarfile.open(filename, "w:gz")
        tfile.add(self.jobpath, arcname=self._arcpath, recursive=True)
        if self.jobfile:
            tfile.add(os.path.join(self.jobpath, self.jobfile), arcname=self.jobfile)
        tfile.close()
        return filename


class QueuedJob(Job):
    pass


class BatchJob(Job):
    pass


class ClientJob(Job):
    """A specialized job for use in an interactive, sometimes disconnected client."""

    def __init__(self, jobfile_or_path="./", jobfile=None, s3key=None):
        super(ClientJob, self).__init__(jobfile_or_path, jobfile, s3key)
        self.pending_actions = set()

    def __getstate__(self):
        """The State for a job does not include it's s3 key"""
        ret = dict(self.__dict__)
        if "_key" in ret:
            ret.pop("_key")
        return ret

    @property
    def storage(self):
        if not hasattr(self, "_key"):
            return "cached"
        elif self._key.bucket is None:
            return "local"
        else:
            return "remote"


class Results(object):
    def __init__(self, id=None, path=None, status=None, s3key=None):
        """

        """
        if s3key:
            s3key.open_read()
            self.type = s3key.get_metadata("jobtype")
            self.id = s3key.get_metadata("jobid")
            self.path = None
            self.status = s3key.get_metadata("jobstatus")
            self._arcpath = s3key.get_metadata("arcpath")
            if not self._arcpath:
                self._arcpath = "output"
            self._key = s3key
        else:
            self.type = "results"
            self.id = id
            self.path = path
            self.status = status
            self._arcpath = "output"

    def mkTar(self):
        """

        """
        filename = os.path.expanduser(
            os.path.join("~", ".remotebatch", "outqueue", "%s_%s.tar.gz" % (self.id, self.type)))
        tfile = tarfile.open(filename, "w:gz")
        tfile.add(self.path, arcname=self._arcpath, recursive=True)
        tfile.close()
        return filename

    def store_in_key(self, key):
        """

        """
        print "Storing results for job %s in %s" % (self.id, str(key))
        bundleFile = self.mkTar()
        key.set_metadata("jobid", self.id)
        key.set_metadata("jobstatus", str(self.status))
        if hasattr(self, "orig_path"):
            key.set_metadata("orig_path", self.orig_path)
        if hasattr(self, "type"):
            key.set_metadata("jobtype", self.type)
            key.set_metadata("arcpath", self._arcpath)
        key.set_contents_from_filename(bundleFile)
        os.unlink(bundleFile)


class BatchQueue(object):
    def __init__(self, bucket=REMOTE_BATCH_BUCKET, job_class=QueuedJob):
        self.openJobs = {}
        self.job_class = job_class
        self.connect(bucket)

    def connect(self, bucket=REMOTE_BATCH_BUCKET):
        connection = boto.connect_s3()
        self.bucket = connection.get_bucket(bucket)
        if not self.bucket:
            self.bucket = connection.create_bucket(bucket)
        return True

    def queue_job(self, job):
        """Add the given job to this queue"""
        job.store_in_key(Key(self.bucket, name=job.id))

    def jobs(self):
        """A generator that returns jobs

        the same job will not be returned twice by the
        same queue object
        """
        emptyBucket = False
        while not emptyBucket:
            emptyBucket = True
            for key in self.bucket.list():
                if key.key not in self.openJobs:
                    job = self.job_class(s3key=key)  # need to fully construct job here
                    self.openJobs[key.key] = True
                    emptyBucket = False
                    yield job

    def allJobs(self):
        return [self.job_class(s3key=key) for key in self.bucket.list()]

    def delete(self, job):
        job.delete()


class ClientQueue(BatchQueue):
    """A specialized queue for use on the client side"""

    def __init__(self, local_path, bucket=REMOTE_BATCH_BUCKET, job_class=ClientJob, check_network=lambda: True):
        """

        """
        self.openJobs = {}
        self.local_jobs = []
        self.cached_remote_jobs = []
        self.local_path = local_path
        self.job_class = job_class
        self.bucket = None
        self.bucket_name = bucket
        self.check_network = check_network

    def connect(self):
        if not self.check_network():
            return False
        return super(ClientQueue, self).connect(self.bucket_name)

    def disconnect(self):
        self.bucket = None

    @property
    def isConnected(self):
        return self.bucket is not None

    @property
    def remote_jobs(self):
        if self.isConnected:
            self.cached_remote_jobs = super(ClientQueue, self).allJobs()
        return self.cached_remote_jobs

    def queue_job(self, job):
        """Add the given job to this queue"""
        key = Key(self.bucket, name="%s_%s" % (job.id, job.type))
        job.store_in_key(key)
        if not self.isConnected:
            self.local_jobs.append(job)

    def allJobs(self):
        if not self.isConnected:
            try:
                if self.connect():
                    print "running in connected mode."
                else:
                    print "no connection"
            except AttributeError:
                print "No s3 connection configured, running local only."
            except IOError:
                print "Failed to connect to s3, running local only."
            except Exception, e:
                print type(e), e, "Failed to create/get s3 bucket, running local only."
        return self.local_jobs + self.remote_jobs

    def save(self):
        """

        """
        pickle.dump({"remote_jobs": self.remote_jobs, "local_jobs": self.local_jobs},
                    open(os.path.join(self.local_path,
                                      "index.pkl"),
                         "wb"))

    def load(self):
        """
            if self.resultsAct.isChecked() and job.type != "results":
                continue

        """
        try:
            state = pickle.load(open(os.path.join(self.local_path, "index.pkl"), "rb"))
        except (IOError, EOFError):
            pass
        else:
            self.local_jobs = state.get("local_jobs", [])
            self.cached_remote_jobs = state.get("remote_jobs", [])

    def delete(self, job):
        """
        
        """
        if job in self.local_jobs:
            self.local_jobs.remove(job)
        else:
            job.pending_actions.add("delete")
            if self.isConnected:
                super(ClientQueue, self).delete(job)
