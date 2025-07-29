"""Add permission and security monitoring tables

Revision ID: 002
Revises: 001
Create Date: 2024-07-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.Enum('USER', 'ROLE', 'PERMISSION', 'REPORT', 'SYSTEM', 'AUDIT', 'DATA', name='resourcetype'), nullable=False),
        sa.Column('operation_type', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'EXECUTE', 'MANAGE', name='operationtype'), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=False)
    op.create_index(op.f('ix_permissions_resource_type'), 'permissions', ['resource_type'], unique=False)
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_code'), 'roles', ['code'], unique=True)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)
    
    # Create permission_groups table
    op.create_table('permission_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_groups_name'), 'permission_groups', ['name'], unique=True)
    
    # Create role_permissions association table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create user_permissions association table
    op.create_table('user_permissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'permission_id')
    )
    
    # Create resource_permissions table
    op.create_table('resource_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.Enum('USER', 'ROLE', 'PERMISSION', 'REPORT', 'SYSTEM', 'AUDIT', 'DATA', name='resourcetype'), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('permission_level', sa.Enum('OWNER', 'ADMIN', 'WRITE', 'READ', name='permissionlevel'), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_permissions_resource_type'), 'resource_permissions', ['resource_type'], unique=False)
    op.create_index(op.f('ix_resource_permissions_user_id'), 'resource_permissions', ['user_id'], unique=False)
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_url', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_ip_address'), 'audit_logs', ['ip_address'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_status'), 'audit_logs', ['status'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    # Create security_events table
    op.create_table('security_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum('BRUTE_FORCE', 'SUSPICIOUS_LOGIN', 'UNAUTHORIZED_ACCESS', 'PRIVILEGE_ESCALATION', 'DATA_BREACH', 'MALWARE_DETECTION', 'INSIDER_THREAT', 'API_ABUSE', 'SQL_INJECTION', 'XSS_ATTACK', 'SYSTEM_ANOMALY', name='securityeventtype'), nullable=False),
        sa.Column('level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='securityeventlevel'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_ip', sa.String(length=45), nullable=True),
        sa.Column('source_port', sa.Integer(), nullable=True),
        sa.Column('source_country', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('request_url', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('detection_method', sa.String(length=100), nullable=True),
        sa.Column('detection_rule', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('severity_score', sa.Integer(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_events_created_at'), 'security_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_is_resolved'), 'security_events', ['is_resolved'], unique=False)
    op.create_index(op.f('ix_security_events_level'), 'security_events', ['level'], unique=False)
    op.create_index(op.f('ix_security_events_source_ip'), 'security_events', ['source_ip'], unique=False)
    op.create_index(op.f('ix_security_events_user_id'), 'security_events', ['user_id'], unique=False)
    
    # Add new columns to users table
    op.add_column('users', sa.Column('primary_role_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_primary_role', 'users', 'roles', ['primary_role_id'], ['id'])
    
    # Create indexes for better performance
    op.create_index('ix_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_logs_created_status', 'audit_logs', ['created_at', 'status'])
    op.create_index('ix_security_events_type_level', 'security_events', ['event_type', 'level'])
    op.create_index('ix_security_events_resolved_created', 'security_events', ['is_resolved', 'created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_security_events_resolved_created', table_name='security_events')
    op.drop_index('ix_security_events_type_level', table_name='security_events')
    op.drop_index('ix_audit_logs_created_status', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_action', table_name='audit_logs')
    
    # Drop foreign key and column from users table
    op.drop_constraint('fk_users_primary_role', 'users', type_='foreignkey')
    op.drop_column('users', 'primary_role_id')
    
    # Drop security_events table
    op.drop_index(op.f('ix_security_events_user_id'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_source_ip'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_level'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_is_resolved'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_type'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_created_at'), table_name='security_events')
    op.drop_table('security_events')
    
    # Drop audit_logs table
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_status'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_ip_address'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    # Drop resource_permissions table
    op.drop_index(op.f('ix_resource_permissions_user_id'), table_name='resource_permissions')
    op.drop_index(op.f('ix_resource_permissions_resource_type'), table_name='resource_permissions')
    op.drop_table('resource_permissions')
    
    # Drop association tables
    op.drop_table('user_permissions')
    op.drop_table('role_permissions')
    
    # Drop permission_groups table
    op.drop_index(op.f('ix_permission_groups_name'), table_name='permission_groups')
    op.drop_table('permission_groups')
    
    # Drop roles table
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_code'), table_name='roles')
    op.drop_table('roles')
    
    # Drop permissions table
    op.drop_index(op.f('ix_permissions_resource_type'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_table('permissions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS permissionlevel')
    op.execute('DROP TYPE IF EXISTS securityeventlevel')
    op.execute('DROP TYPE IF EXISTS securityeventtype')
    op.execute('DROP TYPE IF EXISTS operationtype')
    op.execute('DROP TYPE IF EXISTS resourcetype')