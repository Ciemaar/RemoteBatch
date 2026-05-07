"""Entry point for the Batch Manager GUI application."""

import argparse
import logging
import sys
from pathlib import Path

from PyQt6 import QtWidgets
from remotebatch.controller import mgr_main
from remotebatch.model import ClientQueue

log = logging.getLogger(__name__)


class RemoteMgrApp(QtWidgets.QApplication):
    """Main application class for the Remote Batch Manager."""

    def __init__(self, argv: list[str]):
        """Initialize the RemoteMgrApp.

        Args:
            argv (list[str]): Command-line arguments.
        """
        super().__init__(argv)
        self.local_path = Path.home() / ".remotebatch" / "outqueue"
        self.local_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the app including queue initialization."""
        log.debug("Connecting and loading queued jobs")
        self.queue = ClientQueue(str(self.local_path), check_network=lambda: True)
        self.queue.load()
        self.main = mgr_main(self.queue)
        self.main.show()
        self.aboutToQuit.connect(self.saveQueue)
        log.debug("done starting")

    def saveQueue(self, *args: object, **kwargs: object):
        """Save the current state of the queue to disk."""
        log.debug("Saving queue for next time")
        self.queue.save()


def main():
    """Start the Remote Batch Manager application."""
    parser = argparse.ArgumentParser(description="Start the Remote Batch Manager application.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args, unknown = parser.parse_known_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    log.debug("in main")
    app = RemoteMgrApp(sys.argv)
    log.debug("created remote batch app")
    app.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
