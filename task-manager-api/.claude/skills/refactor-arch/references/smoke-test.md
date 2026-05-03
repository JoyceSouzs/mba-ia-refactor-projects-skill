# Smoke Test Procedure

Reference for Phase 3 validation. Execute after refactoring is complete. The application must pass all checks before Phase 3 can be declared successful.

---

## Prerequisites by Stack

### Python / Flask

1. **Detect virtualenv:**
```bash
# Check for existing venv
ls -d .venv venv env 2>/dev/null | head -1
```

2. **Create if absent:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Initialize database (if seed script exists):**
```bash
ls seed.py 2>/dev/null && python3 seed.py
```

### Node.js / Express

1. **Check for node_modules:**
```bash
ls node_modules 2>/dev/null || npm install --no-audit --no-fund
```

---

## Port Detection

Check if the default port is free before starting the server:

```bash
DEFAULT_PORT=5000  # or 3000 for Node
lsof -ti:$DEFAULT_PORT 2>/dev/null
```

If the port is occupied, use `PORT=$((DEFAULT_PORT + 1000))` as fallback. Pass the port via environment variable.

---

## Boot Server in Background

### Python / Flask
```bash
# Activate venv first if not already active
source .venv/bin/activate 2>/dev/null || true

# Start server
PORT=5000 python3 app.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
```

### Node.js / Express
```bash
PORT=3000 node src/app.js &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
```

---

## Wait for Server Ready

Poll until the server responds or timeout (10 seconds):

```bash
PORT=5000  # adjust to actual port
MAX_WAIT=10
COUNT=0

while [ $COUNT -lt $MAX_WAIT ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 1 http://localhost:$PORT/ 2>/dev/null)
    if [ "$STATUS" != "000" ] && [ -n "$STATUS" ]; then
        echo "Server is up (status: $STATUS)"
        break
    fi
    COUNT=$((COUNT + 1))
    sleep 1
done

if [ $COUNT -eq $MAX_WAIT ]; then
    echo "TIMEOUT: Server did not start within ${MAX_WAIT}s"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
```

---

## Smoke Test Endpoints

For each endpoint from the Phase 1 inventory:

```bash
# GET endpoints
curl -s -o /dev/null -w "%{http_code}" -m 5 http://localhost:$PORT/path

# POST endpoints (minimal payload)
curl -s -o /dev/null -w "%{http_code}" -m 5 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:$PORT/path
```

### Skip / Handle with care

**Skip entirely** (do not test these in smoke runs):
- `POST /admin/reset-db` — would delete all data
- `POST /admin/query` — would execute arbitrary SQL

**Test with safe payload only:**
- `DELETE /users/:id` — use a non-existent ID: `DELETE /users/99999` (expect 404, not 500)

### In-memory DB projects (e.g., ecommerce-api-legacy)

When the database is `:memory:` (destroyed on server restart), follow the create-then-read pattern:

```bash
# 1. Create a resource first
RESULT=$(curl -s -m 5 -X POST -H "Content-Type: application/json" \
  -d '{"title":"Test Course","price":99.90,"email":"test@test.com","card":"4111111111111111","courseId":1}' \
  http://localhost:$PORT/api/checkout)
echo "POST result: $RESULT"

# 2. Then test read endpoints
curl -s -o /dev/null -w "%{http_code}" -m 5 http://localhost:$PORT/api/admin/financial-report
```

---

## Acceptable Response Codes

| HTTP Status | Interpretation | Pass/Fail |
|---|---|---|
| 2xx | Success | PASS |
| 400 | Bad request (endpoint exists, rejected empty payload) | PASS |
| 401 | Unauthorized (endpoint exists, auth required — expected after adding auth middleware) | PASS |
| 404 | Not found (route returns 404 for missing resource — valid) | PASS |
| 405 | Method not allowed | PASS |
| 000 | Connection refused / timeout | **FAIL** |
| 5xx | Server error (application crashed) | **FAIL** |

---

## Teardown

```bash
# Kill server by saved PID
kill $SERVER_PID 2>/dev/null
sleep 1

# Verify port is free
if lsof -ti:$PORT 2>/dev/null | grep -q .; then
    echo "Port still occupied, forcing kill..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
fi
echo "Server stopped."
```

---

## Result Format

Print results in this format:

```
## Smoke Test Results
  ✓ GET  /                     → 200
  ✓ GET  /health               → 200
  ✓ GET  /produtos             → 200
  ✓ POST /produtos             → 400 (empty payload rejected correctly)
  ✓ GET  /produtos/1           → 404 (no seed data, valid 404)
  ✗ GET  /relatorios/vendas    → 500 (FAIL: KeyError in relatorio_controller.py:42)

Passed: 5/6 endpoints
```

If any endpoint returns 5xx or times out, report the failure detail and do not mark Phase 3 as complete.

---

## Failure Recovery

If the smoke test fails:

1. Read the server log output (check for Python traceback or Node.js error).
2. Identify the file and line number causing the crash.
3. Fix the issue (usually a broken import, missing variable, or wrong function signature).
4. Restart and re-run smoke test.
5. Only after all endpoints pass, print the Phase 3 completion box.

**Common failures and fixes:**

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | Import path broken after file move | Update `from X import Y` — run `grep -Rn "from <old_module>"` |
| `AttributeError: module has no attribute X` | Function moved but import not updated | Update import to point to new module |
| `OperationalError: no such table` | DB not initialized | Run `seed.py` or add `db.create_all()` to entry point |
| `Address already in use` | Previous server still running | `lsof -ti:PORT \| xargs kill -9` |
| `TypeError: X() takes N arguments` | Function signature changed | Check the function definition in new file |
| Server starts but returns 500 on all routes | Blueprint/router not registered | Check entry point — verify `app.register_blueprint()` or `app.use()` calls |
