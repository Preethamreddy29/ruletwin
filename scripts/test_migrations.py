import os
import subprocess
import sys
from urllib.parse import urlparse


def main() -> int:
    database_url = os.environ.get("RULETWIN_DATABASE_URL", "")
    database_name = urlparse(database_url.replace("postgresql+psycopg", "postgresql")).path
    if "test" not in database_name.lower():
        print("Migration cycle refused: database name must contain 'test'.", file=sys.stderr)
        return 2
    for arguments in (
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        [sys.executable, "-m", "alembic", "check"],
    ):
        completed = subprocess.run(arguments, check=False)  # noqa: S603
        if completed.returncode:
            return completed.returncode
    print("Migration upgrade/downgrade/forward/check cycle passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
