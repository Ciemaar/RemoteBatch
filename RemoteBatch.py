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

import contextlib
import os
import os.path
import sys

from PyQt6 import QtWidgets

from controller import job_dialog
from model import BatchQueue, Results

ARGS_MIN_LENGTH = 2


class RemoteBatchApp(QtWidgets.QApplication):
    """The main client application for submitting jobs to RemoteBatch."""

    def __init__(self, argv, *args, **xargs):
        """Initialize the RemoteBatchApp.

        Args:
            argv (list): Command-line arguments.
            *args: Variable length argument list.
            **xargs: Arbitrary keyword arguments.
        """
        super().__init__(argv, *args, **xargs)
        self.path = argv[1] if len(argv) >= ARGS_MIN_LENGTH else "./"
        with contextlib.suppress(OSError):
            os.makedirs(os.path.expanduser("~/.remotebatch/outqueue"))

    def start(self):
        """Start the client application and open the job submission dialog."""
        print("started")
        job_dialog(self.path, BatchQueue())


if __name__ == "__main__":
    print("in main")
    app = RemoteBatchApp(sys.argv)
    print("created remote batch app")
    app.start()
    try:
        resultQueue = BatchQueue(job_class=Results)
        for result in resultQueue.jobs():
            if result.type != "results":
                continue
    except AttributeError:
        resultQueue = None
