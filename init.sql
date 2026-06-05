-- PostgreSQL initialization script
-- Runs once when container first starts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For LIKE query optimization

-- Audit log protection (will apply after tables are created by Alembic)
DO $$
BEGIN
    EXECUTE 'REVOKE UPDATE, DELETE ON TABLE audit_logs FROM ' || current_user;
EXCEPTION WHEN others THEN
    NULL;  -- Table may not exist yet (Alembic runs after)
END $$;
