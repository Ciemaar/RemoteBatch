# Future Features & Roadmap

This document outlines potential future features, expected enhancements, and logical extensions to the RemoteBatch system that have been discussed or identified during development.

## 1. Multi-Queue / Plugin Architecture for Storage

Currently, the system relies on an AWS S3 `BatchQueue` and a filesystem-backed `LocalQueue`. A logical extension is to introduce a formal plugin system or registry for different storage backends (e.g., Azure Blob Storage, Google Cloud Storage, or Redis Queues) to allow users to switch queue implementations dynamically via configuration (`pyproject.toml` or `.env`) rather than hardcoding conditionals.

## 2. Advanced Job Types & Generic Execution

The `batchserver` (`src/remotebatch/server.py`) currently specifically looks for and executes the `"povray"` job type by explicitly invoking `/usr/bin/povray`. Future iterations should introduce:

- A generic execution runner where the job metadata can define the execution command or container image.
- A registry mapping `job.type` to specific runner classes so that developers can easily extend the server to process new types of work (e.g., video rendering, data processing) without modifying the core daemon.

## 3. Web-based Dashboard (FastAPI / HTMX)

The current batch manager relies on PyQt6 for a desktop GUI. As per the modernization guidelines, migrating complex desktop or single-page apps to **FastAPI** with `htmx` and Jinja2 is recommended. A web-based dashboard would allow multiple users to monitor the S3 queue status remotely without installing the desktop client.

## 4. Enhanced Server Concurrency

The `batchserver` daemon processes jobs sequentially in a polling loop (`time.sleep(120)`). Future features should include:

- `asyncio` implementation using `aiobotocore` for non-blocking queue polling.
- Multiprocessing or multithreading support so the server can process multiple jobs concurrently.

## 5. Job Dependency Graph (DAG)

The `Job` class has a `next_job` attribute and a `step` variable, implying jobs can be chained. Implementing a full Directed Acyclic Graph (DAG) resolution in the queue manager would allow users to submit complex pipelines where jobs automatically trigger downstream tasks upon completion.

## 6. Authentication and Authorization

If the system expands beyond local user AWS credentials, implementing secure identity verification (e.g., OIDC) for the clients submitting and retrieving jobs will be necessary, particularly if a web dashboard is implemented.
