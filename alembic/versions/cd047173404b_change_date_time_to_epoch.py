"""Change date time to epoch

Revision ID: cd047173404b
Revises: 446213422fdc
Create Date: 2025-01-29 11:01:23.884237

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = 'cd047173404b'
down_revision: Union[str, None] = '446213422fdc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert column types and migrate data in a single operation
    op.alter_column('invoices', 'invoice_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.Integer(),
               existing_nullable=False,
               postgresql_using="EXTRACT(EPOCH FROM invoice_date)::INTEGER")

    op.alter_column('invoices', 'next_due_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.Integer(),
               existing_nullable=False,
               postgresql_using="EXTRACT(EPOCH FROM next_due_date)::INTEGER")

    op.alter_column('payments', 'payment_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.Integer(),
               existing_nullable=False,
               postgresql_using="EXTRACT(EPOCH FROM payment_date)::INTEGER")

    op.alter_column('subscriptions', 'start_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.Integer(),
               existing_nullable=False,
               postgresql_using="EXTRACT(EPOCH FROM start_date)::INTEGER")

    op.alter_column('subscriptions', 'end_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.Integer(),
               existing_nullable=True,
               postgresql_using="EXTRACT(EPOCH FROM end_date)::INTEGER")


def downgrade() -> None:
    # Convert back to TIMESTAMP type while preserving values
    op.alter_column('subscriptions', 'end_date',
               existing_type=sa.Integer(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True,
               postgresql_using="TO_TIMESTAMP(end_date)")

    op.alter_column('subscriptions', 'start_date',
               existing_type=sa.Integer(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="TO_TIMESTAMP(start_date)")

    op.alter_column('payments', 'payment_date',
               existing_type=sa.Integer(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="TO_TIMESTAMP(payment_date)")

    op.alter_column('invoices', 'next_due_date',
               existing_type=sa.Integer(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="TO_TIMESTAMP(next_due_date)")

    op.alter_column('invoices', 'invoice_date',
               existing_type=sa.Integer(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="TO_TIMESTAMP(invoice_date)")
