import os
import sys
import json
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import Response

from ert_storage import json_schema as js
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
async def root() -> dict:
    return {}


app.include_router(router)
