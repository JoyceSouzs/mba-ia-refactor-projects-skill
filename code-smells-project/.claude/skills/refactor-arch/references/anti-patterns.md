# Anti-patterns Catalog

Reference for Phase 2 audit. For each pattern: run the detection signal, then **confirm by reading the file** before adding to the report. Do not report based on grep alone.

---

## AP-01 — SQL Injection via String Concatenation
**Severity:** CRITICAL

**Detection (Python + Node):**
```bash
grep -RnE "(execute|cursor\.execute|db\.run|db\.get|db\.all)\s*\(.*['\"].*\+" . --include="*.py" --include="*.js"
grep -RnE 'f".*SELECT|f".*INSERT|f".*UPDATE|f".*DELETE|f".*WHERE' . --include="*.py"
grep -RnE '"SELECT.*"\s*\+|"INSERT.*"\s*\+|"UPDATE.*"\s*\+|"WHERE.*"\s*\+' . --include="*.py" --include="*.js"
```

**Description:** SQL queries built via string concatenation or f-strings with user-controlled variables, instead of parameterized placeholders.

**Impact:** Attacker can extract, modify, or delete any data; may escalate to RCE.

**Recommendation:** Replace all string concatenation in SQL with `?` placeholders (sqlite3) or `%s` (psycopg2). Use ORM query builders.

**Found in projects:**
- `code-smells-project/models.py` — virtually every function (lines 28, 48, 92, 109, 127, 224, 291-297)

---

## AP-02 — Hardcoded Credentials / Secrets
**Severity:** CRITICAL

**Detection (Python + Node):**
```bash
grep -RniE "(secret_key|api[_-]?key|gateway[_-]?key|smtp[_-]?pass|db[_-]?pass|payment.*key)\s*[=:]\s*['\"][^'\"]{6,}" . --include="*.py" --include="*.js"
grep -RniE "password\s*=\s*['\"][^'\"]{4,}" . --include="*.py" --include="*.js"
grep -RniE "(token|senha|passwd)\s*[=:]\s*['\"][^'\"]{4,}" . --include="*.py" --include="*.js"
```

**Description:** Secrets (API keys, passwords, secret keys) hardcoded directly in source files visible in version control.

**Impact:** Anyone with repository access can use the credentials; session forgery, payment fraud, data breach.

**Recommendation:** Move all secrets to environment variables using `os.getenv()` (Python) or `process.env.VAR` (Node). Create `.env.example` with placeholder values. Add `.env` to `.gitignore`.

**Found in projects:**
- `code-smells-project/app.py:7` — `SECRET_KEY = "minha-chave-super-secreta-123"`
- `ecommerce-api-legacy/src/utils.js:2-6` — `dbPass`, `paymentGatewayKey`, `smtpUser`
- `task-manager-api/app.py:13` — `SECRET_KEY = 'super-secret-key-123'`
- `task-manager-api/services/notification_service.py:9-10` — Gmail credentials

---

## AP-03 — God Class / God File
**Severity:** CRITICAL

**Detection:**
```bash
# Find largest files
find . -name "*.py" -o -name "*.js" | grep -v node_modules | grep -v .git | xargs wc -l 2>/dev/null | sort -rn | head -10

# Count functions/methods per file
grep -c "def \|function \|=>\s*{" <file> 2>/dev/null
```

**Heuristic:** A file qualifies as God Class if it has **> 200 lines AND > 6 public functions/methods** AND mixes multiple responsibilities (routing + business logic + data access + validation).

**Description:** Single file or class that handles multiple unrelated domains, violating the Single Responsibility Principle.

**Impact:** Impossible to test in isolation; any change risks breaking unrelated functionality; onboarding is extremely difficult.

**Recommendation:** Split by domain into separate model/controller/service files. Each file should have one clear responsibility.

**Found in projects:**
- `code-smells-project/models.py` — 314 lines, 14 functions, handles 4 domains (produtos, usuarios, pedidos, relatórios)
- `ecommerce-api-legacy/src/AppManager.js` — 141 lines, handles DB init, routing, checkout, reports, user management

---

## AP-04 — Insecure Password Hashing (MD5 / Base64 / Plaintext)
**Severity:** HIGH

**Detection (Python + Node):**
```bash
grep -RniE "hashlib\.(md5|sha1|sha256)\s*\(" . --include="*.py"
grep -RniE "Buffer\.from\(.*base64|\.toString\('base64'\)" . --include="*.js"
grep -RniE "btoa\s*\(" . --include="*.js"
# Also check for plaintext storage: look for direct assignment without any hash function
grep -RnE "senha\s*=\s*\w+|password\s*=\s*\w+[^_]" . --include="*.py" --include="*.js" | grep -v "hash\|generate\|encrypt\|bcrypt\|argon"
```

**Description:** Passwords stored using broken algorithms (MD5, SHA1, Base64 encoding) or in plaintext. These can be reversed or cracked with rainbow tables instantly.

**Impact:** Any database breach exposes all user passwords immediately.

**Recommendation:** Use `werkzeug.security.generate_password_hash()` / `check_password_hash()` (Python/Flask), `bcrypt` (Node), or `argon2`. Add salt automatically via these libraries.

**Found in projects:**
- `code-smells-project/models.py:127-128` — passwords stored in plaintext via SQL INSERT
- `ecommerce-api-legacy/src/utils.js:17-23` — fake hash using Base64 repetition (`badCrypto()`)
- `task-manager-api/models/user.py:29` — `hashlib.md5(pwd.encode()).hexdigest()`

---

## AP-05 — Fat Controller / Business Logic in Routes
**Severity:** HIGH

**Detection:**
```bash
# Find large route/controller files
find . \( -name "*route*" -o -name "*controller*" -o -name "*app.py" -o -name "app.js" \) | grep -v node_modules | xargs wc -l 2>/dev/null | sort -rn

# Find queries inside route handlers
grep -RnE "(cursor\.execute|db\.run|db\.get|\.query\.(filter|get|all))" routes/ controllers/ --include="*.py" --include="*.js" 2>/dev/null
grep -RnE "(cursor\.execute|db\.run|db\.get|\.query\.(filter|get|all))" . --include="*.py" --include="*.js" 2>/dev/null | grep -v "model\|service\|repository"
```

**Description:** Business logic, database queries, and validation mixed directly into route handlers. Controllers become bloated and impossible to reuse or test.

**Impact:** Cannot reuse business logic from CLI, jobs, or webhooks; unit tests require full HTTP stack; changes cascade across unrelated code.

**Recommendation:** Extract business logic into a Service layer (`services/<domain>_service.py` or `services/<domain>Service.js`). Controllers/routes only handle HTTP concerns (parse request, call service, format response).

**Found in projects:**
- `code-smells-project/controllers.py` — validation duplicated in create/update functions (lines 24-96)
- `task-manager-api/routes/task_routes.py` — overdue calculation inline at lines 30-58, N+1 queries inline at 41-57
- `ecommerce-api-legacy/src/AppManager.js:28-78` — entire checkout flow in one route handler

---

## AP-06 — Callback Hell / Missing Async-Await
**Severity:** HIGH

**Detection (Node only):**
```bash
grep -RnE "\.(run|get|all|each)\s*\([^)]*,\s*function\s*\(" . --include="*.js" | grep -v node_modules
# Count nesting depth by looking for consecutive closing parentheses
grep -RnE "^\s{12,}}" . --include="*.js" | grep -v node_modules
```

**Description:** Deeply nested callbacks (Pyramid of Doom) creating brittle, unreadable code with inconsistent error handling and potential race conditions.

**Impact:** Bugs introduced by missed error paths; ordering of async operations not guaranteed; impossible to add error handling consistently.

**Recommendation:** Promisify sqlite3 calls or use `better-sqlite3` (synchronous). Convert all callbacks to `async/await`. Use try/catch blocks.

**Found in projects:**
- `ecommerce-api-legacy/src/AppManager.js:28-78` — 5 levels of nesting in checkout handler
- `ecommerce-api-legacy/src/AppManager.js:80-129` — manual counter-based async coordination (`coursesPending`, `enrPending`)

---

## AP-07 — Sensitive Endpoints Without Authentication
**Severity:** HIGH

**Detection:**
```bash
# Find admin/destructive endpoints
grep -RniE "@\w+\.route\s*\(.*admin|app\.(get|post|put|delete|patch)\s*\(.*admin" . --include="*.py" --include="*.js"
grep -RniE "@\w+\.route\s*\(.*reset|DELETE.*users" . --include="*.py" --include="*.js"

# Check if auth decorator/middleware exists near them
grep -RnE "@login_required|@auth\.|authenticate|requireAuth|verifyToken" . --include="*.py" --include="*.js"
```

**Description:** Admin, destructive, or privileged endpoints accessible without any authentication or authorization check.

**Impact:** Any anonymous user can reset database, run arbitrary SQL, delete users, or access financial reports.

**Recommendation:** Add authentication middleware (Flask decorator `@login_required`, Express middleware `verifyToken`). For admin endpoints, additionally verify admin role.

**Found in projects:**
- `code-smells-project/app.py:47-57` — `POST /admin/reset-db` with no auth
- `code-smells-project/app.py:59-78` — `POST /admin/query` accepts arbitrary SQL with no auth
- `ecommerce-api-legacy/src/AppManager.js:80` — `GET /api/admin/financial-report` with no auth
- `task-manager-api/routes/` — all endpoints have no authentication middleware

---

## AP-08 — N+1 Query Problem
**Severity:** MEDIUM

**Detection:**
```bash
# Find database queries inside loops (Python)
grep -RnB3 "for .* in " . --include="*.py" | grep -E "(cursor\.execute|\.query\.(get|filter|first|all))"

# Find database queries inside loops (Node)
grep -RnB3 "for\s*\(|\.forEach\s*\(" . --include="*.js" | grep -E "(db\.(run|get|all)|\.query\s*\()"
```

**Description:** Database query executed inside a loop, causing N additional queries for N items fetched in the outer query.

**Impact:** 100 items → 200+ queries; response times grow linearly with data; brings databases to their knees under load.

**Recommendation:** Use `JOIN` (raw SQL) or SQLAlchemy `joinedload()`/`subqueryload()` to load related data in one query.

**Found in projects:**
- `code-smells-project/models.py:187-200` — fetches itens_pedido and produto for each pedido in loop (2 extra queries per pedido)
- `task-manager-api/routes/task_routes.py:41-57` — fetches user and category for each task in loop
- `task-manager-api/routes/report_routes.py:53-68` — fetches tasks for each user in loop

---

## AP-09 — Missing or Duplicated Input Validation
**Severity:** MEDIUM

**Detection:**
```bash
# Find duplicated validation patterns across files
grep -RnE "if not (data\.get|req\.body\.|dados\.get)" . --include="*.py" --include="*.js"

# Find routes with no validation at all
grep -RnE "request\.get_json\(\)|req\.body" . --include="*.py" --include="*.js" | grep -v "validate\|schema\|joi\|marshmallow"
```

**Description:** Input validation either missing entirely (any payload accepted) or duplicated across multiple route handlers with subtle differences that create inconsistent behavior.

**Impact:** Invalid data corrupts database; duplicated validation drifts out of sync; security rules enforced inconsistently.

**Recommendation:** Centralize validation in reusable schema validators (Marshmallow for Python, Joi for Node). Route handlers call validator, not duplicate checks.

**Found in projects:**
- `code-smells-project/controllers.py:30-54` vs `74-90` — same 6 validations for create vs update produto
- `task-manager-api/routes/task_routes.py:96-114` vs `166-184` — same validations for create vs update task
- `ecommerce-api-legacy/src/AppManager.js` — card validation checks only first digit (`card[0] === '4'`)

---

## AP-10 — Mutable Global State
**Severity:** MEDIUM

**Detection:**
```bash
# Python module-level globals
grep -RnE "^[a-z_]+\s*=\s*(None|\{\}|\[\]|0)" . --include="*.py" | grep -v "app\s*=\|db\s*="

# Node module-level mutable globals
grep -RnE "^(let|var)\s+\w+\s*=\s*(\{\}|\[\]|0|null)" . --include="*.js" | grep -v node_modules

# Python 'global' keyword usage
grep -RnE "^\s+global\s+\w+" . --include="*.py"
```

**Description:** Module-level mutable variables used as implicit singletons, shared across requests without synchronization.

**Impact:** Race conditions under concurrent requests; non-deterministic bugs; stale cache serving wrong data to wrong users.

**Recommendation:** Use request-scoped context (Flask `g`, Express `res.locals`) or dependency injection. For database connections, use connection pooling.

**Found in projects:**
- `code-smells-project/database.py:4` — `db_connection = None` as module global with `check_same_thread=False`
- `ecommerce-api-legacy/src/utils.js:9-10` — `globalCache = {}` and `totalRevenue = 0` as module globals

---

## AP-11 — Deprecated APIs
**Severity:** LOW (escalate to MEDIUM if `debug=True` in production)

**Detection:**
```bash
# Python deprecated patterns
grep -RnE "debug\s*=\s*True" . --include="*.py"
grep -RnE "datetime\.utcnow\s*\(\)" . --include="*.py"
grep -RnE "app\.run\s*\(.*debug" . --include="*.py"

# Node deprecated patterns  
grep -RnE "sqlite3\.verbose\s*\(\)" . --include="*.js" | grep -v node_modules
grep -RnE "new\s+Buffer\s*\(" . --include="*.js" | grep -v node_modules
grep -RnE "\.on\s*\(\s*'error'" . --include="*.js" | grep -v node_modules
```

**Description:** Use of APIs deprecated in current runtime versions, or dangerous development-only flags left enabled in production code.

**Impact:** `debug=True` exposes interactive debugger and stack traces remotely; `datetime.utcnow()` deprecated since Python 3.12 (returns naive datetime); `sqlite3.verbose()` is a no-op in modern sqlite3.

**Recommendation:**
- Replace `app.run(debug=True)` with environment variable: `debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'`
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Remove `sqlite3.verbose()` (no-op); switch to promise-based sqlite API

**Found in projects:**
- `code-smells-project/app.py:8,88` — `app.config["DEBUG"] = True` and `app.run(debug=True)`
- `task-manager-api/app.py:34` — `app.run(debug=True)`
- `ecommerce-api-legacy/src/AppManager.js:1` — `sqlite3.verbose()`

---

## AP-12 — Magic Numbers and Hardcoded String Lists
**Severity:** LOW

**Detection:**
```bash
# Hardcoded port numbers
grep -RnE "\b(5000|3000|8000|8080|3306|5432)\b" . --include="*.py" --include="*.js" | grep -v node_modules | grep -v "#\|//\|comment"

# Repeated status/priority lists
grep -RnE "(\[|,)\s*'(pending|in_progress|done|cancelled|PAID|DENIED)'" . --include="*.py" --include="*.js"

# Hardcoded business thresholds
grep -RnE "\b(10000|5000|1000|0\.1|0\.05|0\.02)\b" . --include="*.py" | grep -v "migration\|test"
```

**Description:** Literal numbers and duplicated string enumerations scattered across the codebase with no named constant.

**Impact:** Changing a value requires searching all occurrences; easy to miss one; no documentation of why the value exists.

**Recommendation:** Extract to a `config/constants.py` or `config/constants.js` file. Use Enum classes for status/priority lists.

**Found in projects:**
- `code-smells-project/app.py:88` — port `5000` hardcoded
- `code-smells-project/models.py:256-262` — discount thresholds `10000`, `5000`, `1000` with `0.1`, `0.05`, `0.02`
- `task-manager-api/routes/task_routes.py` — `['pending', 'in_progress', 'done', 'cancelled']` repeated in multiple routes
- `task-manager-api/routes/task_routes.py:96,100,113` — `len(title) < 3`, `> 200`, `priority < 1`, `priority > 5`
