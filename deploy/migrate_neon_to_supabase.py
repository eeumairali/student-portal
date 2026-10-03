"""One-off: copy every row from the Neon database into Supabase.

Reads DATABASE_URL (Neon, source) and SUPABASE_DATABASE_URL (target) from .env.
Run from the project root:  python deploy/migrate_neon_to_supabase.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP = ROOT / "deploy" / "neon_dump.json"


def read_env():
    values = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def manage(*args, database_url):
    env = {**os.environ, "DATABASE_URL": database_url, "PYTHONUTF8": "1"}
    print(">> manage.py", " ".join(args))
    subprocess.run([sys.executable, "manage.py", *args], cwd=ROOT, env=env, check=True)


def main():
    env = read_env()
    neon, supabase = env.get("DATABASE_URL"), env.get("SUPABASE_DATABASE_URL")
    if not neon or not supabase:
        sys.exit("Set both DATABASE_URL (Neon) and SUPABASE_DATABASE_URL in .env")

    # 1. Export everything from Neon. contenttypes/permissions are recreated by migrate.
    manage(
        "dumpdata", "--natural-foreign", "--natural-primary",
        "-e", "contenttypes", "-e", "auth.Permission", "-e", "sessions",
        "--indent", "2", "-o", str(DUMP),
        database_url=neon,
    )
    # 2. Build the schema on Supabase, then 3. load the data.
    manage("migrate", "--noinput", database_url=supabase)
    manage("loaddata", str(DUMP), database_url=supabase)
    print(f"\nDone. Now point DATABASE_URL at Supabase. Delete {DUMP.name} (it contains your data).")


if __name__ == "__main__":
    main()
