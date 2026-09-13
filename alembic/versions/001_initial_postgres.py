"""001_initial_postgres

Revision ID: 001_initial_postgres
Revises: 
Create Date: 2026-09-14 04:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001_initial_postgres'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 1. Buses table
    op.create_table(
        'buses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bus_id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='Active'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_buses_bus_id'), 'buses', ['bus_id'], unique=True)
    op.create_index(op.f('ix_buses_id'), 'buses', ['id'], unique=False)
    op.create_index(op.f('ix_buses_route_id'), 'buses', ['route_id'], unique=False)

    # 2. Incidents table
    incident_columns = [
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('anomaly_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, server_default='Medium'),
        sa.Column('priority_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('status', sa.String(), nullable=False, server_default='NEW'),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('first_detected_at', sa.DateTime(), nullable=False),
        sa.Column('last_detected_at', sa.DateTime(), nullable=False),
        sa.Column('confirmation_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unique_bus_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('primary_image_url', sa.String(), nullable=True),
    ]

    if is_postgres:
        incident_columns.append(
            sa.Column('geom', geoalchemy2.Geometry(geometry_type='POINT', srid=4326), nullable=True)
        )

    op.create_table('incidents', *incident_columns, sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_incidents_anomaly_type'), 'incidents', ['anomaly_type'], unique=False)
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_incident_id'), 'incidents', ['incident_id'], unique=True)
    op.create_index(op.f('ix_incidents_severity'), 'incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)

    # 3. Observations table
    obs_columns = [
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('edge_event_id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('bus_id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('speed_kmh', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
    ]
    if is_postgres:
        obs_columns.append(
            sa.Column('geom', geoalchemy2.Geometry(geometry_type='POINT', srid=4326), nullable=True)
        )

    op.create_table(
        'observations',
        *obs_columns,
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_observations_bus_id'), 'observations', ['bus_id'], unique=False)
    op.create_index(op.f('ix_observations_edge_event_id'), 'observations', ['edge_event_id'], unique=True)
    op.create_index(op.f('ix_observations_id'), 'observations', ['id'], unique=False)
    op.create_index(op.f('ix_observations_incident_id'), 'observations', ['incident_id'], unique=False)
    op.create_index(op.f('ix_observations_route_id'), 'observations', ['route_id'], unique=False)
    # Critical index requirement: ix_observations_message_id
    op.create_index(op.f('ix_observations_message_id'), 'observations', ['message_id'], unique=True)

    # 4. Status history table
    op.create_table(
        'status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(), nullable=True),
        sa.Column('to_status', sa.String(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_status_history_id'), 'status_history', ['id'], unique=False)
    op.create_index(op.f('ix_status_history_incident_id'), 'status_history', ['incident_id'], unique=False)

    # 5. Plate reads table (ANPR)
    op.create_table(
        'plate_reads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('edge_event_id', sa.String(), nullable=True),
        sa.Column('bus_id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('plate_text', sa.String(), nullable=False),
        sa.Column('plate_confidence', sa.Float(), nullable=False),
        sa.Column('ocr_confidence', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plate_reads_id'), 'plate_reads', ['id'], unique=False)
    op.create_index(op.f('ix_plate_reads_incident_id'), 'plate_reads', ['incident_id'], unique=False)
    op.create_index(op.f('ix_plate_reads_edge_event_id'), 'plate_reads', ['edge_event_id'], unique=False)
    op.create_index(op.f('ix_plate_reads_bus_id'), 'plate_reads', ['bus_id'], unique=False)
    op.create_index(op.f('ix_plate_reads_route_id'), 'plate_reads', ['route_id'], unique=False)
    op.create_index(op.f('ix_plate_reads_plate_text'), 'plate_reads', ['plate_text'], unique=False)

    # 6. Infra observations table (Traffic signs/signals)
    op.create_table(
        'infra_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sign_type', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bus_id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_infra_observations_id'), 'infra_observations', ['id'], unique=False)
    op.create_index(op.f('ix_infra_observations_sign_type'), 'infra_observations', ['sign_type'], unique=False)
    op.create_index(op.f('ix_infra_observations_bus_id'), 'infra_observations', ['bus_id'], unique=False)
    op.create_index(op.f('ix_infra_observations_route_id'), 'infra_observations', ['route_id'], unique=False)


def downgrade() -> None:
    op.drop_table('infra_observations')
    op.drop_table('plate_reads')
    op.drop_table('status_history')
    op.drop_table('observations')
    op.drop_table('incidents')
    op.drop_table('buses')
