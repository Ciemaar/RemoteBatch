try:
    import osso

    osso_c = osso.Context("Remote_Batch", "0.0.2", False)


    def notify(message, title="Remoted Batch"):
        note = osso.SystemNote(osso_c)
        note.system_note_infoprint(message)

except:

    def notify(message, title="Remoted Batch"):
        pass
