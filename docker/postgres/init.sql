-- Initial DB seed (executed once on first Postgres container creation).
-- Runtime tables are managed by Alembic migrations; this file contains only
-- seeds and extensions.

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
