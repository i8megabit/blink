"""Add testing tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем enum типы
    op.execute("CREATE TYPE testtype AS ENUM ('unit', 'api', 'performance', 'seo', 'llm', 'generic')")
    op.execute("CREATE TYPE teststatus AS ENUM ('pending', 'running', 'passed', 'failed', 'error', 'cancelled')")
    op.execute("CREATE TYPE testpriority AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE testenvironment AS ENUM ('development', 'staging', 'production')")
    
    # Таблица тестов
    op.create_table('tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_type', sa.Enum('unit', 'api', 'performance', 'seo', 'llm', 'generic', name='testtype'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='testpriority'), nullable=False),
        sa.Column('environment', sa.Enum('development', 'staging', 'production', name='testenvironment'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'passed', 'failed', 'error', 'cancelled', name='teststatus'), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица выполнений тестов
    op.create_table('test_executions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('test_request', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'passed', 'failed', 'error', 'cancelled', name='teststatus'), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('results', postgresql.JSONB(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица результатов тестов
    op.create_table('test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=False),
        sa.Column('test_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('passed', 'failed', 'error', 'skipped', name='teststatus'), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['test_executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица наборов тестов
    op.create_table('test_suites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица отчетов
    op.create_table('test_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=True),
        sa.Column('execution_id', sa.String(length=36), nullable=True),
        sa.Column('summary', postgresql.JSONB(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['test_executions.id'], ),
        sa.ForeignKeyConstraint(['suite_id'], ['test_suites.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы
    op.create_index(op.f('ix_tests_user_id'), 'tests', ['user_id'], unique=False)
    op.create_index(op.f('ix_tests_test_type'), 'tests', ['test_type'], unique=False)
    op.create_index(op.f('ix_tests_status'), 'tests', ['status'], unique=False)
    op.create_index(op.f('ix_tests_priority'), 'tests', ['priority'], unique=False)
    op.create_index(op.f('ix_tests_environment'), 'tests', ['environment'], unique=False)
    op.create_index(op.f('ix_tests_created_at'), 'tests', ['created_at'], unique=False)
    
    op.create_index(op.f('ix_test_executions_user_id'), 'test_executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_test_executions_status'), 'test_executions', ['status'], unique=False)
    op.create_index(op.f('ix_test_executions_created_at'), 'test_executions', ['created_at'], unique=False)
    
    op.create_index(op.f('ix_test_results_execution_id'), 'test_results', ['execution_id'], unique=False)
    op.create_index(op.f('ix_test_results_status'), 'test_results', ['status'], unique=False)
    
    op.create_index(op.f('ix_test_suites_user_id'), 'test_suites', ['user_id'], unique=False)
    op.create_index(op.f('ix_test_reports_user_id'), 'test_reports', ['user_id'], unique=False)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index(op.f('ix_test_reports_user_id'), table_name='test_reports')
    op.drop_index(op.f('ix_test_suites_user_id'), table_name='test_suites')
    op.drop_index(op.f('ix_test_results_status'), table_name='test_results')
    op.drop_index(op.f('ix_test_results_execution_id'), table_name='test_results')
    op.drop_index(op.f('ix_test_executions_created_at'), table_name='test_executions')
    op.drop_index(op.f('ix_test_executions_status'), table_name='test_executions')
    op.drop_index(op.f('ix_test_executions_user_id'), table_name='test_executions')
    op.drop_index(op.f('ix_tests_created_at'), table_name='tests')
    op.drop_index(op.f('ix_tests_environment'), table_name='tests')
    op.drop_index(op.f('ix_tests_priority'), table_name='tests')
    op.drop_index(op.f('ix_tests_status'), table_name='tests')
    op.drop_index(op.f('ix_tests_test_type'), table_name='tests')
    op.drop_index(op.f('ix_tests_user_id'), table_name='tests')
    
    # Удаляем таблицы
    op.drop_table('test_reports')
    op.drop_table('test_suites')
    op.drop_table('test_results')
    op.drop_table('test_executions')
    op.drop_table('tests')
    
    # Удаляем enum типы
    op.execute("DROP TYPE testenvironment")
    op.execute("DROP TYPE testpriority")
    op.execute("DROP TYPE teststatus")
    op.execute("DROP TYPE testtype") 