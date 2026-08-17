#!/usr/bin/env python

"""Main entry point for the Remote Batch client application."""

import sys
from pathlib import Path

import click
from PyQt6 import QtWidgets
from remotebatch.controller import job_dialog
from remotebatch.model import BatchQueue, Results


class RemoteBatchApp(QtWidgets.QApplication):
    """The main client application for submitting jobs to RemoteBatch."""

    def __init__(self, path: str, argv: list[str], *args, **xargs):
        """Initialize the RemoteBatchApp.

        Args:
            path (str): The initial path to open for jobs.
            argv (list[str]): Command-line arguments.
            *args: Variable length argument list.
            **xargs: Arbitrary keyword arguments.
        """
        super().__init__(argv, *args, **xargs)
        self.path = path

        # Pathlib equivalent of os.makedirs
        outqueue_path = Path.home() / ".remotebatch" / "outqueue"
        outqueue_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the client application and open the job submission dialog."""
        print("started")
        job_dialog(self.path, BatchQueue())


@click.command()
@click.argument("path", default="./", type=click.Path(exists=True))
def main(path: str):
    """Start the Remote Batch GUI application to submit jobs.

    PATH is the initial directory or file to load. Defaults to current directory.
    """
    print("in main")
    app = RemoteBatchApp(path, sys.argv)
    print("created remote batch app")
    app.start()
    try:
        resultQueue = BatchQueue(job_class=Results)
        for result in resultQueue.jobs():
            if result.type != "results":
                continue
    except AttributeError:
        resultQueue = None


if __name__ == "__main__":
    main()
