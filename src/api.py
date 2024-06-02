import logging, pprint
from fastapi import Request, HTTPException, status, FastAPI
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pathlib import Path
from .config import AppConfig

logger = logging.getLogger(__name__)

config = AppConfig.from_env()
logger.info(f"Worker loaded configuration:\n{pprint.pformat(config.model_dump())}")

parent_dir = Path(__file__).parent
static_dir = parent_dir / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(
    directory=parent_dir / "templates"
)

@app.get("/")
async def home(request: Request):
	return templates.TemplateResponse(request, "home.html.j2")

@app.get("/favicon.ico")
async def favicon():
	return FileResponse(
		static_dir / "favicon.png",
		media_type="image/x-icon"
	)

@app.get("/analyse")
async def stats(request: Request, username: str):
	return templates.TemplateResponse(
		request,
		"analyse.html.j2",
		{
			"username": username
		}
	)

@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_error(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request,
        "error.html.j2",
        {
            "message": f"Resource not found: {request.url.path}",
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )
