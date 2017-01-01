import os.path
from PyQt4 import QtCore, QtGui

from notifier import notify

threaded = True


class RunMe(QtCore.QThread):
    def __init__(self, func):
        super(RunMe, self).__init__()
        self.func = func

    def run(self):
        self.func()


class ManagerMain(QtGui.QMainWindow):
    def __init__(self, queue):
        """

        """
        super(ManagerMain, self).__init__()
        self.queue = queue

        widget = QtGui.QWidget()
        self.setCentralWidget(widget)

        jobListLabel = QtGui.QLabel("Current Jobs:")

        self.jobListBox = QtGui.QListWidget()
        self.jobs = {}

        layout = QtGui.QVBoxLayout()
        layout.addWidget(jobListLabel)
        # layout.addWidget(jobidValueLabel)
        layout.addWidget(self.jobListBox)

        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton("Retrieve", buttonBox.ActionRole).clicked.connect(self.retrieve)
        buttonBox.addButton("Delete", buttonBox.ActionRole).clicked.connect(self.delete)
        buttonBox.addButton("New", buttonBox.ActionRole).clicked.connect(self.newjob)
        self.refreshButton = buttonBox.addButton("Connect", buttonBox.ResetRole)
        self.refreshButton.clicked.connect(self.refresh)
        buttonBox.addButton("Cleanup", buttonBox.ResetRole)
        layout.addWidget(buttonBox)

        self.allAct = QtGui.QAction("&All", self, checkable=True,
                                    shortcut="Ctrl+A", statusTip="Show all jobs",
                                    triggered=self.refilter)
        self.resultsAct = QtGui.QAction("&Results", self, checkable=True,
                                        shortcut="Ctrl+R", statusTip="Show results only",
                                        triggered=self.refilter)
        settingsAct = QtGui.QAction("&Settings", self,
                                    statusTip="Edit settings",
                                    triggered=self.settings)
        aboutAct = QtGui.QAction("About", self,
                                 statusTip="Show the application's About box",
                                 triggered=self.about)

        filterGroup = QtGui.QActionGroup(self)
        filterGroup.addAction(self.allAct)
        filterGroup.addAction(self.resultsAct)
        self.allAct.setChecked(True)

        filterMenu = self.menuBar().addMenu("&Filter")
        filterMenu.addAction(self.allAct)
        filterMenu.addAction(self.resultsAct)
        filterMenu.addAction("Refresh", self.refresh)

        optionMenu = self.menuBar().addMenu("&Options")
        optionMenu.addAction(settingsAct)
        optionMenu.addAction(aboutAct)

        widget.setLayout(layout)

    def about(self):
        pass

    def settings(self):
        pass

    def refilter(self):
        print "running refilter"
        for job_item in self.jobs:
            job = self.jobs[job_item]
            if self.resultsAct.isChecked() and job.type != "results":
                job_item.setHidden(True)
            else:
                job_item.setHidden(False)

    def refresh(self):
        self.refreshButton.setText("Refreshing")
        if threaded:
            self.refresher = RunMe(self._refresh)
            self.refresher.start()
        else:
            self._refresh()

    def _refresh(self):
        self.jobListBox.clear()
        self.jobs = {}
        for job in self.queue.allJobs():
            self.jobs[QtGui.QListWidgetItem("%s:%d %s" % (job.type, job.size, job.storage) + ": " + str(job),
                                            self.jobListBox)] = job
        self.refilter()
        if self.queue.isConnected:
            self.refreshButton.setText("Refresh")
        else:
            self.refreshButton.setText("Connect")

    def newjob(self):
        dialog = AddJobDialog(self.queue)
        return dialog.exec_()

    def retrieve(self):
        """

        """
        job = self.jobListBox.currentItem()
        if job is None: return
        job = self.jobs[job]
        path = QtGui.QFileDialog.getExistingDirectory(self, "Retrieve to",
                                                      "~",
                                                      QtGui.QFileDialog.ShowDirsOnly);
        if not path:
            print "No path given"
            return
        try:
            notify("Retrieving job: " + str(job))
            tempdir = job.getFiles(str(path))
            notify("unzipped to %s" % tempdir)
            files = os.listdir(tempdir)
            print "path %s files %s" % (tempdir, files)
        except:
            notify("Unable to retrieve file.")

    def delete(self):
        item = self.jobListBox.currentItem()
        job = self.jobs[item]
        notify("Deleting job: " + str(job))
        self.queue.delete(job)
        self.jobListBox.removeItemWidget(item)
        item.setHidden(True)


class AddJobDialog(QtGui.QDialog):
    def __init__(self, queue, parent=None):
        super(AddJobDialog, self).__init__(parent)
        self.queue = queue
        self.job = queue.job_class()

        fileInfo = QtCore.QFileInfo(os.path.join(self.job.path, self.job.jobfile))

        tabWidget = QtGui.QTabWidget()
        self.generalTab = GeneralTab(self.job)
        tabWidget.addTab(self.generalTab, "General")
        # tabWidget.addTab(PermissionsTab(fileInfo), "Permissions")
        tabWidget.addTab(DetailsTab(self.job), "Details")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Remote Batch Runner")

    def exec_(self):
        if super(AddJobDialog, self).exec_():
            job = self.job
            notify("Bundling and sending " + str(job))
            self.queue.queue_job(job)
            return True

    def accept(self):
        self.job.set_jobfile(self.generalTab.targetPath, self.generalTab.targetFile)
        # print "self.job.set_jobfile(%s, %s)"%(self.generalTab.targetPath, self.generalTab.targetFile)
        return super(self.__class__, self).accept()


class GeneralTab(QtGui.QWidget):
    def __init__(self, job, parent=None):
        super(GeneralTab, self).__init__(parent)
        self.job = job

        self.fileNameEdit = QtGui.QLineEdit(job.jobfile)
        browseButton = self.createButton("&Browse...", self.browse)

        self.pathEdit = QtGui.QLineEdit(job.path)

        # lastReadLabel = QtGui.QLabel("Last Read:")
        # lastReadValueLabel = QtGui.QLabel(fileInfo.lastRead().toString())
        # lastReadValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        # lastModLabel = QtGui.QLabel("Last Modified:")
        # lastModValueLabel = QtGui.QLabel(fileInfo.lastModified().toString())
        # lastModValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(QtGui.QLabel("Job File/Path:"))
        mainLayout.addWidget(self.fileNameEdit)
        mainLayout.addWidget(self.pathEdit)
        mainLayout.addWidget(browseButton)
        # mainLayout.addWidget(lastReadLabel)
        # mainLayout.addWidget(lastReadValueLabel)
        # mainLayout.addWidget(lastModLabel)
        # mainLayout.addWidget(lastModValueLabel)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @property
    def targetPath(self):
        return os.path.abspath(str(self.pathEdit.text()))

    @property
    def targetFile(self):
        return str(self.fileNameEdit.text())

    def browse(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Job File",
                                                     self.pathEdit.text())
        if filename:
            path, filename = os.path.split(str(filename))
            self.fileNameEdit.setText(filename)
            self.pathEdit.setText(path)
            self.job.set_jobfile(path, filename)

    def createButton(self, text, member):
        button = QtGui.QPushButton(text)
        button.clicked.connect(member)
        return button


class PermissionsTab(QtGui.QWidget):
    def __init__(self, fileInfo, parent=None):
        super(PermissionsTab, self).__init__(parent)

        permissionsGroup = QtGui.QGroupBox("Permissions")

        readable = QtGui.QCheckBox("Readable")
        if fileInfo.isReadable():
            readable.setChecked(True)

        writable = QtGui.QCheckBox("Writable")
        if fileInfo.isWritable():
            writable.setChecked(True)

        executable = QtGui.QCheckBox("Executable")
        if fileInfo.isExecutable():
            executable.setChecked(True)

        ownerGroup = QtGui.QGroupBox("Ownership")

        ownerLabel = QtGui.QLabel("Owner")
        ownerValueLabel = QtGui.QLabel(fileInfo.owner())
        ownerValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        groupLabel = QtGui.QLabel("Group")
        groupValueLabel = QtGui.QLabel(fileInfo.group())
        groupValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        permissionsLayout = QtGui.QVBoxLayout()
        permissionsLayout.addWidget(readable)
        permissionsLayout.addWidget(writable)
        permissionsLayout.addWidget(executable)
        permissionsGroup.setLayout(permissionsLayout)

        ownerLayout = QtGui.QVBoxLayout()
        ownerLayout.addWidget(ownerLabel)
        ownerLayout.addWidget(ownerValueLabel)
        ownerLayout.addWidget(groupLabel)
        ownerLayout.addWidget(groupValueLabel)
        ownerGroup.setLayout(ownerLayout)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(permissionsGroup)
        mainLayout.addWidget(ownerGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class DetailsTab(QtGui.QWidget):
    def __init__(self, job, parent=None):
        super(DetailsTab, self).__init__(parent)
        self.job = job

        topLabel = QtGui.QLabel("Job Type:")

        self.applicationsListBox = QtGui.QListWidget()
        applications = ["Povray", "Upgrade", "Shell"]

        self.applicationsListBox.insertItems(0, applications)
        self.applicationsListBox.itemSelectionChanged.connect(self.update_job)

        alwaysCheckBox = QtGui.QCheckBox()

        if False:
            alwaysCheckBox = QtGui.QCheckBox("Always use this application to "
                                             "open files with the extension '%s'" % fileInfo.suffix())
        else:
            alwaysCheckBox = QtGui.QCheckBox("Always use this application to "
                                             "open this type of file")

        jobidLabel = QtGui.QLabel("Job ID:")
        self.jobID = job.id
        jobidValueLabel = QtGui.QLabel(self.jobID)
        jobidValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        layout = QtGui.QVBoxLayout()
        # layout.addWidget(jobidLabel)
        # layout.addWidget(jobidValueLabel)
        layout.addWidget(self.applicationsListBox)
        layout.addWidget(alwaysCheckBox)
        self.setLayout(layout)

    def update_job(self):
        self.job.type = str(self.applicationsListBox.currentItem().text())

    def showEvent(self, QShowEvent):
        super(DetailsTab, self).showEvent(QShowEvent)
