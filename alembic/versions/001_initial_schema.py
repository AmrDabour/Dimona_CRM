"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'manager', 'agent')")
    op.execute("CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'viewing', 'negotiation', 'won', 'lost')")
    op.execute("CREATE TYPE property_type AS ENUM ('apartment', 'villa', 'office', 'land', 'duplex', 'penthouse')")
    op.execute("CREATE TYPE unit_status AS ENUM ('available', 'reserved', 'sold')")
    op.execute("CREATE TYPE finishing_type AS ENUM ('finished', 'semi_finished', 'core_shell')")
    op.execute("CREATE TYPE activity_type AS ENUM ('call', 'whatsapp', 'meeting', 'note', 'email', 'status_change')")
    op.execute("CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'export', 'import', 'login', 'logout')")

    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'manager', 'agent', name='user_role', create_type=False), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Add foreign key from teams to users for manager
    op.create_foreign_key('fk_teams_manager', 'teams', 'users', ['manager_id'], ['id'], ondelete='SET NULL')

    # Lead sources table
    op.create_table(
        'lead_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=True),
        sa.Column('campaign_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('whatsapp_number', sa.String(20), nullable=True),
        sa.Column('status', postgresql.ENUM('new', 'contacted', 'viewing', 'negotiation', 'won', 'lost', name='lead_status', create_type=False), nullable=False, index=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lead_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Lead requirements table
    op.create_table(
        'lead_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('budget_min', sa.Numeric(14, 2), nullable=True),
        sa.Column('budget_max', sa.Numeric(14, 2), nullable=True),
        sa.Column('preferred_locations', postgresql.JSONB(), nullable=True),
        sa.Column('min_bedrooms', sa.Integer(), nullable=True),
        sa.Column('min_area_sqm', sa.Numeric(10, 2), nullable=True),
        sa.Column('property_type', postgresql.ENUM('apartment', 'villa', 'office', 'land', 'duplex', 'penthouse', name='property_type', create_type=False), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Activities table
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', postgresql.ENUM('call', 'whatsapp', 'meeting', 'note', 'email', 'status_change', name='activity_type', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('call_recording_url', sa.String(500), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), default=False, nullable=False),
        sa.Column('google_calendar_event_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Pipeline history table
    op.create_table(
        'pipeline_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_status', postgresql.ENUM('new', 'contacted', 'viewing', 'negotiation', 'won', 'lost', name='lead_status', create_type=False), nullable=True),
        sa.Column('to_status', postgresql.ENUM('new', 'contacted', 'viewing', 'negotiation', 'won', 'lost', name='lead_status', create_type=False), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Developers table
    op.create_table(
        'developers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('developer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location', sa.String(255), nullable=True, index=True),
        sa.Column('city', sa.String(100), nullable=True, index=True),
        sa.Column('lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('lng', sa.Numeric(11, 8), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brochure_url', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Units table
    op.create_table(
        'units',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('unit_number', sa.String(50), nullable=False),
        sa.Column('property_type', postgresql.ENUM('apartment', 'villa', 'office', 'land', 'duplex', 'penthouse', name='property_type', create_type=False), nullable=False),
        sa.Column('price', sa.Numeric(14, 2), nullable=False, index=True),
        sa.Column('area_sqm', sa.Numeric(10, 2), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=False, index=True),
        sa.Column('bathrooms', sa.Integer(), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=True),
        sa.Column('finishing', postgresql.ENUM('finished', 'semi_finished', 'core_shell', name='finishing_type', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('available', 'reserved', 'sold', name='unit_status', create_type=False), nullable=False, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('specs', postgresql.JSONB(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Unit images table
    op.create_table(
        'unit_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Lead property matches table
    op.create_table(
        'lead_property_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('relevance_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('is_suggested', sa.Boolean(), default=False, nullable=False),
        sa.Column('matched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', postgresql.ENUM('create', 'update', 'delete', 'export', 'import', 'login', 'logout', name='audit_action', create_type=False), nullable=False),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('lead_property_matches')
    op.drop_table('unit_images')
    op.drop_table('units')
    op.drop_table('projects')
    op.drop_table('developers')
    op.drop_table('pipeline_history')
    op.drop_table('activities')
    op.drop_table('lead_requirements')
    op.drop_table('leads')
    op.drop_table('lead_sources')
    op.drop_constraint('fk_teams_manager', 'teams', type_='foreignkey')
    op.drop_table('users')
    op.drop_table('teams')

    # Drop enum types
    op.execute("DROP TYPE audit_action")
    op.execute("DROP TYPE activity_type")
    op.execute("DROP TYPE finishing_type")
    op.execute("DROP TYPE unit_status")
    op.execute("DROP TYPE property_type")
    op.execute("DROP TYPE lead_status")
    op.execute("DROP TYPE user_role")
