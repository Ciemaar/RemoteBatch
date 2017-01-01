#!/usr/bin/python

# from gevent import monkey
# monkey.patch_all()

import logging
import os
import subprocess
from time import sleep

from boto.exception import S3ResponseError
from  model import BatchQueue, Results

log = logging.getLogger(name=__name__)

try:
    os.makedirs(os.path.expanduser("~/.remotebatch/outqueue"))
except OSError:
    pass


def processJob(job):
    if job.type and job.type.lower() == "povray":
        print "povjob %s" % job.jobfile
        job.getFiles()
        print "calling povray on %s/%s" % (job.path, job.jobfile)
        os.mkdir(os.path.join(job.path, "output"))
        status = subprocess.call(("/usr/bin/povray",
                                  job.jobfile), cwd=job.path)
        print "root files %s" % os.listdir(job.path)
        files = os.listdir(os.path.join(job.path, "output"))
        print "output files %s" % (files)
        result = Results("%s_%d" % (job.id, job.step + 1), os.path.join(job.path, "output"), status)
        print "result: " + result.path
        result.mkTar()
        return result
    elif job.type and job.type == "results":
        print "results job %s" % job.id
        return None
    else:
        log.error("Unknown job type %s", job.type)

        tempdir = job.getFiles()
        print "unzipped to %s" % tempdir
        files = os.listdir(tempdir)
        print "path %s files %s" % (tempdir, files)
        if not job.type:
            job.mark_complete()
        return None


batch_queue = BatchQueue()
result_queue = BatchQueue()
while True:
    try:
        for job in batch_queue.jobs():
            print "Found Job:  {job} type: {type}".format(job=job, type=job.type)
            if job.isComplete:
                print "Already Complete"
                continue
            try:
                result = processJob(job)
                if result:
                    result_queue.queue_job(result)
            except:
                import traceback

                traceback.print_exc()
                print "System error on job {job}".format(job=job)
            else:
                job.mark_complete(result)
            finally:
                job.cleanup()
    except  S3ResponseError:
        print "Error from S3, will retry in 5 mins"
        sleep(180)
    sleep(120)
    print "Checking jobs"
