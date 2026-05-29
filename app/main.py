import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.middleware.gzip import GZipMiddleware

from .config import settings
from .database import Base, check_database, engine
from .middleware.security import AuthRateLimitMiddleware, SecurityHeadersMiddleware
from .migrate import run_migrations
from .openapi_tags import OPENAPI_TAGS
from .routers import articles, campus, members, pages, points, projects, uploads
from .routers.auth_router import router as auth_router
from .startup_checks import configure_logging, run_startup_checks

logger = logging.getLogger("sailor")


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    run_startup_checks()
    application.openapi_schema = None
    run_migrations()
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    docs = "/docs" if settings.docs_enabled else None
    application = FastAPI(
        title="sailor 工作室 API",
        version="1.2.0",
        lifespan=lifespan,
        description="工作室网站后端：成员、项目、航海日志、积分、文件上传。",
        openapi_tags=OPENAPI_TAGS,
        docs_url=docs,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    if settings.allowed_host_list:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)

    application.add_middleware(GZipMiddleware, minimum_size=500)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(AuthRateLimitMiddleware, max_per_minute=settings.auth_rate_limit_per_minute)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    uploads_path = Path(settings.upload_dir)
    uploads_path.mkdir(parents=True, exist_ok=True)

    class SafeStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope) -> Response:
            response = await super().get_response(path, scope)
            if path.lower().endswith(".svg"):
                response.headers["Content-Disposition"] = "attachment"
            return response

    application.mount("/uploads", SafeStaticFiles(directory=str(uploads_path.resolve())), name="uploads")

    application.include_router(members.router)
    application.include_router(projects.router)
    application.include_router(articles.router)
    application.include_router(pages.router)
    application.include_router(campus.router)
    application.include_router(auth_router)
    application.include_router(members.member)
    application.include_router(articles.member)
    application.include_router(points.router)
    application.include_router(members.admin)
    application.include_router(projects.admin)
    application.include_router(articles.admin)
    application.include_router(pages.admin)
    application.include_router(points.admin)
    application.include_router(uploads.router)

    @application.get("/health", summary="健康检查")
    def health():
        check_database()
        return {"status": "ok"}

    @application.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        if settings.is_production:
            return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return application


app = create_app()
