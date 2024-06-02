import logging, pprint, httpx
import polars as pl
from fastapi import Request, HTTPException, status, FastAPI
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pathlib import Path
from .config import AppConfig
from .user_list import UserList
from .actions import get_user_animes

logger = logging.getLogger(__name__)

config = AppConfig.from_env()
logger.info(f"Worker loaded configuration:\n{pprint.pformat(config.model_dump())}")

data = Path('data')
anime_db_path = data / 'anime_db.parquet'
# anime_db_path = data / 'anime_db.franchise.parquet'
manga_db_path = data / 'manga_db.parquet'
character_db_path = data / 'character_db.parquet'
people_db_path = data / 'people_db.parquet'

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
	async with httpx.AsyncClient() as client:
		user_list = await UserList.from_user_name(client, username)
	user_animes: pl.DataFrame = get_user_animes(user_list, anime_db_path)
	return templates.TemplateResponse(
		request,
		"analyse.html.j2",
		{
			"username": username,
			"nb_animes": user_animes.height,
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
