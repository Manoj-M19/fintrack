import logging
from collections.abc import Callable

from fastapi import Request, Response,status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("fintrack.errors")

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Catches anu unhandled exception that escapes route handlers.
    Returns a structured JSON error instead of a raw 500 traceback.
    """
    async def dispatch(self,request:Request,call_next:Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state,"request_id","unknown")
            logger.exception(
                "unhandled exception",
                extra={"request_id":request_id,"path":request.url.path},
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail":"An unexpected error occurred.Please try again later.",
                    "request_id":request_id,
                },
            )