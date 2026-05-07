#!/usr/bin/env python

"""Main entry point for the Remote Batch client application."""

#############################################################################
##
## Copyright (C) 2004-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################
import argparse
import logging
import sys
from pathlib import Path

from PyQt6 import QtWidgets
from remotebatch.controller import job_dialog
from remotebatch.model import BatchQueue

log = logging.getLogger(__name__)


class RemoteBatchApp(QtWidgets.QApplication):
    """The main client application for submitting jobs to RemoteBatch."""

    def __init__(self, path: str, argv: list[str]):
        """Initialize the RemoteBatchApp.

        Args:
            path (str): The initial path to open for jobs.
            argv (list[str]): Command-line arguments.
        """
        super().__init__(argv)
        self.path = path

        # Pathlib equivalent of os.makedirs
        outqueue_path = Path.home() / ".remotebatch" / "outqueue"
        outqueue_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the client application and open the job submission dialog."""
        log.debug("started")
        job_dialog(self.path, BatchQueue())


def main():
    """Start the Remote Batch GUI application to submit jobs."""
    parser = argparse.ArgumentParser(description="Start the Remote Batch GUI application to submit jobs.")
    parser.add_argument(
        "path", nargs="?", default="./", help="The initial directory or file to load. Defaults to current directory."
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args, unknown = parser.parse_known_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.debug("in main")
    # Pass sys.argv back so Qt can parse the flags it cares about
    app = RemoteBatchApp(args.path, sys.argv)
    log.debug("created remote batch app")
    app.start()

    # Run the Qt application loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
