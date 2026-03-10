# PyQt6 Developer Guide

This guide is intended for developers who are new to PyQt6 and graphical user interface (GUI) development in general. It explains the core concepts used in this project's GUI applications (`RemoteBatch.py` and `BatchManager.py`).

## What is PyQt6?

PyQt6 is a comprehensive set of Python bindings for Qt v6, a powerful cross-platform C++ application framework. It allows you to write desktop applications that look and feel native on Windows, macOS, and Linux.

## Core Concepts

### 1. The Application and the Event Loop

Every PyQt6 application must have exactly one `QApplication` object. This object manages application-wide resources and, most importantly, the **event loop**.

```python
import sys
from PyQt6 import QtWidgets

# Create the application object
app = QtWidgets.QApplication(sys.argv)

# ... create and show windows here ...

# Start the event loop
sys.exit(app.exec())
```

**The Event Loop** is an infinite loop that waits for user interactions (mouse clicks, key presses) or system events (timers, network data). When an event occurs, the loop dispatches it to the appropriate widget. If the event loop is blocked (e.g., by a long-running calculation like a network request or file processing), the entire UI will freeze.

### 2. Widgets and Layouts

**Widgets** are the building blocks of the UI. Everything you see is a widget: buttons (`QPushButton`), labels (`QLabel`), text inputs (`QLineEdit`), lists (`QListWidget`), and even the main window itself (`QMainWindow` or `QDialog`).

**Layouts** dictate how widgets are arranged within their parent widget. Instead of hardcoding (x, y) coordinates, you add widgets to a layout, and the layout automatically handles sizing and positioning, adapting gracefully when the window is resized.

Common layouts:

- `QVBoxLayout`: Arranges widgets vertically, top to bottom.
- `QHBoxLayout`: Arranges widgets horizontally, left to right.

Example:

```python
window = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout()

label = QtWidgets.QLabel("Hello World")
button = QtWidgets.QPushButton("Click Me")

layout.addWidget(label)
layout.addWidget(button)

window.setLayout(layout)
window.show()
```

### 3. Signals and Slots (Event Handling)

This is PyQt's mechanism for communication between objects.

- **Signals** are emitted when a specific event occurs (e.g., a button is `clicked`).
- **Slots** are Python callable functions or methods that are executed in response to a signal.

You "connect" a signal to a slot to make things happen.

```python
def my_custom_function():
    print("Button was clicked!")

button = QtWidgets.QPushButton("Click Me")
# Connect the 'clicked' signal to the 'my_custom_function' slot
button.clicked.connect(my_custom_function)
```

In this codebase, look at how the `refreshButton` in `ManagerMain` connects its `clicked` signal to the `refresh` method.

### 4. Dialogs

Dialogs (`QDialog`) are pop-up windows used to interact with the user for a specific task. They can be *modal* (blocking interaction with the main window until closed) or *modeless*.
Our `AddJobDialog` is executed modally using the `.exec()` method. It returns a result code (like `QDialog.DialogCode.Accepted` if the user clicks "Ok").

### 5. Threading (`QThread`)

As mentioned, blocking the event loop freezes the UI. If you need to perform a slow operation (like fetching a list of remote jobs from S3), you should offload that work to a separate thread.

PyQt provides `QThread` for this purpose.

In `view/__init__.py`, you will see a `RunMe` class that inherits from `QThread`.

```python
class RunMe(QtCore.QThread):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        self.func()
```

When `ManagerMain.refresh()` is called, it initializes a `RunMe` thread with the actual refresh logic and calls `.start()`. The `run()` method executes in the background, allowing the GUI to remain responsive (for example, showing a "Refreshing" button state) while the remote queue is queried.

*Important Note:* You should generally only update UI elements (widgets) from the main thread. If a background thread needs to update the UI, it should emit a signal that is connected to a slot running in the main thread.

### 6. Testing PyQt Apps

Testing GUIs can be tricky. We use `pytest-qt`, which provides fixtures (like `qapp`) that handle setting up the `QApplication` and event loop for tests.

When testing locally or in CI (like GitHub Actions) on systems without a display server (e.g., a Linux terminal), GUI tests will crash. We use `xvfb` (X virtual framebuffer) in our CI pipeline to simulate a display so the PyQt application can render headlessly.
