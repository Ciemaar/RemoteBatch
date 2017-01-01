import os

import sip

sip.setapi('QVariant', 2)

from PyQt4 import QtGui
from PyQt4.QtNetwork import QNetworkConfigurationManager
from controller import mgr_main
from model import ClientQueue


class RemoteMgrApp(QtGui.QApplication, object):
    def __init__(self, argv, *args, **xargs):
        super(RemoteMgrApp, self).__init__(argv, *args, **xargs)
        self.local_path = os.path.expanduser("~/.remotebatch/outqueue")
        try:
            os.makedirs(self.local_path)
        except OSError:
            pass

    def start(self):
        """
        Start app including queue initialization.
        """
        print 'Connecting and loading queued jobs'
        self.queue = ClientQueue(self.local_path, check_network=lambda: QNetworkConfigurationManager().isOnline())
        self.queue.load()
        self.main = mgr_main(self.queue)
        self.setActiveWindow(self.main)
        self.aboutToQuit.connect(self.saveQueue)
        print "done starting"

    def saveQueue(self, *args, **kwargs):
        print "Saving queue for next time"
        self.queue.save()


if __name__ == '__main__':
    #
    import sys

    print "in main"
    app = RemoteMgrApp(sys.argv)
    print "created remote batch app"
    app.start()
    sys.exit(app.exec_())
