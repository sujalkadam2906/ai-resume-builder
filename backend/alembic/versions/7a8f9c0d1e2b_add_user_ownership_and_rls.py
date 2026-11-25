"""add_user_ownership_and_rls

Revision ID: 7a8f9c0d1e2b
Revises: 4426bf87b36a
Create Date: 2026-11-24 21:45:00.000000

"""
import logging
import os
from typing import Sequence, Union
import uuid

from alembic import context, op
import sqlalchemy as sa

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision: str = '7a8f9c0d1e2b'
down_revision: Union[str, Sequence[str], None] = '4426bf87b36a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All 13 relational tables in the schema
ALL_TABLES = [
    "candidate_profiles",
    "educations",
    "experiences",
    "skills",
    "projects",
    "certifications",
    "achievements",
    "professional_developments",
    "job_descriptions",
    "resumes",
    "resume_versions",
    "ats_evaluations",
    "file_assets",
]

OWNERSHIP_TABLES = [
    "candidate_profiles",
    "job_descriptions",
    "resumes",
    "file_assets",
]


def upgrade() -> None:
    """Apply safe nullable user ownership columns, indexes, foreign keys, backfill, and RLS."""
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_offline = context.is_offline_mode()

    # ==============================================================================
    # 1. Schema Alteration: Add Nullable user_id Columns and Indexes
    # ==============================================================================
    for table_name in OWNERSHIP_TABLES:
        op.add_column(
            table_name,
            sa.Column('user_id', sa.Uuid(), nullable=True),
        )
        op.create_index(
            f'ix_{table_name}_user_id',
            table_name,
            ['user_id'],
            unique=False,
        )

    # ==============================================================================
    # 2. Add Foreign Keys to auth.users(id) in PostgreSQL / Supabase
    # ==============================================================================
    if dialect == "postgresql":
        if is_offline:
            # Emit standard PostgreSQL cross-schema foreign keys when generating static DDL
            for table_name in OWNERSHIP_TABLES:
                op.create_foreign_key(
                    f'fk_{table_name}_user_id_auth_users',
                    table_name,
                    'users',
                    ['user_id'],
                    ['id'],
                    referent_schema='auth',
                    ondelete='CASCADE',
                )
        else:
            # Check specifically if table 'users' in schema 'auth' exists
            auth_users_exist = bind.execute(
                sa.text("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'auth' AND table_name = 'users'
                """)
            ).scalar()

            if auth_users_exist:
                for table_name in OWNERSHIP_TABLES:
                    op.create_foreign_key(
                        f'fk_{table_name}_user_id_auth_users',
                        table_name,
                        'users',
                        ['user_id'],
                        ['id'],
                        referent_schema='auth',
                        ondelete='CASCADE',
                    )
                logger.info("Successfully established foreign keys to auth.users(id).")
            else:
                logger.warning(
                    "PostgreSQL table 'auth.users' not detected in schema 'auth'; "
                    "deferred cross-schema foreign key constraint."
                )

    # ==============================================================================
    # 3. Data Backfill & Integrity Check (Fail-Closed Safety)
    # ==============================================================================
    if is_offline:
        # Static SQL script generation: emit deterministic UPDATE statements using auth.users lookup
        operator_email = os.getenv("ALLOWED_EMAILS", "").split(",")[0].strip() or "operator@example.com"
        op.execute(f"""
            -- Backfill candidate_profiles for sujal using auth.users subquery
            UPDATE candidate_profiles
            SET user_id = (SELECT id FROM auth.users WHERE lower(email) = lower('{operator_email}') LIMIT 1)
            WHERE slug = 'sujal' AND is_synthetic = FALSE AND user_id IS NULL;

            -- Backfill resumes linked to sujal
            UPDATE resumes
            SET user_id = (SELECT id FROM auth.users WHERE lower(email) = lower('{operator_email}') LIMIT 1)
            WHERE profile_id IN (SELECT id FROM candidate_profiles WHERE slug = 'sujal') AND user_id IS NULL;

            -- Backfill job_descriptions linked to sujal directly or via resumes
            UPDATE job_descriptions
            SET user_id = (SELECT id FROM auth.users WHERE lower(email) = lower('{operator_email}') LIMIT 1)
            WHERE profile_id IN (SELECT id FROM candidate_profiles WHERE slug = 'sujal') AND user_id IS NULL;

            UPDATE job_descriptions
            SET user_id = (SELECT id FROM auth.users WHERE lower(email) = lower('{operator_email}') LIMIT 1)
            WHERE id IN (
                SELECT job_description_id FROM resumes
                WHERE profile_id IN (SELECT id FROM candidate_profiles WHERE slug = 'sujal')
                AND job_description_id IS NOT NULL
            ) AND user_id IS NULL;

            -- Backfill file_assets linked to sujal
            UPDATE file_assets
            SET user_id = (SELECT id FROM auth.users WHERE lower(email) = lower('{operator_email}') LIMIT 1)
            WHERE profile_id IN (SELECT id FROM candidate_profiles WHERE slug = 'sujal') AND user_id IS NULL;
        """)
    else:
        try:
            profiles_rows = bind.execute(
                sa.text("SELECT id, slug, is_synthetic FROM candidate_profiles")
            ).fetchall()
        except Exception:
            profiles_rows = []

        has_sujal = any(r[1] == 'sujal' and not r[2] for r in profiles_rows)
        non_synthetic_slugs = [r[1] for r in profiles_rows if not r[2]]

        if has_sujal or non_synthetic_slugs:
            # Resolve owner UUID from environment or auth.users table
            sujal_user_id = os.getenv("SUJAL_AUTH_USER_ID", "").strip()

            if not sujal_user_id and dialect == "postgresql":
                try:
                    operator_email = os.getenv("ALLOWED_EMAILS", "").split(",")[0].strip()
                    if operator_email:
                        row = bind.execute(
                            sa.text("SELECT id FROM auth.users WHERE lower(email) = lower(:email) LIMIT 1"),
                            {"email": operator_email},
                        ).fetchone()
                        if row:
                            sujal_user_id = str(row[0])
                            logger.info("Resolved operator UUID %s from auth.users for %s", sujal_user_id, operator_email)
                except Exception as e:
                    logger.warning("Could not auto-query auth.users during migration backfill: %s", e)

            # Fail-closed: If non-synthetic profiles exist but owner cannot be determined, abort!
            if not sujal_user_id:
                raise RuntimeError(
                    f"Migration aborted: Non-synthetic profile(s) {non_synthetic_slugs} exist in the database, "
                    "but the owner user UUID could not be determined. "
                    "Set SUJAL_AUTH_USER_ID or ensure the operator email is present in auth.users before migrating."
                )

            try:
                user_uuid = uuid.UUID(sujal_user_id)
            except ValueError:
                raise RuntimeError(f"Migration aborted: Invalid UUID format for SUJAL_AUTH_USER_ID: '{sujal_user_id}'")

            # Check for unexpected non-synthetic profiles requiring manual resolution
            unexpected_profiles = [s for s in non_synthetic_slugs if s != 'sujal']
            if unexpected_profiles:
                raise RuntimeError(
                    f"Migration aborted: Found unrecognized non-synthetic profiles: {unexpected_profiles}. "
                    "Manual ownership resolution is required."
                )

            # A. Backfill Sujal Candidate Profile
            bind.execute(
                sa.text("UPDATE candidate_profiles SET user_id = :user_id WHERE slug = 'sujal' AND is_synthetic = FALSE"),
                {"user_id": user_uuid},
            )

            # B. Check for orphaned resumes
            orphaned_resumes = bind.execute(
                sa.text("SELECT id FROM resumes WHERE profile_id NOT IN (SELECT id FROM candidate_profiles)")
            ).fetchall()
            if orphaned_resumes:
                raise RuntimeError(
                    f"Migration aborted: Found {len(orphaned_resumes)} orphaned resume(s) referencing missing profiles. "
                    "Manual cleanup required."
                )

            # Backfill Resumes linked to Sujal
            bind.execute(
                sa.text("""
                    UPDATE resumes
                    SET user_id = :user_id
                    WHERE profile_id IN (
                        SELECT id FROM candidate_profiles WHERE slug = 'sujal'
                    )
                """),
                {"user_id": user_uuid},
            )

            # C. Backfill Job Descriptions linked to Sujal directly or via Resumes
            bind.execute(
                sa.text("""
                    UPDATE job_descriptions
                    SET user_id = :user_id
                    WHERE profile_id IN (
                        SELECT id FROM candidate_profiles WHERE slug = 'sujal'
                    )
                """),
                {"user_id": user_uuid},
            )
            bind.execute(
                sa.text("""
                    UPDATE job_descriptions
                    SET user_id = :user_id
                    WHERE id IN (
                        SELECT job_description_id FROM resumes
                        WHERE profile_id IN (SELECT id FROM candidate_profiles WHERE slug = 'sujal')
                        AND job_description_id IS NOT NULL
                    ) AND user_id IS NULL
                """),
                {"user_id": user_uuid},
            )

            # Verify no unowned ambiguous JDs exist
            unowned_jds = bind.execute(
                sa.text("SELECT id FROM job_descriptions WHERE user_id IS NULL AND profile_id IS NULL")
            ).fetchall()
            if unowned_jds:
                raise RuntimeError(
                    f"Migration aborted: Found {len(unowned_jds)} unowned job description(s) without linked profile or resume. "
                    f"IDs: {[str(r[0]) for r in unowned_jds]}. Manual resolution required."
                )

            # D. Backfill File Assets linked to Sujal
            bind.execute(
                sa.text("""
                    UPDATE file_assets
                    SET user_id = :user_id
                    WHERE profile_id IN (
                        SELECT id FROM candidate_profiles WHERE slug = 'sujal'
                    )
                """),
                {"user_id": user_uuid},
            )

            unowned_assets = bind.execute(
                sa.text("SELECT id FROM file_assets WHERE user_id IS NULL AND profile_id IS NULL")
            ).fetchall()
            if unowned_assets:
                raise RuntimeError(
                    f"Migration aborted: Found {len(unowned_assets)} unowned file asset(s) without linked profile. "
                    f"IDs: {[str(r[0]) for r in unowned_assets]}. Manual resolution required."
                )

            logger.info("Successfully validated and backfilled Sujal records with user_id %s", sujal_user_id)

        logger.info("Successfully validated and backfilled Sujal records with user_id %s", sujal_user_id)

    # Note on demo_candidate:
    # Records where is_synthetic = TRUE remain with user_id = NULL (unowned, shared template).

    # ==============================================================================
    # 4. Row Level Security (RLS) Enablement & Policies (PostgreSQL / Supabase)
    # ==============================================================================
    if dialect == "postgresql":
        # Notice: In Supabase, the backend connects as database owner 'postgres' which
        # has BYPASSRLS. RLS acts as the defense-in-depth barrier against direct PostgREST access.
        # Application-level query scoping in FastAPI remains mandatory.

        # Enable RLS on all 13 tables
        for tbl in ALL_TABLES:
            op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")

        # A. candidate_profiles RLS Policies
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_select_policy\" ON candidate_profiles;")
        op.execute("""
            CREATE POLICY "candidate_profiles_select_policy" ON candidate_profiles
            FOR SELECT USING (
                is_synthetic = TRUE
                OR (auth.uid() IS NOT NULL AND user_id = auth.uid())
            );
        """)
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_insert_policy\" ON candidate_profiles;")
        op.execute("""
            CREATE POLICY "candidate_profiles_insert_policy" ON candidate_profiles
            FOR INSERT WITH CHECK (
                auth.uid() IS NOT NULL
                AND user_id = auth.uid()
                AND is_synthetic = FALSE
            );
        """)
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_update_policy\" ON candidate_profiles;")
        op.execute("""
            CREATE POLICY "candidate_profiles_update_policy" ON candidate_profiles
            FOR UPDATE USING (
                auth.uid() IS NOT NULL
                AND user_id = auth.uid()
                AND is_synthetic = FALSE
            ) WITH CHECK (
                auth.uid() IS NOT NULL
                AND user_id = auth.uid()
                AND is_synthetic = FALSE
            );
        """)
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_delete_policy\" ON candidate_profiles;")
        op.execute("""
            CREATE POLICY "candidate_profiles_delete_policy" ON candidate_profiles
            FOR DELETE USING (
                auth.uid() IS NOT NULL
                AND user_id = auth.uid()
                AND is_synthetic = FALSE
            );
        """)

        # B. Child Profile Tables RLS Policies (Inherit from candidate_profiles)
        child_profile_tables = [
            "educations",
            "experiences",
            "skills",
            "projects",
            "certifications",
            "achievements",
            "professional_developments",
        ]
        for ctbl in child_profile_tables:
            op.execute(f"DROP POLICY IF EXISTS \"{ctbl}_select_policy\" ON {ctbl};")
            op.execute(f"""
                CREATE POLICY "{ctbl}_select_policy" ON {ctbl}
                FOR SELECT USING (
                    EXISTS (
                        SELECT 1 FROM candidate_profiles p
                        WHERE p.id = {ctbl}.profile_id
                        AND (p.is_synthetic = TRUE OR (auth.uid() IS NOT NULL AND p.user_id = auth.uid()))
                    )
                );
            """)
            op.execute(f"DROP POLICY IF EXISTS \"{ctbl}_mutate_policy\" ON {ctbl};")
            op.execute(f"""
                CREATE POLICY "{ctbl}_mutate_policy" ON {ctbl}
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM candidate_profiles p
                        WHERE p.id = {ctbl}.profile_id
                        AND p.is_synthetic = FALSE
                        AND auth.uid() IS NOT NULL
                        AND p.user_id = auth.uid()
                    )
                ) WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM candidate_profiles p
                        WHERE p.id = {ctbl}.profile_id
                        AND p.is_synthetic = FALSE
                        AND auth.uid() IS NOT NULL
                        AND p.user_id = auth.uid()
                    )
                );
            """)

        # C. job_descriptions RLS Policies
        op.execute("DROP POLICY IF EXISTS \"job_descriptions_select_policy\" ON job_descriptions;")
        op.execute("""
            CREATE POLICY "job_descriptions_select_policy" ON job_descriptions
            FOR SELECT USING (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            );
        """)
        op.execute("DROP POLICY IF EXISTS \"job_descriptions_mutate_policy\" ON job_descriptions;")
        op.execute("""
            CREATE POLICY "job_descriptions_mutate_policy" ON job_descriptions
            FOR ALL USING (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            ) WITH CHECK (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            );
        """)

        # D. resumes RLS Policies
        op.execute("DROP POLICY IF EXISTS \"resumes_select_policy\" ON resumes;")
        op.execute("""
            CREATE POLICY "resumes_select_policy" ON resumes
            FOR SELECT USING (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            );
        """)
        op.execute("DROP POLICY IF EXISTS \"resumes_mutate_policy\" ON resumes;")
        op.execute("""
            CREATE POLICY "resumes_mutate_policy" ON resumes
            FOR ALL USING (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            ) WITH CHECK (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            );
        """)

        # E. Child Resume Tables RLS Policies (resume_versions, ats_evaluations)
        child_resume_tables = ["resume_versions", "ats_evaluations"]
        for rtbl in child_resume_tables:
            op.execute(f"DROP POLICY IF EXISTS \"{rtbl}_select_policy\" ON {rtbl};")
            op.execute(f"""
                CREATE POLICY "{rtbl}_select_policy" ON {rtbl}
                FOR SELECT USING (
                    EXISTS (
                        SELECT 1 FROM resumes r
                        WHERE r.id = {rtbl}.resume_id
                        AND auth.uid() IS NOT NULL
                        AND r.user_id = auth.uid()
                    )
                );
            """)
            op.execute(f"DROP POLICY IF EXISTS \"{rtbl}_mutate_policy\" ON {rtbl};")
            op.execute(f"""
                CREATE POLICY "{rtbl}_mutate_policy" ON {rtbl}
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM resumes r
                        WHERE r.id = {rtbl}.resume_id
                        AND auth.uid() IS NOT NULL
                        AND r.user_id = auth.uid()
                    )
                ) WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM resumes r
                        WHERE r.id = {rtbl}.resume_id
                        AND auth.uid() IS NOT NULL
                        AND r.user_id = auth.uid()
                    )
                );
            """)

        # F. file_assets RLS Policies
        op.execute("DROP POLICY IF EXISTS \"file_assets_all_policy\" ON file_assets;")
        op.execute("""
            CREATE POLICY "file_assets_all_policy" ON file_assets
            FOR ALL USING (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            ) WITH CHECK (
                auth.uid() IS NOT NULL AND user_id = auth.uid()
            );
        """)

        # G. Schema and Sequence Privileges Hardening
        # Allow authenticated users schema usage and sequence selection
        op.execute("GRANT USAGE ON SCHEMA public TO authenticated;")
        op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;")
        # Restrict table access: authenticated can only access rows matching RLS policies
        op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;")
        # Completely revoke table and sequence access from public anonymous API clients
        op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;")
        op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;")


def downgrade() -> None:
    """Revert user ownership columns, indexes, foreign keys, and RLS policies."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Drop all RLS policies
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_select_policy\" ON candidate_profiles;")
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_insert_policy\" ON candidate_profiles;")
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_update_policy\" ON candidate_profiles;")
        op.execute("DROP POLICY IF EXISTS \"candidate_profiles_delete_policy\" ON candidate_profiles;")

        child_profile_tables = [
            "educations",
            "experiences",
            "skills",
            "projects",
            "certifications",
            "achievements",
            "professional_developments",
        ]
        for ctbl in child_profile_tables:
            op.execute(f"DROP POLICY IF EXISTS \"{ctbl}_select_policy\" ON {ctbl};")
            op.execute(f"DROP POLICY IF EXISTS \"{ctbl}_mutate_policy\" ON {ctbl};")

        op.execute("DROP POLICY IF EXISTS \"job_descriptions_select_policy\" ON job_descriptions;")
        op.execute("DROP POLICY IF EXISTS \"job_descriptions_mutate_policy\" ON job_descriptions;")

        op.execute("DROP POLICY IF EXISTS \"resumes_select_policy\" ON resumes;")
        op.execute("DROP POLICY IF EXISTS \"resumes_mutate_policy\" ON resumes;")

        child_resume_tables = ["resume_versions", "ats_evaluations"]
        for rtbl in child_resume_tables:
            op.execute(f"DROP POLICY IF EXISTS \"{rtbl}_select_policy\" ON {rtbl};")
            op.execute(f"DROP POLICY IF EXISTS \"{rtbl}_mutate_policy\" ON {rtbl};")

        op.execute("DROP POLICY IF EXISTS \"file_assets_all_policy\" ON file_assets;")

        # Disable RLS on all 13 tables
        for tbl in ALL_TABLES:
            op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY;")

        # Drop foreign keys to auth.users
        for table_name in OWNERSHIP_TABLES:
            try:
                op.drop_constraint(f'fk_{table_name}_user_id_auth_users', table_name, type_='foreignkey')
            except Exception as e:
                logger.warning("Could not drop constraint fk_%s_user_id_auth_users: %s", table_name, e)

    # Drop indexes and columns
    for table_name in reversed(OWNERSHIP_TABLES):
        op.drop_index(f'ix_{table_name}_user_id', table_name=table_name)
        op.drop_column(table_name, 'user_id')
