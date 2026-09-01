from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api import upload, cases
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Starting up FastAPI SIH Backend...")
    async with engine.begin() as conn:
        # Create all tables (in MVP we can skip alembic for quick iterations initially, or use it later)
        await conn.run_sync(Base.metadata.create_all)

app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=f"{settings.API_V1_STR}/cases")

@app.get("/")
def root():
    return {"message": "SIH Memory Forensics API is running"}
