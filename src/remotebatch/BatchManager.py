"""Entry point for the Batch Manager GUI application."""

import sys
from pathlib import Path

import click
from PyQt6 import QtWidgets
from remotebatch.controller import mgr_main
from remotebatch.model import ClientQueue


class RemoteMgrApp(QtWidgets.QApplication):
    """Main application class for the Remote Batch Manager."""

    def __init__(self, argv: list[str], *args, **xargs):
        """Initialize the RemoteMgrApp.

        Args:
            argv (list[str]): Command-line arguments.
            *args: Variable length argument list.
            **xargs: Arbitrary keyword arguments.
        """
        super().__init__(argv, *args, **xargs)
        self.local_path = Path.home() / ".remotebatch" / "outqueue"
        self.local_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the app including queue initialization."""
        print("Connecting and loading queued jobs")
        self.queue = ClientQueue(str(self.local_path), check_network=lambda: True)
        self.queue.load()
        self.main = mgr_main(self.queue)
        self.main.show()
        self.aboutToQuit.connect(self.saveQueue)
        print("done starting")

    def saveQueue(self, *args, **kwargs):
        """Save the current state of the queue to disk."""
        print("Saving queue for next time")
        self.queue.save()


@click.command()
def main():
    """Start the Remote Batch Manager application."""
    print("in main")
    app = RemoteMgrApp(sys.argv)
    print("created remote batch app")
    app.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
