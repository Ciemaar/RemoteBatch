# RemoteBatch

A modern Python 3.12+ application for delegating work from one machine to another.
This tool allows users to queue jobs on a client machine and execute them
on a remote server, with results sent back.

## Features

- **GUI Client**: User-friendly Qt6 interface to add, retrieve, and manage jobs.
- **Job Management**: Support for different job types.
- **Queue Abstraction**: Built-in support for AWS S3 queues (`BatchQueue`) and a
  fallback filesystem queue (`LocalQueue`).
- **Modern Python Tooling**: Uses `ruff`, `pyright`, and `pytest`.

## Documentation

- [User Guide](USER_GUIDE.md): Installation and usage instructions.
- [Developer Guide](DEVELOPER_GUIDE.md): Architecture, setup, and PyQt introduction.
