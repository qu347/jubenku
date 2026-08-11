from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match

from app.api.router import api_router
from app.core.config import Settings, settings
from app.core.exceptions import error_payload, register_exception_handlers
from app.core.logging import configure_logging, get_app_logger
from app.core.runtime import prepare_runtime_directories, validate_frontend_dist


def _safe_dist_file(dist: Path, requested_path: str) -> Path | None:
    candidate = (dist / requested_path).resolve()
    try:
        candidate.relative_to(dist)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _mount_frontend(application: FastAPI, config: Settings, dist: Path) -> None:
    assets = dist / "assets"
    if assets.is_dir():
        application.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    api_prefix = config.api_prefix.rstrip("/") or "/api"
    known_api_routes = tuple(
        route
        for route in application.router.routes
        if str(getattr(route, "path", "")).startswith(api_prefix)
    )

    async def api_not_found(request: Request) -> JSONResponse:
        allowed_methods: set[str] = set()
        for route in known_api_routes:
            match, _ = route.matches(request.scope)
            if match == Match.PARTIAL:
                allowed_methods.update(getattr(route, "methods", set()) or set())
        if allowed_methods:
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content=error_payload("请求方法不允许", "method_not_allowed"),
                headers={"Allow": ", ".join(sorted(allowed_methods))},
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_payload("接口不存在", "api_not_found"),
        )

    # These routes are registered after the real API router and before the SPA
    # fallback. Therefore an unknown /api path can never receive index.html.
    application.add_api_route(
        api_prefix,
        api_not_found,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    application.add_api_route(
        f"{api_prefix}/{{api_path:path}}",
        api_not_found,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )

    async def serve_spa(request: Request, frontend_path: str = "") -> Response:
        del request
        requested_file = _safe_dist_file(dist, frontend_path) if frontend_path else None
        if requested_file is not None:
            if requested_file == dist / "index.html":
                return FileResponse(
                    requested_file,
                    media_type="text/html",
                    headers={"Cache-Control": "no-store, max-age=0"},
                )
            return FileResponse(requested_file, headers={"Cache-Control": "public, max-age=3600"})
        return FileResponse(
            dist / "index.html",
            media_type="text/html",
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    application.add_api_route("/", serve_spa, methods=["GET", "HEAD"], include_in_schema=False)
    application.add_api_route(
        "/{frontend_path:path}",
        serve_spa,
        methods=["GET", "HEAD"],
        include_in_schema=False,
    )


def create_application(config: Settings | None = None) -> FastAPI:
    runtime_config = config or settings
    if runtime_config.is_production:
        prepare_runtime_directories(runtime_config)
    logger = configure_logging(runtime_config)

    validated_frontend_dist: Path | None = None
    if runtime_config.is_production or runtime_config.serve_frontend:
        try:
            validated_frontend_dist = validate_frontend_dist(runtime_config)
        except RuntimeError:
            logger.error("frontend_dist_validation_failed")
            raise

    application = FastAPI(
        title=runtime_config.app_name,
        version=runtime_config.app_version,
        debug=runtime_config.debug and not runtime_config.is_production,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.state.settings = runtime_config
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_config.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(api_router, prefix=runtime_config.api_prefix)

    request_logger = get_app_logger("access")

    @application.middleware("http")
    async def request_logging(request: Request, call_next):  # type: ignore[no-untyped-def]
        started = perf_counter()
        response = await call_next(request)
        if request.url.path.startswith(runtime_config.api_prefix):
            request_logger.info(
                "request method=%s path=%s status=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                (perf_counter() - started) * 1000,
            )
        if request.url.path.startswith("/assets/") and response.status_code < 400:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    if runtime_config.serve_frontend and validated_frontend_dist is not None:
        _mount_frontend(application, runtime_config, validated_frontend_dist)
    return application


app = create_application()
