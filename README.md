# Dimora CRM

A comprehensive Real Estate CRM system for marketing and brokerage agencies. Built with FastAPI, PostgreSQL, Redis, and designed for cloud-native deployment.

## Features

### Lead Management
- Omnichannel lead capture (Facebook, Instagram, WhatsApp, Website)
- Auto-deduplication by phone/email
- Round-robin lead assignment to agents
- Full interaction logging (calls, meetings, notes, WhatsApp)

### Sales Pipeline (Kanban)
- Visual pipeline stages: New → Contacted → Viewing → Negotiation → Won/Lost
- Mandatory notes when marking leads as Lost
- Pipeline history tracking
- SLA monitoring for stuck leads

### Inventory Management
- Hierarchical structure: Developer → Project → Unit
- Rich unit details: price, area, bedrooms, bathrooms, floor, finishing
- Image gallery and PDF brochure support
- Advanced search and filtering
- Bulk import via Excel

### Smart Matching
- Automatic property matching based on lead requirements
- Weighted scoring algorithm (budget 40%, location 30%, bedrooms 15%, area 15%)
- One-click "suggest to client" action

### Role-Based Access Control (RBAC)

| Feature | Admin | Manager | Agent |
|---------|-------|---------|-------|
| View all leads | ✅ | Team only | Own only |
| Create leads | ✅ | ✅ | ✅ (auto-assign) |
| Delete leads | ✅ | ❌ | ❌ |
| Export leads | ✅ | ❌ | ❌ |
| Import leads | ✅ | ✅ | ❌ |
| Reassign leads | ✅ | Team only | ❌ |
| Manage inventory | Full | Read + Add | Read only |
| View reports | All | Team | Own |
| Manage users | ✅ | ❌ | ❌ |
| Integrations | ✅ | ❌ | ❌ |

### Integrations
- WhatsApp Business API (send/receive messages)
- Google Calendar (meeting sync)
- Facebook/Instagram Lead Ads webhooks
- Website contact form webhook

### Analytics & Reporting
- Agent performance dashboards
- Marketing ROI by source/campaign
- Conversion funnel analysis
- Personal, team, and global dashboards

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **ORM**: SQLAlchemy 2.0 (async)
- **Task Queue**: Celery
- **File Storage**: MinIO/S3
- **Auth**: JWT (access + refresh tokens)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/dimora-crm.git
cd dimora-crm

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Create initial admin user (optional)
docker-compose exec api python -c "
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.core.permissions import UserRole
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email='admin@dimora.com',
            full_name='System Admin',
            hashed_password=get_password_hash('admin123'),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print('Admin user created!')

asyncio.run(create_admin())
"
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (using Docker)
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, access the interactive API docs:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Project Structure

```
dimora-crm/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── core/            # Security, permissions, Redis
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tasks/           # Celery async tasks
│   ├── utils/           # Helpers (Excel, pagination)
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   ├── dependencies.py  # FastAPI dependencies
│   └── main.py          # App entry point
├── alembic/             # Database migrations
├── tests/               # Test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/refresh` - Refresh access token

### Leads
- `GET /api/v1/leads` - List leads (RBAC filtered)
- `POST /api/v1/leads` - Create lead
- `GET /api/v1/leads/{id}` - Get lead details
- `PATCH /api/v1/leads/{id}` - Update lead
- `DELETE /api/v1/leads/{id}` - Delete lead (Admin)
- `PATCH /api/v1/leads/{id}/status` - Change pipeline stage
- `POST /api/v1/leads/{id}/assign` - Reassign lead

### Lead Requirements & Matching
- `POST /api/v1/leads/{id}/requirements` - Set requirements
- `GET /api/v1/leads/{id}/matches` - Get matched properties

### Activities
- `GET /api/v1/leads/{id}/activities` - List activities
- `POST /api/v1/leads/{id}/activities` - Log activity

### Inventory
- `GET /api/v1/developers` - List developers
- `GET /api/v1/projects` - List projects
- `GET /api/v1/units` - Search units with filters

### Reports
- `GET /api/v1/reports/dashboard` - Get dashboard
- `GET /api/v1/reports/agent-performance/{id}` - Agent report
- `GET /api/v1/reports/marketing-roi` - Marketing ROI (Admin)

### Webhooks
- `POST /api/v1/webhooks/facebook` - Facebook Lead Ads
- `POST /api/v1/webhooks/whatsapp` - WhatsApp messages
- `POST /api/v1/webhooks/website` - Website forms

## Environment Variables

See `.env.example` for all configuration options:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Secret key for JWT tokens |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API token |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |

## Running Tests

```bash
# Create test database
createdb dimora_crm_test

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Deployment

### Kubernetes

```bash
# Build and push Docker image
docker build -t your-registry/dimora-crm:latest .
docker push your-registry/dimora-crm:latest

# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### AWS ECS

Use the provided Dockerfile with AWS ECS service. Configure environment variables through AWS Secrets Manager or Parameter Store.

## License

Proprietary - Dimora Marketing & Brokerage Agency

## Support

For issues and feature requests, contact: support@dimora.com
