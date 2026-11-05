from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import add_scalar_reference

from deauville_festival import errors
from deauville_festival.api.router import router
from deauville_festival.storage import DataStorage


def festival_exception_handler(_: Request, exc: errors.FestivalError) -> JSONResponse:
    """Handles FestivalError exceptions and returns an appropriate JSON response."""
    match exc:
        case errors.NotFoundError():
            status_code = 404
        case errors.ConflictError():
            status_code = 409
        case errors.InvalidError():
            status_code = 422
        case _:
            status_code = 500

    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def create_app(storage: DataStorage) -> FastAPI:
    """Creates and returns the FastAPI application."""

    app = FastAPI(
        title="Deauville Festival API",
        docs_url=None,
        redoc_url=None,
    )

    app.dependency_overrides[DataStorage] = lambda: storage
    app.exception_handlers[errors.FestivalError] = festival_exception_handler

    add_scalar_reference(app, route="/docs")
    app.include_router(router)

    app.mount("/admin", StaticFiles(directory="web/admin", html=True))
    app.mount("/", StaticFiles(directory="web/public", html=True))

    return app


def run_server(storage: DataStorage) -> None:  # pragma: no cover
    """Runs the FastAPI server."""

    import uvicorn

    app = create_app(storage)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    from pathlib import Path

    from deauville_festival.storage import SQLiteStorage, seed_database

    storage = SQLiteStorage(Path("data/festival.db"))
    seed_database(storage)

    run_server(storage)
