# RemoteBatch

A modern Python 3.12+ application for delegating work from one machine to another (originally for Povray renders).

## Installation

1. Clone the repository.
1. Create a virtual environment: `python -m venv env`
1. Activate it: `source env/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`

## Usage

### GUI

Run the main application:

```bash
python RemoteBatch.py
```

### Manager

Run the manager:

```bash
python BatchManager.py
```

## Development

### Running Tests

```bash
pytest
```

### Linting & Type Checking

```bash
ruff check .
pyright
```
