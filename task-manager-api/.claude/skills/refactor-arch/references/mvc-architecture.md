# MVC Architecture Guidelines

Reference for Phase 3. Defines the target structure, layer responsibilities, and the adaptive strategy logic.

---

## Target MVC Structure

### Python / Flask

```
src/
├── config/
│   └── settings.py          # All config: env vars, DB path, app settings
├── models/
│   └── <domain>_model.py    # Data access: SQL queries or ORM models
├── controllers/
│   └── <domain>_controller.py  # Business logic: validation, orchestration
├── views/
│   └── routes.py            # HTTP layer: route registration, request parsing, response formatting
├── middlewares/
│   └── error_handler.py     # Centralized error handling, auth decorators
└── app.py                   # Composition root: create app, register blueprints, init DB
```

Alternative when project already uses Flask Blueprints (`routes/` folder exists):

```
├── routes/
│   └── <domain>_routes.py   # Thin route handlers, call controllers
├── controllers/
│   └── <domain>_controller.py
```

### Node.js / Express

```
src/
├── config/
│   └── settings.js          # All config: env vars, DB settings
├── models/
│   └── <domain>Model.js     # Data access: SQL or ORM queries
├── controllers/
│   └── <domain>Controller.js  # Business logic
├── routes/
│   └── <domain>Routes.js    # Route definitions, call controllers
├── middlewares/
│   └── errorHandler.js      # Error middleware, auth middleware
└── app.js                   # Express app factory
```

---

## Layer Responsibilities

### Config (`config/settings.py` or `config/settings.js`)
- Load all environment variables
- Set application defaults
- Database connection string / path
- **NEVER** contain business logic

### Models (`models/`)
- Abstract all data persistence (SQL queries or ORM models)
- Return plain objects/dicts, not HTTP responses
- Contain no HTTP-specific code (no `request`, no `jsonify`, no `res.json`)
- One file per domain entity (e.g., `produto_model.py`, `usuario_model.py`)

### Controllers (`controllers/`)
- Contain business logic and orchestration
- Validate input data (or delegate to schema validators)
- Call model functions, apply business rules, return results
- Contain no HTTP-specific code
- One file per domain

### Views / Routes (`views/routes.py` or `routes/`)
- Define URL routes and HTTP methods
- Parse request data (`request.get_json()`, `req.body`)
- Call appropriate controller functions
- Format and return HTTP responses (`jsonify`, `res.json()`)
- Contain **no business logic**, **no database queries**

### Middlewares (`middlewares/`)
- Cross-cutting concerns: authentication, authorization, logging, error handling
- Flask: decorators (`@require_auth`) and `@app.errorhandler`
- Express: middleware functions `(req, res, next)`
- Centralized error handler catches all unhandled exceptions

### Entry Point (`app.py` / `app.js`)
- Create framework application
- Load config
- Register routes / blueprints
- Initialize database
- Minimal logic — purely composition

---

## Adaptive Strategy

### Decision Algorithm

Run these commands to determine which strategy to apply:

```bash
# Count known layer directories at project root
layer_dirs=$(ls -d */ 2>/dev/null | grep -cE "^(models|routes|controllers|views|services|middlewares|config|src)/$")

# Count source files at root (excluding entry points)
root_files=$(find . -maxdepth 1 \( -name "*.py" -o -name "*.js" \) 2>/dev/null | grep -vE "app\.(py|js)|seed\.(py|js)|database\.(py|js)" | wc -l | tr -d ' ')

echo "Layer dirs: $layer_dirs | Root source files: $root_files"
```

**Decision rule:**
- If `layer_dirs >= 2` AND `root_files <= 3` → **PARTIAL-IMPROVE**
- Otherwise → **MONOLITH-REWRITE**

### MONOLITH-REWRITE Behavior

Applied when: all (or most) code lives in a flat file structure with no layer separation.

Actions:
1. Create full `src/` directory tree with all layers from scratch.
2. Read all existing source files.
3. Extract each responsibility type into the appropriate layer.
4. Rewrite entry point (`app.py` / `app.js`) as composition root only.
5. Move any configuration out of source files into `config/settings.py` and `.env.example`.
6. Update all internal imports after moving files.
7. Delete or archive original flat files once new structure is verified.

Example: `code-smells-project` (4 flat files → full `src/` structure).

### PARTIAL-IMPROVE Behavior

Applied when: project already has partial layer separation.

Actions:
1. **Preserve** existing layers that are correctly structured.
2. **Add** missing layers (e.g., add `middlewares/` and `config/` if absent).
3. **Extract** business logic that is in the wrong layer (e.g., service logic in `routes/`).
4. **Fix** security issues in existing files (hardcoded secrets, insecure hashing).
5. **Do NOT** rename or move files that are correctly placed.
6. **Do NOT** remove existing dependencies unless clearly broken.
7. Update only what needs changing based on findings from Phase 2.

Example: `task-manager-api` (has `models/`, `routes/`, `services/`, `utils/` — add `middlewares/`, `schemas/`, fix security issues, centralize service layer logic).

---

## Mandatory Refactoring Actions (Both Strategies)

Regardless of strategy, always apply these when the corresponding finding was detected:

| Finding | Action |
|---|---|
| Hardcoded SECRET_KEY | Move to `.env` + load via `os.getenv()` / `process.env`. Create `.env.example`. |
| Hardcoded credentials | Same as above |
| `debug=True` in source | Replace with `debug=os.getenv('FLASK_DEBUG','false').lower()=='true'` |
| SQL injection | Replace with parameterized queries (see playbook) |
| Insecure password hash | Replace with `werkzeug.security` or `bcrypt` (see playbook) |
| No error handler | Add centralized error handler in `middlewares/` |
| Sensitive endpoint without auth | Add auth middleware/decorator stub with clear TODO comment |

---

## Import Update Protocol

After every file move or rename, run:

```bash
# Python: find all imports referencing old module name
grep -Rn "from <old_module_name> import\|import <old_module_name>" . --include="*.py"

# Node: find all requires referencing old file
grep -Rn "require.*<old_file_name>" . --include="*.js" | grep -v node_modules
```

Update every reference found before proceeding to the next file move.

---

## Phase 3 Output Format

After refactoring completes and smoke test passes, print:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Strategy: {Monolith-Rewrite | Partial-Improve}

## New Project Structure
{ascii tree of actual new directory structure}

## Changes Made
- {bullet list of files created, moved, or modified}

## Security Fixes Applied
- {bullet list of security issues resolved}

## Validation
{smoke test results block}
================================
```
