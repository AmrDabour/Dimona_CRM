import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus
from app.models.lead_source import LeadSource
from app.models.user import User
from app.core.permissions import UserRole
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_lead_as_admin(client: AsyncClient, test_admin, admin_token, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/leads",
        json={
            "full_name": "John Doe",
            "phone": "+201234567890",
            "email": "john@example.com",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert data["phone"] == "+201234567890"
    assert data["status"] == "new"


@pytest.mark.asyncio
async def test_create_lead_as_agent_auto_assign(
    client: AsyncClient,
    test_agent: User,
    agent_token: str,
    db_session: AsyncSession,
):
    response = await client.post(
        "/api/v1/leads",
        json={
            "full_name": "Jane Doe",
            "phone": "+201234567891",
        },
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to"] == str(test_agent.id)


@pytest.mark.asyncio
async def test_list_leads_rbac_agent(
    client: AsyncClient,
    test_agent: User,
    agent_token: str,
    db_session: AsyncSession,
):
    lead1 = Lead(
        id=uuid4(),
        full_name="Lead 1",
        phone="+201111111111",
        assigned_to=test_agent.id,
        status=LeadStatus.NEW,
    )
    other_agent = User(
        id=uuid4(),
        email="other_agent@test.com",
        full_name="Other Agent",
        hashed_password="fakehash",
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(other_agent)
    await db_session.flush()

    lead2 = Lead(
        id=uuid4(),
        full_name="Lead 2",
        phone="+202222222222",
        assigned_to=other_agent.id,
        status=LeadStatus.NEW,
    )
    db_session.add_all([lead1, lead2])
    await db_session.commit()

    response = await client.get(
        "/api/v1/leads",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Lead 1"


@pytest.mark.asyncio
async def test_update_lead_status(
    client: AsyncClient,
    test_admin,
    admin_token: str,
    db_session: AsyncSession,
):
    lead = Lead(
        id=uuid4(),
        full_name="Test Lead",
        phone="+203333333333",
        status=LeadStatus.NEW,
    )
    db_session.add(lead)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/leads/{lead.id}/status",
        json={
            "status": "contacted",
            "note": "First contact made",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "contacted"


@pytest.mark.asyncio
async def test_update_lead_status_lost_requires_reason(
    client: AsyncClient,
    test_admin,
    admin_token: str,
    db_session: AsyncSession,
):
    lead = Lead(
        id=uuid4(),
        full_name="Test Lead",
        phone="+204444444444",
        status=LeadStatus.NEGOTIATION,
    )
    db_session.add(lead)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/leads/{lead.id}/status",
        json={
            "status": "lost",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400

    response = await client.patch(
        f"/api/v1/leads/{lead.id}/status",
        json={
            "status": "lost",
            "lost_reason": "Budget constraints",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "lost"
    assert data["lost_reason"] == "Budget constraints"


@pytest.mark.asyncio
async def test_agent_cannot_delete_lead(
    client: AsyncClient,
    test_agent: User,
    agent_token: str,
    db_session: AsyncSession,
):
    lead = Lead(
        id=uuid4(),
        full_name="Test Lead",
        phone="+205555555555",
        assigned_to=test_agent.id,
        status=LeadStatus.NEW,
    )
    db_session.add(lead)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/leads/{lead.id}",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 401 or response.status_code == 403
