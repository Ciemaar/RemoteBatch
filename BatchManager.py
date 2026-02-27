import contextlib
import os
import sys

from PyQt6 import QtWidgets

from controller import mgr_main
from model import ClientQueue


class RemoteMgrApp(QtWidgets.QApplication):
    def __init__(self, argv, *args, **xargs):
        super().__init__(argv, *args, **xargs)
        self.local_path = os.path.expanduser("~/.remotebatch/outqueue")
        with contextlib.suppress(OSError):
            os.makedirs(self.local_path)

    def start(self):
        """
        Start app including queue initialization.
        """
        print('Connecting and loading queued jobs')
        # QNetworkConfigurationManager is deprecated/removed in Qt6.
        # Using a simpler check or skipping for now.
        # Assuming true for now as replacement logic is complex without specific requirements.
        self.queue = ClientQueue(self.local_path, check_network=lambda: True)
        self.queue.load()
        self.main = mgr_main(self.queue)
        # setActiveWindow is not needed usually if we show the main window
        self.main.show()
        self.aboutToQuit.connect(self.saveQueue)
        print("done starting")

    def saveQueue(self, *args, **kwargs):
        print("Saving queue for next time")
        self.queue.save()


if __name__ == '__main__':
    print("in main")
    app = RemoteMgrApp(sys.argv)
    print("created remote batch app")
    app.start()
    sys.exit(app.exec())
