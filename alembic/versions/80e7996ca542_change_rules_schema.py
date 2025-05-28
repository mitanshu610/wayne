"""Change rules schema

Revision ID: 80e7996ca542
Revises: c6f8fe8fbdbf
Create Date: 2025-01-27 18:56:11.495857

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '80e7996ca542'
down_revision = 'c6f8fe8fbdbf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Explicit changes to the rules schema ###
    # Remove the `rule_conditions` table if it exists
    op.drop_table('rule_conditions')

    # Drop the `OperatorEnum` if it exists
    op.execute("DROP TYPE IF EXISTS operatorenum;")

    # Add the new `condition_data` column to the `rules` table
    op.add_column(
        'rules',
        sa.Column('condition_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Optional: Drop any constraints or references to removed fields (if necessary)
    op.drop_index('ix_rules_feature_id', table_name='rules')
    op.drop_constraint('rules_feature_id_fkey', 'rules', type_='foreignkey')
    op.drop_column('rules', 'feature_id')


def downgrade() -> None:
    # Recreate the `OperatorEnum` type
    op.execute("CREATE TYPE operatorenum AS ENUM ('=', '>', '<', '>=', '<=');")

    # Recreate the `rule_conditions` table
    op.create_table(
        'rule_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('condition_key', sa.String(), nullable=False),
        sa.Column('operator', sa.Enum('=', '>', '<', '>=', '<=', name='operatorenum'), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=dict),
        sa.Column('time_period', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], name='rule_conditions_rule_id_fkey'),
        sa.Index('ix_rule_conditions_rule_id', 'rule_id')
    )

    # Drop the `condition_data` column
    op.drop_column('rules', 'condition_data')

    # Recreate the dropped constraints and index for `feature_id`
    op.add_column(
        'rules',
        sa.Column('feature_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key('rules_feature_id_fkey', 'rules', 'features', ['feature_id'], ['id'])
    op.create_index('ix_rules_feature_id', 'rules', ['feature_id'], unique=False)
