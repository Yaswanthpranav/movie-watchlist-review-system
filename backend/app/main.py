"""CineTrack FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.exceptions import translate_integrity_error
from app.routers import auth, genres, languages, movies, platforms, reviews, watchlists
from app.schemas import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run no startup schema creation, seeding, or queries against live Supabase."""
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CineTrack movie watchlist and community review platform backend API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_error_handler(
    _request: Request, exc: IntegrityError
) -> JSONResponse:
    """Global fallback converting uncaught SQLAlchemy IntegrityError to HTTP 409."""
    http_exc = translate_integrity_error(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Verify API availability and live database connectivity."""
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="connected")


app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(genres.router)
app.include_router(languages.router)
app.include_router(platforms.router)
app.include_router(watchlists.router)
app.include_router(reviews.router)
