from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    (BASE_DIR / "uploads").mkdir(exist_ok=True)
    (BASE_DIR / "outputs").mkdir(exist_ok=True)
    yield


app = FastAPI(title="md → pdf", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/themes", StaticFiles(directory=BASE_DIR / "app" / "themes"), name="themes")

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

from app.routers import convert  # noqa: E402
app.include_router(convert.router)
