#!/usr/bin/env python

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

import sip

sip.setapi('QVariant', 2)

from PyQt4 import QtGui

import os
import os.path

from controller import job_dialog
from model import BatchQueue, Results


class RemoteBatchApp(QtGui.QApplication):
    def __init__(self, argv, *args, **xargs):
        super(RemoteBatchApp, self).__init__(argv, *args, **xargs)
        if len(argv) >= 2:
            self.path = argv[1]
        else:
            self.path = "./"
        try:
            os.makedirs(os.path.expanduser("~/.remotebatch/outqueue"))
        except OSError:
            pass

    def start(self):
        print "started"
        job_dialog(self.path, BatchQueue())


if __name__ == '__main__':
    #
    import sys

    print "in main"
    app = RemoteBatchApp(sys.argv)
    print "created remote batch app"
    app.start()
    try:
        resultQueue = BatchQueue(job_class=Results)
        for result in resultQueue.jobs():
            if result.type != "results":
                continue
    except AttributeError:
        resultQueue = None
