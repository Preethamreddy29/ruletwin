#!/usr/bin/env bash
# Keep LF line endings: this initializer executes inside the Alpine PostgreSQL image.
set -euo pipefail

read_secret() {
  local value_name="$1"
  local file_name="$2"
  local value="${!value_name:-}"
  local file="${!file_name:-}"
  if [[ -n "$value" && -n "$file" ]]; then
    echo "Configure only one of ${value_name} or ${file_name}." >&2
    exit 1
  fi
  if [[ -n "$file" ]]; then
    [[ -f "$file" ]] || { echo "Secret file for ${value_name} is unavailable." >&2; exit 1; }
    value="$(<"$file")"
  fi
  printf -v "$value_name" '%s' "$value"
}

read_secret POSTGRES_APP_PASSWORD POSTGRES_APP_PASSWORD_FILE
read_secret POSTGRES_TEST_PASSWORD POSTGRES_TEST_PASSWORD_FILE
: "${POSTGRES_APP_PASSWORD:?POSTGRES_APP_PASSWORD or POSTGRES_APP_PASSWORD_FILE is required}"

psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=app_password="$POSTGRES_APP_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE ruletwin_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ruletwin_app') \gexec
GRANT CONNECT ON DATABASE ruletwin TO ruletwin_app;
GRANT USAGE ON SCHEMA public TO ruletwin_app;
SQL

if [[ -n "$POSTGRES_TEST_PASSWORD" ]]; then
  psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    --set=test_password="$POSTGRES_TEST_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE ruletwin_test LOGIN PASSWORD %L CREATEDB', :'test_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ruletwin_test') \gexec
GRANT CONNECT ON DATABASE ruletwin TO ruletwin_test;
GRANT ALL ON SCHEMA public TO ruletwin_test;
SQL
fi
