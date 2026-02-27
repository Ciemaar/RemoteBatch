try:
    import osso

    def notify(message, title="Remoted Batch"):
        """ """
        note = osso.Context().get_system_note()
        note.system_note_infoprint(message)

except Exception:

    def notify(message, title="Remoted Batch"):
        """ """
        print(message)
