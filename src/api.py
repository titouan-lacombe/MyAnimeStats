import logging, pprint
from fastapi import APIRouter
from .config import AppConfig

logger = logging.getLogger(__name__)

config = AppConfig.from_env()
logger.info(f"Worker loaded configuration:\n{pprint.pformat(config.model_dump())}")

api = APIRouter()

# --- Bucket operations ---
# https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html
# https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListMultipartUploads.html
@api.get("/")
async def home():
	return {"message": "Hello, world!"}
