"""Paste into the WSGI configuration file on PythonAnywhere's Web tab,
replacing everything already there. Change USERNAME to your account name."""
import os
import sys
from pathlib import Path

USERNAME = "yourname"
PROJECT = Path(f"/home/{USERNAME}/student-portal")

sys.path.insert(0, str(PROJECT))

# Secrets live in the .env file, which is never committed.
env_file = PROJECT / ".env"
for line in env_file.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")

os.environ["DJANGO_SETTINGS_MODULE"] = "portal.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
