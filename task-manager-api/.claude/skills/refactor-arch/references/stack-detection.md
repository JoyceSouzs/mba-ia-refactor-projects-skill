# Stack Detection Heuristics

Reference for Phase 1. Apply checks in the order listed — first match wins for each category.

---

## Step 1: Detect Runtime / Language

Run in the project root:

```bash
ls -la | grep -E "requirements.txt|pyproject.toml|Pipfile|package.json|go.mod|pom.xml|build.gradle|Cargo.toml"
```

| File found | Language | Action |
|---|---|---|
| `requirements.txt` or `pyproject.toml` or `Pipfile` | Python | Continue to Step 2a |
| `package.json` | Node.js | Continue to Step 2b |
| `go.mod` | Go | Report: "Stack not supported by this skill. Aborting." |
| `pom.xml` or `build.gradle` | Java | Report: "Stack not supported by this skill. Aborting." |
| Both Python and Node manifests | Ambiguous | Use the one with more source files in root: `find . -maxdepth 2 -name "*.py" | wc -l` vs `find . -maxdepth 2 -name "*.js" | grep -v node_modules | wc -l` |

---

## Step 2a: Detect Framework (Python)

```bash
cat requirements.txt 2>/dev/null || cat pyproject.toml 2>/dev/null || cat Pipfile 2>/dev/null
```

| Dependency found | Framework | Extract version |
|---|---|---|
| `flask` | Flask | `grep -i "flask==" requirements.txt` |
| `fastapi` | FastAPI | `grep -i "fastapi==" requirements.txt` |
| `django` | Django | `grep -i "django==" requirements.txt` |
| `tornado` | Tornado | `grep -i "tornado==" requirements.txt` |
| None of the above | Unknown Python framework | Report as "Python (framework unknown)" |

Also detect ORM:
```bash
grep -iE "sqlalchemy|flask-sqlalchemy|peewee|tortoise" requirements.txt
```

---

## Step 2b: Detect Framework (Node.js)

```bash
cat package.json
```

Check `dependencies` field:

| Dependency found | Framework |
|---|---|
| `express` | Express.js |
| `fastify` | Fastify |
| `@nestjs/core` | NestJS |
| `koa` | Koa |
| None | Unknown Node framework |

Extract version: `node -e "console.log(require('./package.json').dependencies.express)"` or read from `package.json` directly.

Also detect database client:
```bash
# In package.json dependencies:
grep -E "sqlite3|better-sqlite3|pg|mysql|mongoose|sequelize|prisma" package.json
```

---

## Step 3: Detect Database

```bash
# Python: look in requirements.txt
grep -iE "sqlite3|psycopg2|pymongo|mysql-connector|flask-sqlalchemy|peewee" requirements.txt 2>/dev/null

# Node: look in package.json
grep -iE "sqlite3|better-sqlite3|pg|mysql|mongoose|sequelize|prisma" package.json 2>/dev/null

# Look for .db or .sqlite files
find . -name "*.db" -o -name "*.sqlite" 2>/dev/null | grep -v node_modules | grep -v .git

# Infer tables from SQL CREATE statements
grep -RnE "CREATE TABLE\s+(\w+)" . --include="*.py" --include="*.js" --include="*.sql" | grep -v node_modules
```

Map to database type:
- `sqlite3` / `better-sqlite3` / `.db` file → SQLite
- `psycopg2` / `pg` → PostgreSQL
- `mysql-connector` / `mysql` → MySQL
- `pymongo` / `mongoose` → MongoDB

---

## Step 4: Map All Endpoints

This list is reused in Phase 3 for smoke testing.

**Flask (Python):**
```bash
grep -RnE "@\w+\.route\s*\(['\"]([^'\"]+)" . --include="*.py" | grep -v node_modules | grep -v ".pyc"
grep -RnE "app\.add_url_rule\s*\(['\"]([^'\"]+)" . --include="*.py"
```

**Express (Node):**
```bash
grep -RnE "app\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)" . --include="*.js" | grep -v node_modules
grep -RnE "router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)" . --include="*.js" | grep -v node_modules
```

Record: HTTP method + path + file:line. This is the **endpoint inventory**.

---

## Step 5: Infer Business Domain

From the combination of:
1. Table names (Step 3)
2. Endpoint paths (Step 4)
3. Model/entity names: `find . -name "*model*" -o -name "*entity*" | grep -v node_modules`

| Tables/endpoints contain | Domain |
|---|---|
| `produtos`, `pedidos`, `usuarios`, `/produtos`, `/pedidos` | E-commerce API |
| `courses`, `enrollments`, `payments`, `/checkout`, `/enroll` | LMS / Learning Platform |
| `tasks`, `categories`, `/tasks`, `/reports` | Task Management API |
| `users`, `posts`, `comments` | Blog / CMS |

If unclear, describe as: "API managing [list of main entities]".

---

## Step 6: Determine Current Architecture

```bash
# Count known layer directories at root level
ls -d */ 2>/dev/null | grep -E "^(models|routes|controllers|views|services|middlewares|config|src)/$"

# Count source files at root level (excluding entry points and config)
find . -maxdepth 1 -name "*.py" -o -maxdepth 1 -name "*.js" 2>/dev/null | grep -v node_modules | grep -vE "app\.(py|js)|seed\.(py|js)|database\.(py|js)|config\.(py|js)"
```

**Decision rule:**
- ≥ 2 known layer directories **AND** ≤ 3 source files at root → **Partially Organized** (report layers present)
- Otherwise → **Monolithic** (report file count and what's mixed)

---

## Phase 1 Output Format

Print exactly this ASCII box after completing all steps:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <Python | Node.js>
Framework:     <Flask X.Y.Z | Express X.Y.Z | ...>
Dependencies:  <comma-separated key deps>
Domain:        <inferred domain description>
Architecture:  <Monolithic — N files, no layer separation | Partially Organized — layers: X, Y, Z>
Source files:  <N files analyzed>
DB tables:     <comma-separated table names | SQLite in-memory>
================================
```

List of endpoints (printed below the box):
```
Endpoints mapped:
  GET    /path1
  POST   /path2
  ...
```

Save the endpoint list — it is reused in Phase 3 smoke testing.
