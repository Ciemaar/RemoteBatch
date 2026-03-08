#!/usr/bin/python

"""Server daemon for processing jobs from the queue."""

# from gevent import monkey
# monkey.patch_all()

import contextlib
import logging
import os
import subprocess
from time import sleep

# from boto.exception import S3ResponseError # boto3 doesn't use this
from model import BatchQueue, Results

log = logging.getLogger(name=__name__)

with contextlib.suppress(OSError):
    os.makedirs(os.path.expanduser("~/.remotebatch/outqueue"))


def processJob(job):
    """Process a single job based on its type.

    Args:
        job (Job): The job object to process.

    Returns:
        Results | None: The result object if processed, or None if the job requires no further action.
    """
    if job.type and job.type.lower() == "povray":
        print(f"povjob {job.jobfile}")
        job.getFiles()
        print(f"calling povray on {job.path}/{job.jobfile}")
        os.mkdir(os.path.join(job.path, "output"))
        status = subprocess.call(("/usr/bin/povray",
                                  job.jobfile), cwd=job.path)
        print(f"root files {os.listdir(job.path)}")
        files = os.listdir(os.path.join(job.path, "output"))
        print(f"output files {files}")
        result = Results(f"{job.id}_{job.step + 1}", os.path.join(job.path, "output"), status)
        print(f"result: {result.path}")
        result.mkTar()
        return result
    elif job.type and job.type == "results":
        print(f"results job {job.id}")
        return None
    else:
        log.error("Unknown job type %s", job.type)

        tempdir = job.getFiles()
        print(f"unzipped to {tempdir}")
        files = os.listdir(tempdir)
        print(f"path {tempdir} files {files}")
        if not job.type:
            job.mark_complete()
        return None


if __name__ == "__main__":
    batch_queue = BatchQueue()
    result_queue = BatchQueue()
    while True:
        try:
            for job in batch_queue.jobs():
                print(f"Found Job:  {job} type: {job.type}")
                if job.isComplete:
                    print("Already Complete")
                    continue
                try:
                    result = processJob(job)
                    if result:
                        result_queue.queue_job(result)
                except Exception:
                    import traceback

                    traceback.print_exc()
                    print(f"System error on job {job}")
                else:
                    job.mark_complete(result)
                finally:
                    job.cleanup()
        except Exception:
            print("Error from S3, will retry in 5 mins")
            sleep(180)
        sleep(120)
        print("Checking jobs")
