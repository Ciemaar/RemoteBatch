#!/usr/bin/env python

#############################################################################
##
## Copyright (C) 2004-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

import os.path

from PyQt6 import QtCore, QtGui, QtWidgets

from view.notifier import notify

threaded = True


class RunMe(QtCore.QThread):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        self.func()


class ManagerMain(QtWidgets.QMainWindow):
    def __init__(self, queue):
        """

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
        # layout.addWidget(jobidValueLabel)
        layout.addWidget(self.jobListBox)

        buttonBox = QtWidgets.QDialogButtonBox()
        buttonBox.addButton("Retrieve", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole).clicked.connect(self.retrieve)
        buttonBox.addButton("Delete", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole).clicked.connect(self.delete)
        buttonBox.addButton("New", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole).clicked.connect(self.newjob)
        self.refreshButton = buttonBox.addButton("Connect", QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        self.refreshButton.clicked.connect(self.refresh)
        buttonBox.addButton("Cleanup", QtWidgets.QDialogButtonBox.ButtonRole.ResetRole)
        layout.addWidget(buttonBox)

        # In PyQt6, QAction is in QtGui
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
        print("running refilter")
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
            item = QtWidgets.QListWidgetItem("%s:%d %s" % (job.type, job.size, job.storage) + ": " + str(job), self.jobListBox)
            self.jobs[item] = job
        self.refilter()
        if self.queue.isConnected:
            self.refreshButton.setText("Refresh")
        else:
            self.refreshButton.setText("Connect")

    def newjob(self):
        dialog = AddJobDialog(self.queue)
        return dialog.exec()

    def retrieve(self):
        """

        """
        job_item = self.jobListBox.currentItem()
        if job_item is None:
            return
        job = self.jobs[job_item]
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Retrieve to",
                                                      "~",
                                                      QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if not path:
            print("No path given")
            return
        try:
            notify("Retrieving job: " + str(job))
            tempdir = job.getFiles(str(path))
            notify("unzipped to %s" % tempdir)
            files = os.listdir(tempdir)
            print("path %s files %s" % (tempdir, files))
        except Exception:
            notify("Unable to retrieve file.")

    def delete(self):
        item = self.jobListBox.currentItem()
        if not item:
            return
        job = self.jobs[item]
        notify("Deleting job: " + str(job))
        self.queue.delete(job)
        self.jobListBox.takeItem(self.jobListBox.row(item))
        # item.setHidden(True) # Removed from listbox already


class AddJobDialog(QtWidgets.QDialog):
    def __init__(self, queue, parent=None):
        super().__init__(parent)
        self.queue = queue
        self.job = queue.job_class()

        # Ensure path exists before using it
        if self.job.path is None:
             self.job.path = os.getcwd()

        # fileInfo = QtCore.QFileInfo(os.path.join(self.job.path, self.job.jobfile if self.job.jobfile else ""))

        tabWidget = QtWidgets.QTabWidget()
        self.generalTab = GeneralTab(self.job)
        tabWidget.addTab(self.generalTab, "General")
        # tabWidget.addTab(PermissionsTab(fileInfo), "Permissions")
        tabWidget.addTab(DetailsTab(self.job), "Details")

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Remote Batch Runner")

    def exec(self):
        if super().exec():
            job = self.job
            notify("Bundling and sending " + str(job))
            self.queue.queue_job(job)
            return True

    def accept(self):
        self.job.set_jobfile(self.generalTab.targetPath, self.generalTab.targetFile)
        # print "self.job.set_jobfile(%s, %s)"%(self.generalTab.targetPath, self.generalTab.targetFile)
        return super(self.__class__, self).accept()


class GeneralTab(QtWidgets.QWidget):
    def __init__(self, job, parent=None):
        super().__init__(parent)
        self.job = job

        self.fileNameEdit = QtWidgets.QLineEdit(job.jobfile)
        browseButton = self.createButton("&Browse...", self.browse)

        self.pathEdit = QtWidgets.QLineEdit(job.path)

        # lastReadLabel = QtGui.QLabel("Last Read:")
        # lastReadValueLabel = QtGui.QLabel(fileInfo.lastRead().toString())
        # lastReadValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        # lastModLabel = QtGui.QLabel("Last Modified:")
        # lastModValueLabel = QtGui.QLabel(fileInfo.lastModified().toString())
        # lastModValueLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(QtWidgets.QLabel("Job File/Path:"))
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
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Job File",
                                                     self.pathEdit.text())
        if filename:
            path, filename = os.path.split(str(filename))
            self.fileNameEdit.setText(filename)
            self.pathEdit.setText(path)
            self.job.set_jobfile(path, filename)

    def createButton(self, text, member):
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(member)
        return button


class PermissionsTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
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
    def __init__(self, job, parent=None):
        super().__init__(parent)
        self.job = job

        self.topLabel = QtWidgets.QLabel("Job Type:")

        self.applicationsListBox = QtWidgets.QListWidget()
        applications = ["Povray", "Upgrade", "Shell"]

        self.applicationsListBox.insertItems(0, applications)
        self.applicationsListBox.itemSelectionChanged.connect(self.update_job)

        # alwaysCheckBox = QtWidgets.QCheckBox()

        # if False:
        #     alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to "
        #                                      "open files with the extension '%s'" % fileInfo.suffix())
        # else:
        #     alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to "
        #                                      "open this type of file")

        # jobidLabel = QtWidgets.QLabel("Job ID:")
        self.jobID = job.id
        # jobidValueLabel = QtWidgets.QLabel(self.jobID)
        # jobidValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(jobidLabel)
        # layout.addWidget(jobidValueLabel)
        layout.addWidget(self.applicationsListBox)
        # layout.addWidget(alwaysCheckBox)
        self.setLayout(layout)

    def update_job(self):
        item = self.applicationsListBox.currentItem()
        if item:
             self.job.type = str(item.text())

    def showEvent(self, QShowEvent):
        super().showEvent(QShowEvent)
