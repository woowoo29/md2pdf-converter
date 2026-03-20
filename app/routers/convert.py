import asyncio
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from app.services import markdown_service, pdf_service

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

router = APIRouter()


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/convert")
async def convert(
    file: UploadFile = File(...),
    theme: str = Form(default="default"),
):
    if not file.filename or not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are supported.")

    content = await file.read()
    try:
        md_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    html_body = markdown_service.render(md_text)

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, pdf_service.generate, html_body, theme
    )

    original_name = Path(file.filename).stem
    filename = f"{original_name}.pdf"
    filename_encoded = quote(filename, safe="")

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"},
    )
