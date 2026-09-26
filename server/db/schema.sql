CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sso_domain VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    source_doc_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY,
    project_a_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_b_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    synergy_score INT NOT NULL CHECK (synergy_score BETWEEN 0 AND 100),
    spatial_distance_m FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'identified',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (project_a_id <> project_b_id)
);

CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY,
    match_id UUID NOT NULL UNIQUE REFERENCES matches(id) ON DELETE CASCADE,
    nda_signed_a BOOLEAN NOT NULL DEFAULT FALSE,
    nda_signed_b BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_tenant_id ON projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_geom ON projects USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_matches_project_a_id ON matches(project_a_id);
CREATE INDEX IF NOT EXISTS idx_matches_project_b_id ON matches(project_b_id);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
