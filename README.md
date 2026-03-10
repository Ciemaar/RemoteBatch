# RemoteBatch

A modern Python 3.12+ application for delegating work from one machine to another. This tool allows users to queue jobs (such as Povray renders or other tasks) on a client machine and execute them on a remote server, with results sent back.

## Features

- **GUI Client**: User-friendly Qt6 interface to add, retrieve, and manage jobs.
- **Job Management**: Support for different job types (e.g., Povray, Upgrade, Shell).
- **Queue Abstraction**: Built-in support for AWS S3 queues (`BatchQueue`) and a fallback filesystem queue (`LocalQueue`) for testing and local execution.
- **Modern Python Tooling**: Uses `ruff` for linting, `pyright` for type checking, and `pytest` for testing.

______________________________________________________________________

## User Documentation

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Ciemaar/RemoteBatch.git
   cd RemoteBatch
   ```

1. **Create a virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Running the Applications

The project includes two main graphical applications and a server daemon.

#### 1. Remote Batch Client (`RemoteBatch.py`)

The Remote Batch Client is a simple utility to quickly add a new job to the queue from a specific file.

```bash
python RemoteBatch.py [path/to/file]
```

If a path is provided, it automatically selects that file as the target job file. Otherwise, it defaults to the current directory.

#### 2. Batch Manager (`BatchManager.py`)

The Batch Manager is the main GUI for overseeing all jobs in the queue.

```bash
python BatchManager.py
```

- **Retrieve**: Download the results of a completed job to a specified local directory.
- **Delete**: Remove a job from the queue.
- **New**: Open a dialog to add a new job to the queue. You can specify the file, path, and job type (e.g., "Povray").
- **Connect/Refresh**: Manually refresh the list of jobs from the remote queue.

#### 3. Server Daemon (`server.py`)

The server daemon continuously polls the queue for new jobs, processes them, and uploads the results back to the queue.

```bash
python server.py
```

*Note: The server currently specifically processes "Povray" job types by invoking the `/usr/bin/povray` executable.*

______________________________________________________________________

## Developer Documentation

### Setup

To set up the development environment, install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Architecture

The application is built around the concept of a "Queue" and "Jobs".

- **`model.Job`**: Represents a unit of work. It encapsulates the file payload (stored as a `.tar.gz` archive), metadata (job type, ID), and logic to serialize/deserialize itself.
- **`model.BatchQueue`**: The interface to the queue. The default implementation targets an AWS S3 bucket, where jobs are stored as objects and metadata is stored in object metadata.
- **`model.LocalQueue`**: A filesystem-backed implementation of the queue used for local testing without AWS credentials. It stores job payloads and metadata (`.meta` files) in a local directory.

### Adding New Job Types

To add a new job type:

1. Update the `DetailsTab` in `view/__init__.py` to include the new job type in the `applicationsListBox`.
1. Modify the `processJob` function in `server.py` to handle the specific execution logic for the new job type.

### Tooling & Setup

- **Type Checking**: This project uses `pyright`.
  ```bash
  pyright
  ```
- **Linting & Formatting**: This project uses `ruff`.
  ```bash
  ruff check .
  ruff format .
  ```
- **Markdown Formatting**:
  ```bash
  mdformat .
  ```

### Testing

Tests are written using `pytest` and `hypothesis` for property-based testing. They use the `LocalQueue` to simulate the S3 queue interactions.

```bash
pytest
```

To run tests with detailed output:

```bash
pytest -v
```

### AWS Implementation Notes

The original implementation relied on an outdated `boto` version. It has been migrated to `boto3`. By default, tests and local runs use `LocalQueue` or mock the S3 interactions. To use the actual AWS S3 queue, ensure you have valid AWS credentials configured (e.g., via `~/.aws/credentials`) and update `app_secrets.py` with your `REMOTE_BATCH_BUCKET` name.
