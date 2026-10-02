"""Notifications module for the application."""

import logging

log = logging.getLogger(__name__)


try:
    from plyer import notification  # type: ignore

    def notify(message: str, title: str = "Remoted Batch") -> None:
        """Send a notification using plyer framework.

        Args:
            message (str): The message to display.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        notification.notify(title=title, message=message, app_name="RemoteBatch")  # type: ignore

except Exception as e:
    log.warning(f"Failed to load plyer notification system: {e}")

    def notify(message: str, title: str = "Remoted Batch") -> None:
        """Print a notification to the console.

        Args:
            message (str): The message to print.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        log.debug(message)
