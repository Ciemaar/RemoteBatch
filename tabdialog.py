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

from PyQt6 import QtCore, QtWidgets

ARGS_MIN_LENGTH = 2

class TabDialog(QtWidgets.QDialog):
    def __init__(self, fileName, parent=None):
        super().__init__(parent)

        fileInfo = QtCore.QFileInfo(fileName)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(GeneralTab(fileInfo), "General")
        tabWidget.addTab(PermissionsTab(fileInfo), "Permissions")
        tabWidget.addTab(ApplicationsTab(fileInfo), "Applications")

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Tab Dialog")


class GeneralTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
        super().__init__(parent)

        fileNameLabel = QtWidgets.QLabel("File Name:")
        fileNameEdit = QtWidgets.QLineEdit(fileInfo.fileName())

        pathLabel = QtWidgets.QLabel("Path:")
        pathValueLabel = QtWidgets.QLabel(fileInfo.absoluteFilePath())
        pathValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        sizeLabel = QtWidgets.QLabel("Size:")
        size = fileInfo.size() // 1024
        sizeValueLabel = QtWidgets.QLabel("%d K" % size)
        sizeValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        lastReadLabel = QtWidgets.QLabel("Last Read:")
        lastReadValueLabel = QtWidgets.QLabel(fileInfo.lastRead().toString())
        lastReadValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        lastModLabel = QtWidgets.QLabel("Last Modified:")
        lastModValueLabel = QtWidgets.QLabel(fileInfo.lastModified().toString())
        lastModValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(fileNameLabel)
        mainLayout.addWidget(fileNameEdit)
        mainLayout.addWidget(pathLabel)
        mainLayout.addWidget(pathValueLabel)
        mainLayout.addWidget(sizeLabel)
        mainLayout.addWidget(sizeValueLabel)
        mainLayout.addWidget(lastReadLabel)
        mainLayout.addWidget(lastReadValueLabel)
        mainLayout.addWidget(lastModLabel)
        mainLayout.addWidget(lastModValueLabel)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


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


class ApplicationsTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
        super().__init__(parent)

        topLabel = QtWidgets.QLabel("Open with:")

        applicationsListBox = QtWidgets.QListWidget()
        applications = []

        for i in range(1, 31):
            applications.append("Application %d" % i)

        applicationsListBox.insertItems(0, applications)

        alwaysCheckBox = QtWidgets.QCheckBox()

        if fileInfo.suffix():
            alwaysCheckBox = QtWidgets.QCheckBox(
                "Always use this application to open files with the extension '%s'" % fileInfo.suffix()
            )
        else:
            alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to open this type of file")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(topLabel)
        layout.addWidget(applicationsListBox)
        layout.addWidget(alwaysCheckBox)
        self.setLayout(layout)


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    fileName = sys.argv[1] if len(sys.argv) >= ARGS_MIN_LENGTH else "."

    tabdialog = TabDialog(fileName)
    sys.exit(tabdialog.exec())
