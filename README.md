# Student portal — Phase 1

A Django portal where your students sign in, find their course, download that
session's files, and tick lessons off. You add all content through the Django
admin; there is no code to touch when a new student or lesson arrives.

Phase 1 covers login, dashboard, lessons, protected file downloads, completion
tracking and a progress bar. Phases 2–4 (timed hints, Pyodide, memberships) are
not built yet — the data model leaves room for them.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
# paste that into DJANGO_SECRET_KEY in .env, and set DJANGO_DEBUG=True

python manage.py migrate
python manage.py seed_demo        # demo course, files and two students
python manage.py createsuperuser  # your own tutor login
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in as `demo_student` / `demo-student-pass`.
Admin is at `/admin/`.

Delete the `demo_` accounts in the admin before you use this with real students.

## Editing the styling

The compiled CSS at `static/css/app.css` is committed, so **deployment needs no
Node**. Only rebuild it if you change templates or `tailwind.config.js`:

```bash
npm install
npm run css        # or: npm run css:watch while editing
```

## Your weekly workflow in the admin

1. **Courses → Add course.** Title, subject, description. The slug fills itself in.
2. Add lessons inline on the course page (order, title), then click through to a
   lesson to attach files.
3. **Lesson page → Files.** Each file gets a label the student sees ("Session 3
   slides"), a type, and the upload. PPTX, PDF, IPYNB and CSV all work.
4. **Enrolments** on the course page connect students to it.
5. **Users → Add user** creates a login; fill in the Student profile section
   underneath (display name, platform, guardian email if under 18).

## Deploying to PythonAnywhere (free tier)

1. Push this repo to GitHub. **Make it private** — it is the tutor tooling for a
   database of children's names.
2. On PythonAnywhere, open a Bash console:

```bash
git clone git@github.com:you/student-portal.git
cd student-portal
mkvirtualenv portal --python=python3.10
pip install -r requirements.txt
mkdir -p /home/yourname/private_media
```

3. Create `.env` on the server (never committed) with `DJANGO_DEBUG=False`, a
   fresh `DJANGO_SECRET_KEY`, your `DJANGO_ALLOWED_HOSTS`,
   `DJANGO_CSRF_TRUSTED_ORIGINS`, and
   `DJANGO_MEDIA_ROOT=/home/yourname/private_media`.
4. `python manage.py migrate && python manage.py collectstatic --noinput && python manage.py createsuperuser`
5. **Web tab → WSGI configuration file.** Replace its contents with
   `deploy/pythonanywhere_wsgi.py` and change `USERNAME`.
6. **Web tab → Static files.** Map `/static/` to
   `/home/yourname/student-portal/staticfiles`. Map nothing else — in
   particular, do **not** add a mapping for the media directory.
7. Set the virtualenv to `/home/yourname/.virtualenvs/portal`, enable "Force
   HTTPS", and reload.

Free-tier accounts expire after three months of inactivity; log in
occasionally. To upgrade later, move `DJANGO_DB_PATH` to Postgres — no model
changes are needed.

## How student data is protected

- Secrets come from environment variables. `.env`, `db.sqlite3` and the media
  directory are all in `.gitignore`.
- **Uploads are stored outside anything the web server serves.** Filenames on
  disk are random UUIDs; the original name is kept in a database column. The
  only route to a file is `/file/<id>/`, which checks the signed-in student is
  enrolled on that lesson's course before streaming a byte.
- Every query a student can reach is filtered by enrolment in
  `learning/services.py`. Views never build their own querysets, so a new page
  cannot accidentally leak another student's data.
- Non-enrolled access returns 404 rather than 403, which avoids confirming that
  a course or lesson exists.
- The profile stores a display name, platform, a minor flag and a guardian
  email. No date of birth, no address, no phone number. Keep it that way — under
  GDPR, every extra field is a field you have to justify, secure and delete on
  request.
- Pages carry `noindex`, and cookies are secure and HttpOnly in production.

Run the checks before each deploy:

```bash
python manage.py test
python manage.py check --deploy
```

The test suite specifically asserts that one student cannot see, download or
tick another student's material.

## Layout

```
portal/settings.py      configuration, all secrets from the environment
accounts/               StudentProfile, attached to Django's User
learning/models.py      Course, Enrollment, Lesson, LessonFile, LessonProgress
learning/services.py    every enrolment-filtered query lives here
learning/views.py       dashboard, course, lesson, toggle, protected download
learning/tests.py       access-control and progress tests
templates/              base, login, dashboard, course, lesson, partials
static/css/app.css      compiled Tailwind (committed)
deploy/                 PythonAnywhere WSGI file
```
