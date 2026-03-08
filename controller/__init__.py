"""Controller package for the RemoteBatch GUI application."""

from view import AddJobDialog, ManagerMain


def mgr_main(queue):
    """Launch and return the main manager window.

    Args:
        queue (BatchQueue): The queue instance to be managed.

    Returns:
        ManagerMain: The initialized and displayed main manager window.
    """
    main = ManagerMain(queue)
    main.refresh()
    main.show()
    return main


def job_dialog(path, queue):
    """Launch the dialog for adding a new job to the queue.

    Args:
        path (str): The initial directory path to open in the dialog.
        queue (BatchQueue): The queue instance where the new job will be added.

    Returns:
        int: The execution result of the dialog.
    """
    tabdialog = AddJobDialog(queue)
    print("created tabdialog")
    return tabdialog.exec()
