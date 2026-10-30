# Deauville Festival du Rire

Python application for managing the Deauville Festival du Rire 2027 programme.
It provides:

- a domain model for venues, artists, and solo, lineup, and workshop
  performances;
- a JSON-backed persistence layer;
- a command-line interface for programme and festival administration;
- a FastAPI application serving the public website and admin interface;
- validation and tests for the festival's scheduling and participation rules.

The sample data in [data/festival.json](data/festival.json) describes the
10–13 June 2027 edition.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Installation

From the repository root:

```bash
uv sync
```

`uv sync` creates the virtual environment and installs the application and
development dependencies, including FastAPI and pytest.

### Troubleshooting the local installation

If the `deauville` launcher exists but reports
`ModuleNotFoundError: No module named 'deauville_festival'`, the editable
installation in `.venv` may be stale or incomplete. Rebuild the environment:

```bash
uv sync --reinstall
```

Run uv commands sequentially when repairing the environment. Concurrent uv
commands can modify the same `.venv` at the same time and temporarily leave
the package unavailable.

## Running the application

### Command line

The installed `deauville` command reads and updates
[data/festival.json](data/festival.json):

```bash
# Display festival information
uv run deauville

# List venues and their capacities
uv run deauville venues

# Display one day's programme
uv run deauville programme 2027-06-11

# List artists and their number of performances
uv run deauville artists

# Show one artist and their performances
uv run deauville artists --find nora-lebrun

# Add an artist interactively
uv run deauville artists --add

# Show performances currently on stage and the next three
uv run deauville now 2027-06-11T21:00

# Add a solo performance interactively
uv run deauville add

# Cancel a performance by ID
uv run deauville cancel le-kiosque-2027-06-12-0100
```

The CLI returns a non-zero exit code and prints a readable error when input
violates a festival rule.

### Web application

Start the development server with:

```bash
uv run uvicorn deauville_festival.api.app:app --reload
```

Then open:

- <http://127.0.0.1:8000/> — public programme website;
- <http://127.0.0.1:8000/admin/> — administration interface;
- <http://127.0.0.1:8000/docs> — interactive Scalar API documentation.

The HTTP API is documented in [API.md](API.md). Read routes expose festival
information, venues, artists, performances, the programme, and the
performances currently on stage. Admin routes add artists, create/update/delete
performances, and register workshop participants. Successful changes are
persisted to the JSON data file immediately.

## Domain rules

The model enforces rules regardless of whether a change comes from the CLI,
the API, or a test:

- names are trimmed and cannot be empty;
- artist and venue names produce normalized ASCII slugs;
- performance IDs combine the venue slug and local start time;
- performances last between 1 and 360 minutes and must belong to a festival
  day;
- a festival day runs from 06:00 until 05:59 the following day;
- venues and artists require 30 minutes between performances;
- venues, artists, and referenced performances must exist;
- solo performances have an audience age from 0 to 18;
- lineups require at least two unique acts, a distinct host, and enough time
  for the acts and transitions;
- workshops validate their teacher, capacity, and case-insensitive
  participant registration.

Invalid changes are rejected before the in-memory festival is replaced or
saved, so an unsuccessful update does not partially modify the programme.
Domain errors are converted by the API to the documented 404, 409, 422, and
500 responses.

## Project structure

```text
src/deauville_festival/
├── models.py       Domain entities and performance rules
├── festival.py     FestivalManager and cross-entity validation
├── storage.py      Storage abstraction and JSON serialization
├── errors.py       Domain error types
├── helpers.py      Input normalization and date/time helpers
├── cli.py          Command-line interface
└── api/
    ├── app.py      FastAPI application and static-file mounts
    ├── router.py   Public and admin API routes
    ├── schemas.py  Pydantic request/response schemas
    └── dependencies.py
                    JSON storage and FestivalManager dependencies
```

The model classes in `models.py` validate rules intrinsic to one entity.
`FestivalManager` owns rules involving several entities, such as references,
ordering, and schedule conflicts. The API and CLI both call the manager rather
than modifying storage directly. `DataStorage` is an abstraction, so another
backend can be added without changing the domain model or HTTP routes.

The `web/public/` and `web/admin/` directories contain the static frontends.
The [tests/](tests/) directory contains model, storage, CLI, schema, and route
tests.

## Testing

Run the complete test suite:

```bash
uv run pytest
```

The test configuration is in `pyproject.toml`; tests use an isolated copy of
the festival JSON file for API mutations.

## Build and deployment notes

Build the Python distributions with:

```bash
uv build
```

The build currently succeeds and produces a source distribution and wheel in
`dist/`. The wheel packages `src/deauville_festival`, but the application also
expects the repository-level `data/` and `web/` directories at runtime:

- the CLI reads and writes `data/festival.json`;
- FastAPI serves `web/public/` and `web/admin/`.

Therefore, run the CLI and web server from the repository root after
`uv sync`. Installing only the wheel into another directory does not yet
provide the sample data or static websites. To run a built artifact, copy
`data/` and `web/` alongside the working directory and launch the application
from that directory, or package those resources as part of a future release.

If commands cannot find `data/festival.json` or the static directories, check
that:

1. Python 3.12 or newer is selected;
2. dependencies have been installed with `uv sync`;
3. the command is being run from the project root.

## Current status

Implemented:

- the complete festival domain model and validation;
- JSON loading and saving;
- CLI programme, artist, venue, now-playing, add, and cancel commands;
- FastAPI read and admin routes described in [API.md](API.md);
- public and admin static websites;
- automated tests for helpers, models, storage, CLI, schemas, and routes.

The application currently uses JSON file storage. A database-backed storage
implementation has not been added.
