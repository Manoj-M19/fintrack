from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.errors import ErrorHandlerMiddleware
from app.middleware.logging import RequestLoggingMiddleware, configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(debug=settings.DEBUG)
    from app.core.database import engine
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Finance & Expense Tracker REST API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()