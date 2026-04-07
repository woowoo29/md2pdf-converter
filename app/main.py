from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import runtime_paths


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime_paths.ensure_runtime_directories()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="md → pdf", lifespan=lifespan)
    application.mount("/static", StaticFiles(directory=runtime_paths.static_dir()), name="static")
    application.mount("/themes", StaticFiles(directory=runtime_paths.themes_dir()), name="themes")

    from app.routers import convert  # noqa: E402

    application.include_router(convert.router)
    return application


app = create_app()
