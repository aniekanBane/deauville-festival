import contextlib
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import add_scalar_reference

from deauville_festival import errors
from deauville_festival.api import dependencies
from deauville_festival.api.router import router
from deauville_festival.storage import JSONFileStorage, SQLiteStorage


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    database = dependencies.get_storage()
    if isinstance(database, SQLiteStorage) and not database.is_initialized():
        source = dependencies.DATA_PATH.with_name("festival.json")
        database.save(JSONFileStorage(source).load())
    yield


app = FastAPI(
    title="Deauville Festival API",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.exception_handler(errors.FestivalError)
async def festival_exception_handler(
    _: Request, exc: errors.FestivalError
) -> JSONResponse:
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


add_scalar_reference(app, route="/docs")

app.include_router(router)

app.mount("/admin", StaticFiles(directory="web/admin", html=True))
app.mount("/", StaticFiles(directory="web/public", html=True))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
