from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.matches import router as matches_router
from app.api.v1.players import router as players_router
from app.api.v1.scorecards import router as scorecards_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.teams import router as teams_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(teams_router)
api_router.include_router(players_router)
api_router.include_router(matches_router)
api_router.include_router(scoring_router)
api_router.include_router(scorecards_router)
api_router.include_router(analysis_router)
api_router.include_router(chat_router)
api_router.include_router(analytics_router)
