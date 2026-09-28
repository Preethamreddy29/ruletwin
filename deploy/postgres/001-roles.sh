#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_APP_PASSWORD:?POSTGRES_APP_PASSWORD is required}"
: "${POSTGRES_TEST_PASSWORD:?POSTGRES_TEST_PASSWORD is required}"

psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=app_password="$POSTGRES_APP_PASSWORD" --set=test_password="$POSTGRES_TEST_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE ruletwin_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ruletwin_app') \gexec
SELECT format('CREATE ROLE ruletwin_test LOGIN PASSWORD %L CREATEDB', :'test_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ruletwin_test') \gexec
GRANT CONNECT ON DATABASE ruletwin TO ruletwin_app;
GRANT CONNECT ON DATABASE ruletwin TO ruletwin_test;
GRANT USAGE ON SCHEMA public TO ruletwin_app;
GRANT ALL ON SCHEMA public TO ruletwin_test;
SQL
