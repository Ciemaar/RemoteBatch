# RemoteBatch User Guide

## Installation

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
   pip install .
   ```

## Running the Applications

The project includes two main graphical applications and a server daemon.

### 1. Remote Batch Client (`remotebatch`)

The Remote Batch Client is a simple utility to quickly add a new job to the queue from a specific file.

```bash
remotebatch [path/to/file]
```

If a path is provided, it automatically selects that file as the target job file. Otherwise, it defaults to the current directory.

### 2. Batch Manager (`batchmanager`)

The Batch Manager is the main GUI for overseeing all jobs in the queue.

```bash
batchmanager
```

- **Retrieve**: Download the results of a completed job to a specified local directory.
- **Delete**: Remove a job from the queue.
- **New**: Open a dialog to add a new job to the queue. You can specify the file, path, and job type (e.g., "Povray").
- **Connect/Refresh**: Manually refresh the list of jobs from the remote queue.

### 3. Server Daemon (`batchserver`)

The server daemon continuously polls the queue for new jobs, processes them, and uploads the results back to the queue.

```bash
batchserver
```

*Note: The server currently specifically processes "Povray" job types by invoking the `/usr/bin/povray` executable.*
