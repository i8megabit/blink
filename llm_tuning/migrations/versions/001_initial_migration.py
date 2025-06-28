"""Initial migration for LLM Tuning microservice

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_models table
    op.create_table('llm_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, default=True),
        sa.Column('status', sa.Enum('ready', 'tuning', 'failed', 'offline', name='modelstatus'), nullable=False, default='ready'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create model_routes table
    op.create_table('model_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('strategy', sa.Enum('round_robin', 'load_balanced', 'performance_based', 'complexity_based', 'keyword_based', name='routestrategy'), nullable=False),
        sa.Column('request_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('complexity_threshold', sa.Float(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['model_id'], ['llm_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create tuning_sessions table
    op.create_table('tuning_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('strategy', sa.Enum('fine_tuning', 'prompt_tuning', 'adapter_tuning', 'lora', 'qlora', name='tuningstrategy'), nullable=False),
        sa.Column('training_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('target_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('ready', 'tuning', 'failed', 'offline', name='modelstatus'), nullable=False, default='ready'),
        sa.Column('progress', sa.Float(), nullable=False, default=0.0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['model_id'], ['llm_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('tokens_generated', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('cpu_usage', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['model_id'], ['llm_models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['model_routes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create rag_documents table
    op.create_table('rag_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create api_logs table
    op.create_table('api_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('request_content', sa.Text(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['model_id'], ['llm_models.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['route_id'], ['model_routes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better performance
    op.create_index('idx_llm_models_name', 'llm_models', ['name'])
    op.create_index('idx_llm_models_status', 'llm_models', ['status'])
    op.create_index('idx_model_routes_model_id', 'model_routes', ['model_id'])
    op.create_index('idx_model_routes_active', 'model_routes', ['is_active'])
    op.create_index('idx_tuning_sessions_model_id', 'tuning_sessions', ['model_id'])
    op.create_index('idx_tuning_sessions_status', 'tuning_sessions', ['status'])
    op.create_index('idx_performance_metrics_model_id', 'performance_metrics', ['model_id'])
    op.create_index('idx_performance_metrics_timestamp', 'performance_metrics', ['timestamp'])
    op.create_index('idx_rag_documents_title', 'rag_documents', ['title'])
    op.create_index('idx_api_logs_timestamp', 'api_logs', ['timestamp'])
    op.create_index('idx_api_logs_model_id', 'api_logs', ['model_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_api_logs_model_id', table_name='api_logs')
    op.drop_index('idx_api_logs_timestamp', table_name='api_logs')
    op.drop_index('idx_rag_documents_title', table_name='rag_documents')
    op.drop_index('idx_performance_metrics_timestamp', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_model_id', table_name='performance_metrics')
    op.drop_index('idx_tuning_sessions_status', table_name='tuning_sessions')
    op.drop_index('idx_tuning_sessions_model_id', table_name='tuning_sessions')
    op.drop_index('idx_model_routes_active', table_name='model_routes')
    op.drop_index('idx_model_routes_model_id', table_name='model_routes')
    op.drop_index('idx_llm_models_status', table_name='llm_models')
    op.drop_index('idx_llm_models_name', table_name='llm_models')

    # Drop tables
    op.drop_table('api_logs')
    op.drop_table('rag_documents')
    op.drop_table('performance_metrics')
    op.drop_table('tuning_sessions')
    op.drop_table('model_routes')
    op.drop_table('llm_models')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS modelstatus')
    op.execute('DROP TYPE IF EXISTS routestrategy')
    op.execute('DROP TYPE IF EXISTS tuningstrategy') 