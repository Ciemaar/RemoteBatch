#!/usr/bin/env python

"""Module containing the TabDialog and its constituent tabs for Job details."""

from PyQt6 import QtCore, QtWidgets


class TabDialog(QtWidgets.QDialog):
    """A dialog window featuring multiple tabs for file information."""

    def __init__(self, fileName, parent=None):
        """Initialize the TabDialog.

        Args:
            fileName (str): The path to the file to display information for.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
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
    """Tab displaying general file information."""

    def __init__(self, fileInfo, parent=None):
        """Initialize the GeneralTab.

        Args:
            fileInfo (QFileInfo): Information about the file.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        fileNameLabel = QtWidgets.QLabel("File Name:")
        fileNameEdit = QtWidgets.QLineEdit(fileInfo.fileName())

        pathLabel = QtWidgets.QLabel("Path:")
        pathValueLabel = QtWidgets.QLabel(fileInfo.absoluteFilePath())
        pathValueLabel.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Sunken)

        sizeLabel = QtWidgets.QLabel("Size:")
        size = fileInfo.size() // 1024
        sizeValueLabel = QtWidgets.QLabel(f"{size} K")
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
    """Tab displaying file permissions and ownership."""

    def __init__(self, fileInfo, parent=None):
        """Initialize the PermissionsTab.

        Args:
            fileInfo (QFileInfo): Information about the file.
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


class ApplicationsTab(QtWidgets.QWidget):
    """Tab displaying application association options."""

    def __init__(self, fileInfo, parent=None):
        """Initialize the ApplicationsTab.

        Args:
            fileInfo (QFileInfo): Information about the file.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        topLabel = QtWidgets.QLabel("Open with:")

        applicationsListBox = QtWidgets.QListWidget()
        applications = []

        for i in range(1, 31):
            applications.append(f"Application {i}")

        applicationsListBox.insertItems(0, applications)

        alwaysCheckBox = QtWidgets.QCheckBox()

        if fileInfo.suffix():
            alwaysCheckBox = QtWidgets.QCheckBox(
                f"Always use this application to open files with the extension '{fileInfo.suffix()}'"
            )
        else:
            alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to open this type of file")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(topLabel)
        layout.addWidget(applicationsListBox)
        layout.addWidget(alwaysCheckBox)
        self.setLayout(layout)


if __name__ == "__main__":
    import sys

    ARGS_MIN_LENGTH = 2

    app = QtWidgets.QApplication(sys.argv)

    fileName = sys.argv[1] if len(sys.argv) >= ARGS_MIN_LENGTH else "."

    tabdialog = TabDialog(fileName)
    sys.exit(tabdialog.exec())
