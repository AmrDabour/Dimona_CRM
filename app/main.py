import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.router import api_router
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


async def _weekly_compliance_loop() -> None:
    """Background loop: every 6 hours, check if it's Sunday and run compliance."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.permissions import UserRole
    from app.services.gamification_service import GamificationService

    while True:
        await asyncio.sleep(6 * 3600)
        now = datetime.now(timezone.utc)
        if now.weekday() != 6:  # Sunday == 6
            continue
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(User).where(
                        User.is_deleted.is_(False),
                        User.is_active.is_(True),
                        User.role.in_([UserRole.AGENT, UserRole.MANAGER]),
                    )
                )
                agents = result.scalars().all()
                svc = GamificationService(db)
                awarded = 0
                for agent in agents:
                    txn = await svc.check_weekly_compliance(agent.id)
                    if txn:
                        awarded += 1
                await db.commit()
                logger.info("Weekly compliance: checked=%d, awarded=%d", len(agents), awarded)
        except Exception:
            logger.exception("Weekly compliance check failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    compliance_task = asyncio.create_task(_weekly_compliance_loop())
    yield
    compliance_task.cancel()
    await redis_client.disconnect()


app = FastAPI(
    title=settings.app_name,
    description="Real Estate CRM for Dimora Marketing & Brokerage Agency",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}
