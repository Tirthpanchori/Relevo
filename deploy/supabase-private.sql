-- Run after Alembic migrations, in a DEDICATED Relevo Supabase project.
-- The Python engine uses server credentials; browser/PostgREST roles get no access.
BEGIN;
REVOKE ALL ON TABLE public.jobs, public.attempts, public.job_events,
    public.alembic_version FROM anon, authenticated;
REVOKE ALL ON SCHEMA relevo_demo FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA relevo_demo FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA relevo_demo REVOKE ALL ON TABLES FROM anon, authenticated;
COMMIT;
-- Also disable the project's Data API if unused. Check unauthenticated table access
-- after every migration; this script is not a claim that hosted privileges passed.
