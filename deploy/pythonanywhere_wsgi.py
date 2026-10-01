"""Paste into the WSGI configuration file on PythonAnywhere's Web tab."""
import os
import sys
from pathlib import Path

PROJECT = Path("/home/eeumairali/student-portal")

sys.path.insert(0, str(PROJECT))

# Secrets live in the .env file, which is never committed.
env_file = PROJECT / ".env"
if not env_file.exists():
    raise RuntimeError(f"Missing deployment environment file: {env_file}")
for line in env_file.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        os.environ[key] = value.strip().strip('"').strip("'")

os.environ["DJANGO_SETTINGS_MODULE"] = "portal.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
