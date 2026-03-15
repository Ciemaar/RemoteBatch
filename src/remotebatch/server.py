#!/usr/bin/python

"""Server daemon for processing jobs from the queue."""

import logging
import subprocess
from pathlib import Path
from time import sleep

import click
from tenacity import retry, retry_if_exception_type, wait_fixed

from remotebatch.model import BatchQueue, Results

log = logging.getLogger(name=__name__)

outqueue_path = Path.home() / ".remotebatch" / "outqueue"
outqueue_path.mkdir(parents=True, exist_ok=True)


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

        output_dir = Path(job.path) / "output"
        output_dir.mkdir(exist_ok=True)

        status = subprocess.call(("/usr/bin/povray", job.jobfile), cwd=job.path)

        result = Results(f"{job.id}_{job.step + 1}", str(output_dir), status)
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
        if not job.type:
            job.mark_complete()
        return None


@retry(wait=wait_fixed(180), retry=retry_if_exception_type(Exception))
def poll_and_process(batch_queue, result_queue):
    """Poll the queue and process jobs, retrying on generic exceptions like network failure.

    Args:
        batch_queue (BatchQueue): The queue to poll for jobs.
        result_queue (BatchQueue): The queue to place results.
    """
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

    # We yield control and loop inside the main daemon.
    # Tenacity handles retries if the generator or connection throws an exception (e.g. S3 error).


@click.command()
def main():
    """Run the batch processing server."""
    batch_queue = BatchQueue()
    result_queue = BatchQueue()

    print("Starting server polling...")
    while True:
        try:
            poll_and_process(batch_queue, result_queue)
        except Exception as e:
            # Should be caught by tenacity, but catch-all for severe failures
            log.error(f"Critical failure in polling loop: {e}")

        print("Checking jobs complete, waiting for next cycle...")
        sleep(120)

if __name__ == "__main__":
    main()
