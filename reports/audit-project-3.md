================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.x + SQLAlchemy
Files:   8 analyzed | ~550 lines of code

## Summary
CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 3
Total findings: 12

## Findings

### [CRITICAL] Hardcoded Secret Key in Source
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` is hardcoded directly in the entry point, committed to version control.
Impact: Anyone with repository access can forge session cookies, bypassing authentication entirely.
Recommendation: Move to environment variable: `os.getenv('SECRET_KEY')`. Add `.env` to `.gitignore`. Create `.env.example`.

### [CRITICAL] Hardcoded Email Credentials in Service
File: services/notification_service.py:9-10
Description: Gmail credentials hardcoded directly in the service class: `self.email_user = 'taskmanager@gmail.com'` and `self.email_password = 'senha123'`.
Impact: Anyone with repository access can authenticate as this Gmail account. Credentials are committed to version control history permanently unless git history is rewritten.
Recommendation: Load from environment variables: `os.getenv('SMTP_USER')` and `os.getenv('SMTP_PASS')`.

### [HIGH] Insecure Password Hashing — MD5
File: models/user.py:29,32
Description: `set_password()` stores passwords using `hashlib.md5(pwd.encode()).hexdigest()`. MD5 is a broken algorithm with pre-computed rainbow tables covering most common passwords.
Impact: Any database breach exposes all user passwords instantly via rainbow table lookup.
Recommendation: Replace with `werkzeug.security.generate_password_hash()` and `check_password_hash()`, which use PBKDF2 with salt automatically.

### [HIGH] Password Field Exposed in API Response
File: models/user.py:17-25
Description: `User.to_dict()` includes `'password': self.password` in the returned dict. The `GET /users` and `GET /users/<id>` endpoints use this method, exposing MD5 password hashes to any API consumer.
Impact: Unauthenticated callers can harvest MD5 hashes of all user passwords from the `/users` endpoint.
Recommendation: Remove `password` from `to_dict()`. Never serialize password fields in API responses.

### [HIGH] N+1 Query Problem — Tasks Listing
File: routes/task_routes.py:41-57
Description: `get_tasks()` fetches all tasks, then for each task executes `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` individually — 2 extra queries per task.
Impact: 100 tasks = 201 queries; response time grows linearly with data volume.
Recommendation: Use SQLAlchemy eager loading: `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()` — requires `db.relationship()` defined in the model, or use a JOIN query.

### [MEDIUM] Overdue Calculation Duplicated Across 4 Files
File: routes/task_routes.py:30-39,71-80,171-180,282-287 | routes/report_routes.py:33-43
Description: The logic `if t.due_date < datetime.utcnow() and t.status not in ('done','cancelled')` is copy-pasted verbatim in `get_tasks()`, `get_task()`, `get_user_tasks()`, `task_stats()`, and `summary_report()`. Five separate instances.
Impact: A business rule change (e.g., grace period of 1 hour) must be applied in 5 places; inconsistencies will silently produce wrong results.
Recommendation: Extract to a helper function `is_overdue(task)` in `utils/helpers.py` and call it from all locations.

### [MEDIUM] N+1 Query in Report — User Productivity Loop
File: routes/report_routes.py:53-68
Description: `summary_report()` fetches all users, then for each user executes `Task.query.filter_by(user_id=u.id).all()` — 1 extra query per user.
Impact: 50 users = 51 queries for a single report endpoint.
Recommendation: Use a single aggregation query with GROUP BY, or use SQLAlchemy's `joinedload(User.tasks)`.

### [MEDIUM] No Authentication on Any Endpoint
File: routes/task_routes.py, routes/user_routes.py, routes/report_routes.py
Description: All endpoints — including `DELETE /users/<id>`, `GET /reports/summary`, and task management — have no authentication or authorization check. The login endpoint generates a `'fake-jwt-token-' + str(user.id)` token that is never validated anywhere.
Impact: Any anonymous user can delete users, read all reports, and manage all tasks.
Recommendation: Implement JWT validation middleware and apply `@login_required` decorator to protected routes.

### [MEDIUM] Magic Numbers and Duplicated Status/Priority Lists
File: routes/task_routes.py:96,99,100,110,113,167-170,177-180
Description: Validation constants `3`, `200`, `1`, `5` and status list `['pending', 'in_progress', 'done', 'cancelled']` are hardcoded inline and duplicated between `create_task()` (lines 96-114) and `update_task()` (lines 166-184).
Impact: Changing priority range or adding a new status requires editing at least 4 locations with risk of missing one.
Recommendation: Extract to `config/constants.py`: `VALID_STATUSES = [...]`, `MIN_PRIORITY = 1`, `MAX_PRIORITY = 5`, `TITLE_MAX_LEN = 200`.

### [LOW] Deprecated: datetime.utcnow() — Python 3.12+
File: routes/task_routes.py:31,72,172,215,285 | routes/report_routes.py:35,42,46,50,133 | models/user.py:14
Description: `datetime.utcnow()` is deprecated since Python 3.12 — it returns a timezone-naive datetime and raises `DeprecationWarning`.
Impact: Code will break or produce warnings in future Python versions. Naive datetimes cause incorrect comparison when mixing with timezone-aware values.
Recommendation: Replace all occurrences with `datetime.now(timezone.utc)` (requires `from datetime import timezone`).

### [LOW] Bare except Clauses Swallow All Errors
File: routes/task_routes.py:62,153,217,232,237 | routes/report_routes.py:186,501,516
Description: Multiple `except:` blocks with no exception type specified silently swallow `KeyboardInterrupt`, `SystemExit`, and all other exceptions, making debugging impossible.
Impact: Critical errors are silently ignored; application appears to work but returns generic 500 responses; no stack traces logged.
Recommendation: Replace with `except Exception as e:` and log the error: `logger.exception("Error in %s: %s", request.path, e)`.

### [LOW] Logging via print() Instead of logging Module
File: routes/task_routes.py:149,153,219,234 | routes/user_routes.py:83,89,147 | services/notification_service.py:21,24
Description: All operational logging done via `print()` statements with no severity levels, no timestamps, no structured format.
Impact: No log levels in production; no log aggregation; no timestamps; cannot filter by severity.
Recommendation: Replace with `import logging; logger = logging.getLogger(__name__)` and use `logger.info()`, `logger.error()`, etc.

================================
Total: 12 findings
================================

## Refactoring Strategy
Decision: Partial-Improve
Reason: Project already has 4 layer directories (models/, routes/, services/, utils/) with ≤ 3 root source files — preserving the existing structure and adding missing layers (config/, middlewares/) plus fixing security issues and extracting business logic.

Planned new structure:
task-manager-api/
├── config/
│   └── settings.py          ← NEW: env vars, constants, DB URI
├── models/
│   ├── user.py              ← FIX: remove password from to_dict(), fix MD5 → werkzeug
│   ├── task.py              ← KEEP: add relationships for eager loading
│   └── category.py          ← KEEP
├── routes/
│   ├── task_routes.py       ← FIX: remove business logic, call controllers
│   ├── user_routes.py       ← FIX: same
│   └── report_routes.py     ← FIX: same
├── controllers/             ← NEW: business logic extracted from routes
│   ├── task_controller.py
│   ├── user_controller.py
│   └── report_controller.py
├── services/
│   └── notification_service.py  ← FIX: credentials to env vars
├── middlewares/             ← NEW: auth decorator, error handler
│   ├── auth.py
│   └── error_handler.py
├── utils/
│   └── helpers.py           ← ADD: is_overdue(), shared constants
├── database.py              ← KEEP
├── seed.py                  ← KEEP
└── app.py                   ← FIX: SECRET_KEY from env, debug from env
