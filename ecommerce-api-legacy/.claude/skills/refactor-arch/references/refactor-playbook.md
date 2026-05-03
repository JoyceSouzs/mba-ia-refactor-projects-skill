# Refactoring Playbook

Ten concrete transformation patterns. Each has Before/After code examples and notes on applying safely. Reference anti-pattern IDs from `anti-patterns.md`.

---

## T-01 — SQL Concatenation → Parameterized Query
**Applies to:** AP-01 (CRITICAL)

### Before (Python)
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES ('" +
    nome + "', '" + email + "', '" + senha + "')"
)
# Search with f-string
cursor.execute(f"SELECT * FROM produtos WHERE nome LIKE '%{termo}%'")
```

### After (Python — sqlite3)
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
    (nome, email, senha)
)
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))
```

### After (Python — SQLAlchemy ORM)
```python
produto = Produto.query.get(id)
novo = Produto(nome=nome, descricao=descricao, preco=preco)
db.session.add(novo)
db.session.commit()
```

**Notes:** Use `?` for sqlite3. Use `%s` for psycopg2 (PostgreSQL). Use ORM when available — eliminates SQL injection by design. For complex search queries with dynamic filters, build the WHERE clause with `?` placeholders and a list, never string concatenation.

---

## T-02 — Hardcoded Secrets → Environment Variables
**Applies to:** AP-02 (CRITICAL)

### Before (Python)
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
EMAIL_PASSWORD = 'senha123'
PAYMENT_KEY = 'pk_live_1234567890abcdef'
```

### After (Python)
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-only-insecure-key')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
PAYMENT_KEY = os.getenv('PAYMENT_GATEWAY_KEY')
```

### Before (Node.js)
```javascript
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef"
};
```

### After (Node.js)
```javascript
require('dotenv').config();
const config = {
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY
};
```

**Also create `.env.example`:**
```
SECRET_KEY=your-secret-key-here
EMAIL_PASSWORD=your-email-password
PAYMENT_GATEWAY_KEY=pk_live_your_key_here
```

**Notes:** Add `.env` to `.gitignore`. Never commit real credentials. The `load_dotenv()` call belongs in `config/settings.py`, not in the entry point. `python-dotenv` is a common Flask dependency — add to `requirements.txt` if not present.

---

## T-03 — God File → Domain Split
**Applies to:** AP-03 (CRITICAL)

### Before
```python
# models.py — 314 lines mixing 4 domains
def get_todos_produtos(): ...
def criar_produto(): ...
def get_todos_usuarios(): ...
def criar_usuario(): ...
def autenticar_usuario(): ...
def criar_pedido(): ...
def get_relatorio_vendas(): ...
```

### After
```
src/
├── models/
│   ├── produto_model.py    # get_produto, get_todos_produtos, criar_produto, ...
│   ├── usuario_model.py    # get_usuario, criar_usuario, autenticar_usuario, ...
│   ├── pedido_model.py     # criar_pedido, get_pedidos_usuario, ...
│   └── relatorio_model.py  # get_relatorio_vendas, ...
```

```python
# src/models/produto_model.py
from config.settings import get_db

def get_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    return cursor.fetchone()
```

**Notes:** Extract one domain per file. Keep function names identical — only the module path changes. Update all imports after splitting. If using SQLAlchemy, models also carry the ORM class definition.

---

## T-04 — Insecure Hash → bcrypt / werkzeug
**Applies to:** AP-04 (HIGH)

### Before (Python — MD5)
```python
import hashlib
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### After (Python — werkzeug, included with Flask)
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

### Before (Node.js — fake Base64)
```javascript
function badCrypto(str) {
    let result = Buffer.from(str).toString('base64');
    for (let i = 0; i < 10000; i++) {
        result = Buffer.from(result).toString('base64');
    }
    return result.substring(0, 10);
}
```

### After (Node.js — bcrypt)
```javascript
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 12;

async function hashPassword(password) {
    return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password, hash) {
    return bcrypt.compare(password, hash);
}
```

**Notes:** Existing MD5/Base64 hashes **cannot** be automatically migrated — they are not reversible. Add a note in the refactoring output: "Existing password hashes are incompatible with the new algorithm. Users will need to reset their passwords." For Node, add `bcrypt` to `package.json`.

---

## T-05 — Fat Controller → Service Layer
**Applies to:** AP-05 (HIGH)

### Before (route with business logic)
```python
@app.route('/tasks', methods=['POST'])
def criar_task():
    dados = request.get_json()
    if not dados.get('title'):
        return jsonify({'error': 'Título obrigatório'}), 400
    if len(dados['title']) < 3:
        return jsonify({'error': 'Título muito curto'}), 400
    if dados.get('priority') and (dados['priority'] < 1 or dados['priority'] > 5):
        return jsonify({'error': 'Prioridade inválida'}), 400
    # ... more validation ...
    task = Task(title=dados['title'], priority=dados.get('priority', 3))
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201
```

### After (thin route + service)
```python
# routes/task_routes.py
from controllers.task_controller import TaskController

@task_bp.route('/tasks', methods=['POST'])
def criar_task():
    dados = request.get_json()
    result, status = TaskController.create(dados)
    return jsonify(result), status

# controllers/task_controller.py
from models.task_model import TaskModel

class TaskController:
    VALID_PRIORITIES = range(1, 6)

    @classmethod
    def create(cls, dados):
        errors = cls._validate_create(dados)
        if errors:
            return {'error': errors}, 400
        task = TaskModel.create(dados['title'], dados.get('priority', 3))
        return task, 201

    @classmethod
    def _validate_create(cls, dados):
        if not dados.get('title'):
            return 'Título obrigatório'
        if len(dados['title']) < 3:
            return 'Título muito curto'
        if dados.get('priority') and dados['priority'] not in cls.VALID_PRIORITIES:
            return 'Prioridade deve ser entre 1 e 5'
        return None
```

**Notes:** The route only parses the request and formats the response. All validation and business rules move to the controller. The model only handles persistence. This makes the controller independently unit-testable.

---

## T-06 — Callback Hell → Async/Await (Node.js)
**Applies to:** AP-06 (HIGH)

### Before
```javascript
app.post('/api/checkout', (req, res) => {
    const { courseId, email } = req.body;
    db.get('SELECT * FROM courses WHERE id = ?', [courseId], (err, course) => {
        if (err) return res.status(500).send('DB Error');
        if (!course) return res.status(404).send('Course not found');
        db.get('SELECT * FROM users WHERE email = ?', [email], (err, user) => {
            if (err) return res.status(500).send('DB Error');
            // ... 3 more nesting levels
        });
    });
});
```

### After (with promisified db)
```javascript
// src/config/database.js
const sqlite3 = require('sqlite3');
const { open } = require('sqlite');  // sqlite wrapper adds promise support

async function getDb() {
    return open({ filename: ':memory:', driver: sqlite3.Database });
}

// src/controllers/checkoutController.js
const { getDb } = require('../config/database');

async function processCheckout(courseId, email, card) {
    const db = await getDb();
    const course = await db.get('SELECT * FROM courses WHERE id = ?', [courseId]);
    if (!course) throw new Error('Course not found');

    let user = await db.get('SELECT * FROM users WHERE email = ?', [email]);
    if (!user) {
        await db.run('INSERT INTO users (email) VALUES (?)', [email]);
        user = await db.get('SELECT * FROM users WHERE email = ?', [email]);
    }
    // ... flat, readable flow
    return { userId: user.id, courseId };
}

// src/routes/checkoutRoutes.js
router.post('/checkout', async (req, res, next) => {
    try {
        const result = await processCheckout(req.body.courseId, req.body.email, req.body.card);
        res.json({ success: true, ...result });
    } catch (err) {
        next(err);  // passes to error handler middleware
    }
});
```

**Notes:** Install `sqlite` wrapper: `npm install sqlite`. It wraps `sqlite3` with Promise-based API. All route handlers become `async` and use `try/catch`. Errors flow to centralized error handler middleware.

---

## T-07 — Unprotected Endpoint → Auth Middleware
**Applies to:** AP-07 (HIGH)

### Before (Flask)
```python
@app.route('/admin/reset-db', methods=['POST'])
def reset_database():
    # No authentication check!
    db.execute("DELETE FROM produtos")
    db.commit()
    return jsonify({'message': 'DB reset'})
```

### After (Flask)
```python
# middlewares/auth.py
from functools import wraps
from flask import request, jsonify
import os

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or token != os.getenv('ADMIN_TOKEN'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO: implement proper JWT validation and role check
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# routes/admin_routes.py
from middlewares.auth import require_admin

@admin_bp.route('/reset-db', methods=['POST'])
@require_admin
def reset_database():
    ...
```

### After (Express)
```javascript
// middlewares/auth.js
function requireAuth(req, res, next) {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Unauthorized' });
    // TODO: implement proper JWT validation
    next();
}

// routes/adminRoutes.js
router.delete('/users/:id', requireAuth, userController.deleteUser);
```

**Notes:** This creates a stub that enforces the presence of a token. Add TODO comment for full JWT implementation. The important architectural change is that auth logic is in middleware, not scattered in route handlers.

---

## T-08 — N+1 Query → JOIN or Eager Loading
**Applies to:** AP-08 (MEDIUM)

### Before (Python — raw sqlite3 with N+1)
```python
cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
pedidos = cursor.fetchall()
for pedido in pedidos:
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

### After (Python — raw sqlite3 with JOIN)
```python
cursor.execute("""
    SELECT p.*, ip.quantidade, ip.preco_unitario, pr.nome as produto_nome
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
    WHERE p.usuario_id = ?
""", (usuario_id,))
rows = cursor.fetchall()
# Group into nested structure in Python
pedidos = {}
for row in rows:
    pid = row["id"]
    if pid not in pedidos:
        pedidos[pid] = dict(row)
        pedidos[pid]["itens"] = []
    pedidos[pid]["itens"].append({"produto_nome": row["produto_nome"], ...})
```

### Before (Python — SQLAlchemy with N+1)
```python
tasks = Task.query.all()
for t in tasks:
    user = User.query.get(t.user_id)   # N extra queries
    cat = Category.query.get(t.category_id)  # N more queries
```

### After (Python — SQLAlchemy with joinedload)
```python
from sqlalchemy.orm import joinedload

tasks = Task.query.options(
    joinedload(Task.user),
    joinedload(Task.category)
).all()
# user and category now loaded in 1-3 queries total
for t in tasks:
    user = t.user    # no additional query
    cat = t.category # no additional query
```

**Notes:** `joinedload` requires the relationship to be defined in the model class. Verify `Task.user` and `Task.category` are defined as `db.relationship(...)` before applying.

---

## T-09 — Inline Validation → Reusable Schema
**Applies to:** AP-09 (MEDIUM)

### Before (duplicated across create and update)
```python
# In criar_produto():
if "nome" not in dados:
    return jsonify({"erro": "Nome é obrigatório"}), 400
if "preco" not in dados:
    return jsonify({"erro": "Preço é obrigatório"}), 400
# ... 4 more checks

# In atualizar_produto(): — same code duplicated
if "nome" not in dados:
    return jsonify({"erro": "Nome é obrigatório"}), 400
```

### After (centralized validator)
```python
# controllers/produto_controller.py
REQUIRED_FIELDS_CREATE = ['nome', 'preco', 'estoque', 'categoria']
REQUIRED_FIELDS_UPDATE = ['nome', 'preco']

def validate_produto(dados, required_fields):
    for field in required_fields:
        if field not in dados:
            return f"{field.capitalize()} é obrigatório"
    if 'preco' in dados and float(dados['preco']) < 0:
        return "Preço não pode ser negativo"
    if 'estoque' in dados and int(dados['estoque']) < 0:
        return "Estoque não pode ser negativo"
    return None  # valid

# In route handler:
error = validate_produto(dados, REQUIRED_FIELDS_CREATE)
if error:
    return jsonify({"erro": error}), 400
```

**Notes:** The validator returns `None` if valid, or an error message string. This pattern works without adding new dependencies. If Marshmallow is already in `requirements.txt`, prefer Schema classes for richer validation.

---

## T-10 — Deprecated APIs → Modern Equivalents
**Applies to:** AP-11 (LOW)

### Before (Python)
```python
# deprecated since Python 3.12 — returns timezone-naive datetime
from datetime import datetime
updated_at = datetime.utcnow()

# debug mode hardcoded
app.run(debug=True, host='0.0.0.0', port=5000)
```

### After (Python)
```python
# timezone-aware datetime
from datetime import datetime, timezone
updated_at = datetime.now(timezone.utc)

# debug mode from environment
import os
app.run(
    debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
    host='0.0.0.0',
    port=int(os.getenv('PORT', 5000))
)
```

### Before (Node.js)
```javascript
// sqlite3.verbose() is a no-op in modern sqlite3
const sqlite3 = require('sqlite3').verbose();

// callback-style sqlite3 (old pattern)
db.run('INSERT INTO ...', params, function(err) { ... });
```

### After (Node.js)
```javascript
// remove verbose(), it does nothing useful
const sqlite3 = require('sqlite3');

// OR switch to sqlite wrapper for promise support
const { open } = require('sqlite');
const db = await open({ filename: ':memory:', driver: sqlite3.Database });
await db.run('INSERT INTO ...', params);
```

**Notes:** `datetime.utcnow()` is deprecated in Python 3.12 but not yet removed — it will raise a `DeprecationWarning`. Replacing it is forward-compatibility. For `app.run(debug=True)`, this is a security issue in production, not just deprecation — treat as MEDIUM severity if found in a production config.
