from fastapi import APIRouter

from app.api.v1 import auth, users, teams, team, leads, activities, inventory, pipeline, matching, reports, webhooks, integrations, gamification, notifications

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router)

# User & Team Management
api_router.include_router(users.router)
api_router.include_router(teams.router)
api_router.include_router(team.router)

# Lead Management
api_router.include_router(leads.router)
api_router.include_router(activities.router)
api_router.include_router(activities.activity_router)

# Inventory Management
api_router.include_router(inventory.router)

# Pipeline & Matching
api_router.include_router(pipeline.router)
api_router.include_router(pipeline.import_export_router)
api_router.include_router(matching.router)

# Reports & Analytics
api_router.include_router(reports.router)

# Gamification & Points
api_router.include_router(gamification.router)

# Notifications
api_router.include_router(notifications.router)

# Integrations & Webhooks
api_router.include_router(webhooks.router)
api_router.include_router(integrations.router)
