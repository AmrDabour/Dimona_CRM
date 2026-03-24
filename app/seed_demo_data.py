"""Seed realistic demo data for local CRM testing.

This script is idempotent: running it multiple times will not duplicate
records with the same demo identifiers.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.config import settings
from app.core.permissions import UserRole
from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.activity import Activity, ActivityType
from app.models.developer import Developer
from app.models.lead import Lead, LeadStatus
from app.models.lead_source import LeadSource
from app.models.project import Project
from app.models.team import Team
from app.models.unit import FinishingType, Unit, UnitStatus
from app.models.user import User


DEMO_PASSWORD = "Demo@12345"


async def get_or_create_user(
    email: str,
    full_name: str,
    role: UserRole,
    phone: str | None = None,
    password: str = None,
) -> User:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            return existing

        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            hashed_password=get_password_hash(password or DEMO_PASSWORD),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Team + users
        admin = await get_or_create_user(
            settings.admin_email,
            "System Admin",
            UserRole.ADMIN,
            "+201000000000",
            settings.admin_password
        )
        
        manager = await get_or_create_user(
            "manager.demo@dimora.com",
            "Nadia Sales Manager",
            UserRole.MANAGER,
            "+201010000001",
        )
        agent_1 = await get_or_create_user(
            "agent1.demo@dimora.com",
            "Omar Senior Agent",
            UserRole.AGENT,
            "+201010000002",
        )
        agent_2 = await get_or_create_user(
            "agent2.demo@dimora.com",
            "Mariam Property Consultant",
            UserRole.AGENT,
            "+201010000003",
        )

        team = await db.scalar(select(Team).where(Team.name == "Demo Sales Team"))
        if not team:
            team = Team(name="Demo Sales Team", manager_id=manager.id)
            db.add(team)
            await db.flush()

        manager.team_id = team.id
        agent_1.team_id = team.id
        agent_2.team_id = team.id

        # Lead sources
        source_defs = [
            ("Facebook Ads", "Ramadan Offer", Decimal("15000")),
            ("Instagram", "Stories Campaign", Decimal("8000")),
            ("Referral", "Past Client Referral", Decimal("0")),
            ("Website", "Landing Page Form", Decimal("3000")),
            ("WhatsApp", "Direct Inquiry", Decimal("0")),
        ]
        sources: dict[str, LeadSource] = {}
        for name, campaign, cost in source_defs:
            src = await db.scalar(select(LeadSource).where(LeadSource.name == name))
            if not src:
                src = LeadSource(name=name, campaign_name=campaign, campaign_cost=cost)
                db.add(src)
                await db.flush()
            sources[name] = src

        # Developers + projects
        dev_names = [
            "Demo Developments",
            "Nile Gate Real Estate",
        ]
        devs: dict[str, Developer] = {}
        for dn in dev_names:
            d = await db.scalar(select(Developer).where(Developer.name == dn))
            if not d:
                d = Developer(name=dn, description=f"{dn} premium projects")
                db.add(d)
                await db.flush()
            devs[dn] = d

        project_defs = [
            ("Demo Heights", "New Cairo", "Cairo", dev_names[0]),
            ("Nile Vista", "Sheikh Zayed", "Giza", dev_names[1]),
            ("Marina One", "North Coast", "Matrouh", dev_names[0]),
        ]
        projects: dict[str, Project] = {}
        for name, location, city, dev_name in project_defs:
            p = await db.scalar(select(Project).where(Project.name == name))
            if not p:
                p = Project(
                    name=name,
                    location=location,
                    city=city,
                    developer_id=devs[dev_name].id,
                    description=f"{name} mixed-use compound",
                )
                db.add(p)
                await db.flush()
            projects[name] = p

        # Units
        unit_defs = [
            ("DH-A101", "Demo Heights", "apartment", 1450000, 120, 2, 2, "core_shell", "available"),
            ("DH-B202", "Demo Heights", "duplex", 2700000, 210, 4, 3, "semi_finished", "reserved"),
            ("NV-T11", "Nile Vista", "villa", 5200000, 320, 5, 4, "finished", "available"),
            ("NV-A33", "Nile Vista", "apartment", 1950000, 145, 3, 2, "finished", "sold"),
            ("MO-P9", "Marina One", "penthouse", 6100000, 280, 4, 3, "semi_finished", "available"),
            ("MO-A7", "Marina One", "apartment", 2350000, 155, 3, 2, "core_shell", "available"),
        ]

        for (
            unit_number,
            project_name,
            property_type,
            price,
            area_sqm,
            bedrooms,
            bathrooms,
            finishing,
            status,
        ) in unit_defs:
            exists = await db.scalar(select(Unit).where(Unit.unit_number == unit_number))
            if exists:
                continue
            db.add(
                Unit(
                    project_id=projects[project_name].id,
                    unit_number=unit_number,
                    property_type=property_type,  # enum values are lowercase strings
                    price=Decimal(str(price)),
                    area_sqm=Decimal(str(area_sqm)),
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    floor=1,
                    finishing=FinishingType(finishing),
                    status=UnitStatus(status),
                    notes="Demo seeded unit",
                )
            )

        # Leads + activities
        lead_defs = [
            ("Ahmed Samir", "+201200000001", "ahmed.demo@client.com", "Facebook Ads", agent_1.id, "new", "buy"),
            ("Mona Adel", "+201200000002", "mona.demo@client.com", "Instagram", agent_2.id, "contacted", "buy"),
            ("Youssef Nabil", "+201200000003", "youssef.demo@client.com", "Referral", agent_1.id, "viewing", "buy"),
            ("Sara Hany", "+201200000004", "sara.demo@client.com", "Website", agent_2.id, "negotiation", "buy"),
            ("Karim Fathy", "+201200000005", "karim.demo@client.com", "WhatsApp", agent_1.id, "won", "buy"),
            ("Dina Mahmoud", "+201200000006", "dina.demo@client.com", "Facebook Ads", agent_2.id, "lost", "buy"),
            ("Mostafa Ali", "+201200000007", "mostafa.demo@client.com", "Instagram", agent_1.id, "new", "rent"),
            ("Nada Wael", "+201200000008", "nada.demo@client.com", "Website", agent_2.id, "contacted", "rent"),
            ("Hassan Tarek", "+201200000009", "hassan.demo@client.com", "Referral", agent_1.id, "viewing", "buy"),
            ("Laila Ibrahim", "+201200000010", "laila.demo@client.com", "WhatsApp", agent_2.id, "negotiation", "buy"),
        ]

        import random
        from datetime import datetime, timedelta, timezone

        for full_name, phone, email, source_name, assigned_to, status, intent in lead_defs:
            lead = await db.scalar(select(Lead).where(Lead.phone == phone))
            if not lead:
                lead = Lead(
                    full_name=full_name,
                    phone=phone,
                    email=email,
                    whatsapp_number=phone,
                    source_id=sources[source_name].id,
                    assigned_to=assigned_to,
                    status=LeadStatus(status),
                    lost_reason="Budget mismatch" if status == "lost" else None,
                    custom_fields={"intent": intent, "preferred_area": "New Cairo"},
                )
                db.add(lead)
                await db.flush()

            # Add multiple activities if none exist for this lead.
            existing_activity = await db.scalar(
                select(Activity).where(Activity.lead_id == lead.id).limit(1)
            )
            if not existing_activity:
                now = datetime.now(timezone.utc)
                
                # 1. A completed note (history)
                db.add(
                    Activity(
                        lead_id=lead.id,
                        user_id=assigned_to,
                        type=ActivityType.NOTE,
                        description="Initial qualification call completed.",
                        is_completed=True,
                    )
                )

                # 2. A pending (future) or overdue (past) activity
                is_overdue = random.choice([True, False])
                days_offset = random.randint(1, 4)
                scheduled_date = now - timedelta(days=days_offset) if is_overdue else now + timedelta(days=days_offset)
                
                activity_type = random.choice([ActivityType.CALL, ActivityType.MEETING, ActivityType.WHATSAPP])
                
                db.add(
                    Activity(
                        lead_id=lead.id,
                        user_id=assigned_to,
                        type=activity_type,
                        description=f"Scheduled follow-up {activity_type.value}.",
                        scheduled_at=scheduled_date,
                        is_completed=False,
                    )
                )

        await db.commit()

    print("Demo data seeded successfully.")
    print("Demo users:")
    print("  admin@dimora.com / Admin@123")
    print("  manager.demo@dimora.com / Demo@12345")
    print("  agent1.demo@dimora.com / Demo@12345")
    print("  agent2.demo@dimora.com / Demo@12345")


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed())

