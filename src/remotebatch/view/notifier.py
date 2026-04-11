"""Notifications module for the application."""

try:
    import osso

    def notify(message, title="Remoted Batch"):
        """Send a notification using osso framework.

        Args:
            message (str): The message to display.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        note = osso.Context().get_system_note()
        note.system_note_infoprint(message)

except Exception:

    def notify(message, title="Remoted Batch"):
        """Print a notification to the console.

        Args:
            message (str): The message to print.
            title (str, optional): The title of the notification. Defaults to "Remoted Batch".
        """
        print(message)
