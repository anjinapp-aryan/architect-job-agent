-- =====================================================================
-- architect-job-agent — Supabase bootstrap
--
-- Run this ONCE in: Supabase Dashboard -> SQL Editor -> New query
-- Then run `alembic upgrade head` from your machine to create the tables.
-- =====================================================================

-- 1. Dedicated schema so the app is isolated from `public`
--    (and from PostgREST's auto-exposed REST API).
CREATE SCHEMA IF NOT EXISTS aja;

-- 2. Make `aja` the default for the application role's sessions.
--    `postgres` is the superuser Supabase gives you; in a real prod setup
--    you'd create a least-privilege role and grant only what's needed.
ALTER ROLE postgres SET search_path TO aja, public;

-- 3. Grant usage so future tables created by Alembic are accessible.
GRANT USAGE ON SCHEMA aja TO postgres, anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON SCHEMA aja TO postgres;

-- 4. (Optional, defensive) Block PostgREST's anon/authenticated roles
--    from touching application tables — only your backend should.
REVOKE ALL ON ALL TABLES IN SCHEMA aja FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA aja
    REVOKE ALL ON TABLES FROM anon, authenticated;

-- 5. Quick sanity check.
SELECT current_database()         AS database,
       current_schema             AS default_schema,
       current_setting('search_path') AS search_path;
