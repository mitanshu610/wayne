from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, update
from slugify import slugify

# revision identifiers, used by Alembic.
revision: str = '403add78f20c'
down_revision: Union[str, None] = '5cdae26dce95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add the new column `slug`
    op.add_column('plans', sa.Column('slug', sa.String(), nullable=True))

    # Create a temporary connection
    conn = op.get_bind()

    # Reference to the table with UUID type for `id`
    plans_table = table(
        'plans',
        column('id', sa.dialects.postgresql.UUID),  # UUID type
        column('name', sa.String),
        column('slug', sa.String)
    )

    # Fetch all plans
    results = conn.execute(select(plans_table.c.id, plans_table.c.name)).fetchall()

    # Create a set to track used slugs
    used_slugs = set()

    for plan_id, name in results:
        if name:
            new_slug = slugify(name)  # Convert name to slug
            original_slug = new_slug
            counter = 1

            # Ensure uniqueness
            while new_slug in used_slugs:
                new_slug = f"{original_slug}-{counter}"
                counter += 1

            used_slugs.add(new_slug)

            # Update query with correct UUID handling
            conn.execute(
                update(plans_table)
                .where(plans_table.c.id == sa.cast(plan_id, sa.dialects.postgresql.UUID))  # Cast to UUID
                .values(slug=new_slug)
            )

    # Make `slug` column non-nullable
    op.alter_column('plans', 'slug', nullable=False)

    # Add a unique constraint on `slug`
    op.create_unique_constraint('uq_plans_slug', 'plans', ['slug'])

def downgrade() -> None:
    # Drop the unique constraint
    op.drop_constraint('uq_plans_slug', 'plans', type_='unique')

    # Drop the `slug` column
    op.drop_column('plans', 'slug')
