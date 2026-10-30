from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import add_scalar_reference

from deauville_festival import errors
from deauville_festival.api.router import router

app = FastAPI(
    title="Deauville Festival API",
    docs_url=None,
    redoc_url=None,
)


@app.exception_handler(errors.FestivalError)
async def festival_exception_handler(
    request: Request, exc: errors.FestivalError
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
