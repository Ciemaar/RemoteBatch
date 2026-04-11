"""View package containing GUI components for the application."""

import logging
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from remotebatch.view.notifier import notify

log = logging.getLogger(__name__)


threaded = True


class RunMe(QtCore.QThread):
    """A thread class to run a given function asynchronously."""

    def __init__(self, func):
        """Initialize the RunMe thread.

        Args:
            func (callable): The function to execute in the thread.
        """
        super().__init__()
        self.func = func

    def run(self):
        """Execute the stored function."""
        self.func()


class ManagerMain(QtWidgets.QMainWindow):
    """The main window for the Batch Manager application."""

    def __init__(self, queue):
        """Initialize the main manager window.

        Args:
            queue (BatchQueue): The queue backend to interface with.
        """
        super().__init__()
        self.queue = queue

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)

        jobListLabel = QtWidgets.QLabel("Current Jobs:")

        self.jobListBox = QtWidgets.QListWidget()
        self.jobs = {}

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(jobListLabel)
        layout.addWidget(self.jobListBox)

        buttonBox = QtWidgets.QDialogButtonBox()
        retrieve_btn = buttonBox.addButton("Retrieve", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        if retrieve_btn is not None:
            retrieve_btn.clicked.connect(self.retrieve)
        delete_btn = buttonBox.addButton("Delete", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        if delete_btn is not None:
            delete_btn.clicked.connect(self.delete)
        new_btn = buttonBox.addButton("New", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        if new_btn is not None:
            new_btn.clicked.connect(self.newjob)
        self.refreshButton = buttonBox.addButton("Connect", QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        if self.refreshButton is not None:
            self.refreshButton.clicked.connect(self.refresh)
        buttonBox.addButton("Cleanup", QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        layout.addWidget(buttonBox)

        self.allAct = QtGui.QAction("&All", self)
        self.allAct.setCheckable(True)
        self.allAct.setShortcut("Ctrl+A")
        self.allAct.setStatusTip("Show all jobs")
        self.allAct.triggered.connect(self.refilter)

        self.resultsAct = QtGui.QAction("&Results", self)
        self.resultsAct.setCheckable(True)
        self.resultsAct.setShortcut("Ctrl+R")
        self.resultsAct.setStatusTip("Show results only")
        self.resultsAct.triggered.connect(self.refilter)

        settingsAct = QtGui.QAction("&Settings", self)
        settingsAct.setStatusTip("Edit settings")
        settingsAct.triggered.connect(self.settings)

        aboutAct = QtGui.QAction("About", self)
        aboutAct.setStatusTip("Show the application's About box")
        aboutAct.triggered.connect(self.about)

        filterGroup = QtGui.QActionGroup(self)
        filterGroup.addAction(self.allAct)
        filterGroup.addAction(self.resultsAct)
        self.allAct.setChecked(True)

        menu_bar = self.menuBar()
        if menu_bar is not None:
            filterMenu = menu_bar.addMenu("&Filter")
            if filterMenu is not None:
                filterMenu.addAction(self.allAct)
                filterMenu.addAction(self.resultsAct)
                filterMenu.addAction("Refresh", self.refresh)

            optionMenu = menu_bar.addMenu("&Options")
            if optionMenu is not None:
                optionMenu.addAction(settingsAct)
                optionMenu.addAction(aboutAct)

        widget.setLayout(layout)

    def about(self):
        """Show the about dialog."""
        pass

    def settings(self):
        """Show the settings dialog."""
        pass

    def refilter(self):
        """Filter the visible jobs based on selected filter action."""
        log.debug("running refilter")
        for job_item in self.jobs:
            job = self.jobs[job_item]
            if self.resultsAct.isChecked() and job.type != "results":
                job_item.setHidden(True)
            else:
                job_item.setHidden(False)

    def refresh(self):
        """Trigger a refresh of the job list from the queue."""
        if self.refreshButton is not None:
            self.refreshButton.setText("Refreshing")
        if threaded:
            self.refresher = RunMe(self._refresh)
            self.refresher.start()
        else:
            self._refresh()

    def _refresh(self):
        """Internal method to perform the queue refresh operation."""
        self.jobListBox.clear()
        self.jobs = {}
        for job in self.queue.allJobs():
            item_text = f"{job.type}:{job.size} {job.storage}: {str(job)}"
            item = QtWidgets.QListWidgetItem(item_text, self.jobListBox)
            self.jobs[item] = job
        self.refilter()
        if self.refreshButton is not None:
            if self.queue.isConnected:
                self.refreshButton.setText("Refresh")
            else:
                self.refreshButton.setText("Connect")

    def newjob(self):
        """Open the Add Job dialog to submit a new job."""
        dialog = AddJobDialog(self.queue)
        return dialog.exec()

    def retrieve(self):
        """Retrieve the results of the currently selected job."""
        job_item = self.jobListBox.currentItem()
        if job_item is None:
            return
        job = self.jobs[job_item]
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Retrieve to", "~", QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        if not path:
            log.debug("No path given")
            return
        try:
            notify(f"Retrieving job: {str(job)}")
            tempdir = job.getFiles(str(path))
            notify(f"unzipped to {tempdir}")
            files = [f.name for f in Path(tempdir).iterdir()]
            log.debug(f"path {tempdir} files {files}")
        except Exception:
            notify("Unable to retrieve file.")

    def delete(self):
        """Delete the currently selected job from the queue."""
        item = self.jobListBox.currentItem()
        if not item:
            return
        job = self.jobs[item]
        notify(f"Deleting job: {str(job)}")
        self.queue.delete(job)
        self.jobListBox.takeItem(self.jobListBox.row(item))


class AddJobDialog(QtWidgets.QDialog):
    """Dialog window for adding a new job to the queue."""

    def __init__(self, queue, parent=None):
        """Initialize the Add Job dialog.

        Args:
            queue (BatchQueue): The queue backend to submit jobs to.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.queue = queue
        self.job = queue.job_class()

        # Ensure path exists before using it
        if self.job.path is None:
            self.job.path = str(Path.cwd())

        tabWidget = QtWidgets.QTabWidget()
        self.generalTab = GeneralTab(self.job)
        tabWidget.addTab(self.generalTab, "General")
        tabWidget.addTab(DetailsTab(self.job), "Details")

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Remote Batch Runner")

    def exec(self) -> int:
        """Execute the dialog and add the job if accepted.

        Returns:
            int: 1 if the dialog was accepted and job queued, 0 otherwise.
        """
        res = super().exec()
        if res:
            job = self.job
            notify(f"Bundling and sending {str(job)}")
            self.queue.queue_job(job)
        return res

    def accept(self):
        """Handle dialog acceptance, updating the job target."""
        self.job.set_jobfile(self.generalTab.targetPath, self.generalTab.targetFile)
        return super(self.__class__, self).accept()


class GeneralTab(QtWidgets.QWidget):
    """Tab containing general settings for a job like file paths."""

    def __init__(self, job, parent=None):
        """Initialize the General Tab.

        Args:
            job (Job): The target job object to configure.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.job = job

        self.fileNameEdit = QtWidgets.QLineEdit(job.jobfile)
        browseButton = self.createButton("&Browse...", self.browse)

        self.pathEdit = QtWidgets.QLineEdit(job.path)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(QtWidgets.QLabel("Job File/Path:"))
        mainLayout.addWidget(self.fileNameEdit)
        mainLayout.addWidget(self.pathEdit)
        mainLayout.addWidget(browseButton)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @property
    def targetPath(self):
        """Get the absolute target path from the UI.

        Returns:
            str: The target directory path.
        """
        return str(Path(self.pathEdit.text()).resolve())

    @property
    def targetFile(self):
        """Get the target file name from the UI.

        Returns:
            str: The target file name.
        """
        return str(self.fileNameEdit.text())

    def browse(self):
        """Open a file dialog to browse for a target job file."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Job File", self.pathEdit.text())
        if filename:
            p = Path(filename)
            path = str(p.parent)
            filename = str(p.name)
            self.fileNameEdit.setText(filename)
            self.pathEdit.setText(path)
            self.job.set_jobfile(path, filename)

    def createButton(self, text, member):
        """Create a button connected to a specific member function.

        Args:
            text (str): The label for the button.
            member (callable): The function to connect to the clicked signal.

        Returns:
            QPushButton: The created button instance.
        """
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(member)
        return button


class PermissionsTab(QtWidgets.QWidget):
    """Tab displaying file permissions and ownership."""

    def __init__(self, fileInfo, parent=None):
        """Initialize the Permissions Tab.

        Args:
            fileInfo (QFileInfo): The target file info object.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        permissionsGroup = QtWidgets.QGroupBox("Permissions")

        readable = QtWidgets.QCheckBox("Readable")
        if fileInfo.isReadable():
            readable.setChecked(True)

        writable = QtWidgets.QCheckBox("Writable")
        if fileInfo.isWritable():
            writable.setChecked(True)

        executable = QtWidgets.QCheckBox("Executable")
        if fileInfo.isExecutable():
            executable.setChecked(True)

        ownerGroup = QtWidgets.QGroupBox("Ownership")

        ownerLabel = QtWidgets.QLabel("Owner")
        ownerValueLabel = QtWidgets.QLabel(fileInfo.owner())
        ownerValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        groupLabel = QtWidgets.QLabel("Group")
        groupValueLabel = QtWidgets.QLabel(fileInfo.group())
        groupValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        permissionsLayout = QtWidgets.QVBoxLayout()
        permissionsLayout.addWidget(readable)
        permissionsLayout.addWidget(writable)
        permissionsLayout.addWidget(executable)
        permissionsGroup.setLayout(permissionsLayout)

        ownerLayout = QtWidgets.QVBoxLayout()
        ownerLayout.addWidget(ownerLabel)
        ownerLayout.addWidget(ownerValueLabel)
        ownerLayout.addWidget(groupLabel)
        ownerLayout.addWidget(groupValueLabel)
        ownerGroup.setLayout(ownerLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(permissionsGroup)
        mainLayout.addWidget(ownerGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class DetailsTab(QtWidgets.QWidget):
    """Tab containing detailed settings for a job, such as its type."""

    def __init__(self, job, parent=None):
        """Initialize the Details Tab.

        Args:
            job (Job): The target job object to configure.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.job = job

        self.topLabel = QtWidgets.QLabel("Job Type:")

        self.applicationsListBox = QtWidgets.QListWidget()
        applications = ["Povray", "Upgrade", "Shell"]

        self.applicationsListBox.insertItems(0, applications)
        self.applicationsListBox.itemSelectionChanged.connect(self.update_job)

        self.jobID = job.id

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.applicationsListBox)
        self.setLayout(layout)

    def update_job(self):
        """Update the job type based on list box selection."""
        item = self.applicationsListBox.currentItem()
        if item:
            self.job.type = str(item.text())

    def showEvent(self, a0):
        """Handle widget show events."""
        super().showEvent(a0)
