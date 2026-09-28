#!/usr/bin/python

"""Server daemon for processing jobs from the queue."""

import logging
import subprocess
import traceback
from pathlib import Path
from time import sleep

import click
from remotebatch.model import BatchQueue, Job, Results
from tenacity import retry, retry_if_exception_type, wait_fixed

log = logging.getLogger(name=__name__)

outqueue_path = Path.home() / ".remotebatch" / "outqueue"
outqueue_path.mkdir(parents=True, exist_ok=True)


def processJob(job: Job) -> Results | None:
    """Process a single job based on its type.

    Args:
        job (Job): The job object to process.

    Returns:
        Results | None: The result object if processed, or None if the job requires no further action.
    """
    if job.type and job.type.lower() == "povray":
        log.debug(f"povjob {job.jobfile}")
        job.getFiles()
        log.debug(f"calling povray on {job.path}/{job.jobfile}")

        output_dir = Path(str(job.path)) / "output"
        output_dir.mkdir(exist_ok=True)

        status = subprocess.call(("/usr/bin/povray", str(job.jobfile)), cwd=str(job.path))

        result = Results(f"{job.id}_{job.step + 1}", str(output_dir), status)
        log.debug(f"result: {result.path}")
        result.mkTar()
        return result
    elif job.type and job.type == "results":
        log.debug(f"results job {job.id}")
        return None
    else:
        log.error("Unknown job type %s", job.type)

        tempdir = job.getFiles()
        log.debug(f"unzipped to {tempdir}")
        if not job.type:
            job.mark_complete()
        return None


@retry(wait=wait_fixed(180), retry=retry_if_exception_type(Exception))
def poll_and_process(batch_queue: BatchQueue, result_queue: BatchQueue) -> None:
    """Poll the queue and process jobs, retrying on generic exceptions like network failure.

    Args:
        batch_queue (BatchQueue): The queue to poll for jobs.
        result_queue (BatchQueue): The queue to place results.
    """
    for job in batch_queue.jobs():
        log.debug(f"Found Job:  {job} type: {job.type}")
        if job.isComplete:
            log.debug("Already Complete")
            continue
        try:
            result = processJob(job)
            if result:
                result_queue.queue_job(result)
        except Exception:
            traceback.print_exc()
            log.debug(f"System error on job {job}")
        else:
            job.mark_complete(result)
        finally:
            job.cleanup()

    # We yield control and loop inside the main daemon.
    # Tenacity handles retries if the generator or connection throws an exception (e.g. S3 error).


@click.command()
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(verbose: bool):
    """Run the batch processing server."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    batch_queue = BatchQueue()
    result_queue = BatchQueue()

    log.debug("Starting server polling...")
    while True:
        try:
            poll_and_process(batch_queue, result_queue)
        except Exception as e:
            # Should be caught by tenacity, but catch-all for severe failures
            log.error(f"Critical failure in polling loop: {e}")

        log.debug("Checking jobs complete, waiting for next cycle...")
        sleep(120)


if __name__ == "__main__":
    main()
