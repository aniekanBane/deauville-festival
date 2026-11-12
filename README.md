# Deauville Festival du Rire

Python application for managing the Deauville Festival du Rire 2027 programme.
It provides:

- a domain model for venues, artists, and solo, lineup, and workshop
  performances;
- SQLite storage shared by the CLI and web application;
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
[data/festival.db](data/festival.db) (seeded initially from [data/festival.json](data/festival.json)):

```bash
# Display festival information
uv run deauville

# Launch interactive terminal UI (using pick)
uv run deauville interactive

# List venues and their capacities
uv run deauville venues

# Display programme (optionally filtered by day and/or venue)
uv run deauville programme
uv run deauville programme --day 2027-06-11
uv run deauville programme --venue grand-casino
uv run deauville programme --day 2027-06-11 --venue grand-casino

# Show details for a specific performance
uv run deauville performances le-kiosque-2027-06-12-0100

# List artists and their number of performances
uv run deauville artists

# Show one artist and their performances
uv run deauville artists --focus nora-lebrun

# Add an artist interactively
uv run deauville artists --add

# Show performances currently on stage and the next three (defaults to current time)
uv run deauville now
uv run deauville now 2027-06-11T21:00

# Add a performance interactively (solo by default, or specify kind)
uv run deauville add
uv run deauville add --kind lineup
uv run deauville add --kind workshop

# Cancel a performance by ID
uv run deauville cancel le-kiosque-2027-06-12-0100
```

The CLI returns a non-zero exit code and prints a readable error when input
violates a festival rule.

### Web application

Start the development server with:

```bash
uv run deauville serve
```

Then open:

- <http://127.0.0.1:8000/> — public programme website;
- <http://127.0.0.1:8000/admin/> — administration interface;
- <http://127.0.0.1:8000/docs> — interactive Scalar API documentation.

The HTTP API is documented in [API.md](API.md). Read routes expose festival
information, venues, artists, performances, the programme, and the
performances currently on stage. Admin routes add artists, create/update/delete
performances, and register workshop participants. Successful changes are
persisted to [data/festival.db](data/festival.db) immediately.

The application uses [data/festival.db](data/festival.db) as its runtime
database. If the database is empty, the CLI seeds it once from
[data/festival.json](data/festival.json). Existing database contents are
preserved on later starts. The API receives the same `DataStorage` instance
when it is created, while each request builds a `FestivalManager` from that
storage.

## Domain rules

The model enforces rules regardless of whether a change comes from the CLI,
the API, or a test:

- names are trimmed and cannot be empty;
- artist and venue names produce normalized ASCII slugs;
- performance IDs combine the venue slug and local start time;
- performances last between 1 and 360 minutes and must belong to a festival day;
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
├── models.py           Domain entities and performance rules (Solo, Lineup, Workshop)
├── festival.py         FestivalManager and cross-entity validation
├── storage/            Storage abstraction, JSON/SQLite backends, seeding, and SQL schema
├── errors.py           Domain error types
├── helpers.py          Input normalization and date/time helpers
├── cli.py              Command-line interface and argument parsing
├── cli_interactive.py  Terminal interactive interface powered by pick
├── cli_prompts.py      CLI prompts, formatters, and display helpers
└── api/
    ├── app.py          FastAPI application and static-file mounts
    ├── routers.py      Public and admin API routes
    ├── schemas.py      Pydantic request/response schemas
    └── dependencies.py Storage and FestivalManager dependencies
```

The model classes in `models.py` validate rules intrinsic to one entity.
`FestivalManager` owns rules involving several entities, such as references,
ordering, and schedule conflicts. The API and CLI both call the manager rather
than modifying storage directly. `DataStorage` is an abstraction, so another
backend can be added without changing the domain model or HTTP routes.

The `web/public/` and `web/admin/` directories contain the static frontends.
The [tests/](tests/) directory contains model, JSON/SQLite storage, CLI,
schema, and route tests.

## Testing and Code Quality

Run the complete test suite:

```bash
uv run pytest --no-cov
```

The test configuration is in `pyproject.toml`. Storage tests are grouped in
[tests/storage/](tests/storage/), and API tests use isolated SQLite databases
seeded explicitly by their fixtures.

The repository currently contains 379 tests covering helpers, models, JSON and
SQLite storage, CLI commands, interactive navigation, request/response schemas, annotated types, and API routes,
with 100% test coverage across all core domain, CLI, storage, and API modules (94% total).

Linting, formatting, and strict type checking can also be run locally:

```bash
# Check code style and rules
uv run ruff check .

# Check code formatting
uv run ruff format --check .

# Strict type checking across application and test suite
uv run mypy src tests
```

### Pre-commit hooks

Git pre-commit hooks can be installed to automatically verify formatting, linting, and type checking before commits:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Continuous integration

GitHub Actions runs the workflow in
[.github/workflows/ci.yml](.github/workflows/ci.yml) for pushes to `main`,
pull requests, and manual dispatches. It:

1. uses the Python version in [.python-version](.python-version);
2. installs the pinned uv version and caches dependencies;
3. runs `uv sync --locked --dev`;
4. runs `uv run pytest --no-cov`;
5. verifies that `uv build` succeeds.

Documentation-only changes do not trigger CI automatically because the
workflow ignores Markdown and `docs/` changes. CI can still be started
manually from the workflow's **Run workflow** action.

## Build and deployment notes

Build the Python distributions with:

```bash
uv build
```

The build currently succeeds and produces a source distribution and wheel in
`dist/`. The wheel packages `src/deauville_festival`, but the application also
expects the repository-level `data/` and `web/` directories at runtime:

- the CLI and FastAPI both read and write `data/festival.db`;
- `data/festival.json` is available as sample/import data only;
- FastAPI serves `web/public/` and `web/admin/`.

Therefore, run the CLI and web server from the repository root after
`uv sync`. Installing only the wheel into another directory does not yet
provide the sample data or static websites. To run a built artifact, copy
`data/` and `web/` alongside the working directory and launch the application
from that directory, or package those resources as part of a future release.

If commands cannot find `data/festival.db` or the static directories, check
that:

1. Python 3.12 or newer is selected;
2. dependencies have been installed with `uv sync`;
3. the command is being run from the project root.

## Current status

Implemented:

- the complete festival domain model and validation (solo, lineup, workshop);
- JSON loading and saving for import/sample data;
- SQLite schema, persistence, and initial seeding;
- CLI programme, artist, venue, now-playing, performance details, add (solo, lineup, workshop), and cancel commands;
- interactive terminal navigation menu using `pick` (`uv run deauville interactive`);
- FastAPI read and admin routes described in [API.md](API.md) with polymorphic performance response models;
- public and admin static websites;
- automated tests for helpers, models, storage, CLI, interactive navigation, request/response schemas, annotated types, and routes (379 tests, ~93% total coverage, 100% on core domain, CLI, storage, and API modules).

The CLI and FastAPI application both use SQLite storage. The JSON file is
kept as portable sample/import data and is used only to seed an empty
database. The database is generated or provisioned separately and should not
be committed as source data.
