from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from scalar_fastapi import add_scalar_reference

from deauville_festival import config, errors
from deauville_festival.api.routers import admin_router, public_router
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

    app.exception_handlers[errors.FestivalError] = festival_exception_handler
    app.state.storage = storage

    app.include_router(admin_router)
    app.include_router(public_router)
    add_scalar_reference(app, route="/docs")

    app.frontend("/admin", directory="web/admin")
    app.frontend("/", directory="web/public")

    return app


def get_app() -> FastAPI:
    from deauville_festival.storage import SQLiteStorage, seed_database

    storage = SQLiteStorage(config.DATA_DIR / "festival.db")
    seed_database(storage)

    return create_app(storage)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(get_app(), host="0.0.0.0")  # noqa: S104
