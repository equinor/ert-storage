import json
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import Response, RedirectResponse

from ert_storage.endpoints import router

from sqlalchemy.orm.exc import NoResultFound


class JSONResponse(Response):
    """A replacement for Starlette's JSONResponse that permits NaNs."""

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


app = FastAPI(
    title="ERT Storage API",
    version="0.1.2",
    debug=True,
    default_response_class=JSONResponse,
)


@app.on_event("startup")
async def initialize_database() -> None:
    from ert_storage.database import engine, IS_SQLITE
    from ert_storage.database_schema import Base

    if IS_SQLITE:
        # Our SQLite backend doesn't support migrations, so create the database on the fly.
        Base.metadata.create_all(bind=engine)


@app.exception_handler(NoResultFound)
async def sqlalchemy_exception_handler(
    request: Request, exc: NoResultFound
) -> JSONResponse:
    """Automatically catch and convert an SQLAlchemy NoResultFound exception (when
    using `.one()`, for example) to an HTTP 404 message
    """
    return JSONResponse(
        {"detail": "Item not found"}, status_code=status.HTTP_404_NOT_FOUND
    )


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/healthcheck")
async def healthcheck() -> str:
    return "ALL OK!"


app.include_router(router)
