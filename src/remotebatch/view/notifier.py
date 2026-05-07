"""Notifications module for the application."""

import logging

log = logging.getLogger(__name__)


try:
    import osso  # type: ignore

    def notify(message: str, title: str = "Remoted Batch") -> None:
        """Send a notification using osso framework.

        Args:
            message (str): The message to display.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        note = osso.Context().get_system_note()
        note.system_note_infoprint(message)

except Exception:

    def notify(message: str, title: str = "Remoted Batch") -> None:
        """Print a notification to the console.

        Args:
            message (str): The message to print.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        log.debug(message)
