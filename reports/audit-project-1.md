================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 3 | LOW: 3
Total findings: 15

## Findings

### [CRITICAL] SQL Injection via String Concatenation
File: models.py:28
Description: Function `get_produto_por_id()` builds the SQL query by concatenating `str(id)` directly: `"SELECT * FROM produtos WHERE id = " + str(id)`. All 14 query-building functions in this file use the same pattern.
Impact: Attacker can extract all database contents, modify or delete any record by injecting SQL through any parameter.
Recommendation: Replace all string concatenation with parameterized queries using `?` placeholders (sqlite3).

### [CRITICAL] SQL Injection via String Concatenation — Search
File: models.py:291-297
Description: Function `buscar_produtos()` dynamically builds a WHERE clause with string concatenation for `termo`, `categoria`, `preco_min`, `preco_max`. Example: `query += " AND (nome LIKE '%" + termo + "%'"`.
Impact: User-controlled search parameters can inject arbitrary SQL. Combined with the `/admin/query` endpoint, full database takeover is trivial.
Recommendation: Use parameterized queries with dynamic parameter lists.

### [CRITICAL] Hardcoded Secret Key in Source
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` is hardcoded and also exposed in the `/health` endpoint response (controllers.py:282).
Impact: Anyone with repository access or who calls `/health` can forge sessions.
Recommendation: Move to environment variable: `os.getenv('SECRET_KEY')`. Never include in API responses.

### [CRITICAL] Admin Endpoints Without Authentication
File: app.py:47-78
Description: `POST /admin/reset-db` deletes all database tables with no authentication. `POST /admin/query` executes arbitrary SQL supplied by the client with no authentication.
Impact: Any anonymous user can destroy the entire database or extract/modify all data.
Recommendation: Remove `/admin/query` entirely. Protect `/admin/reset-db` with authentication and restrict to admin role only.

### [HIGH] DEBUG Mode Hardcoded in Source
File: app.py:8,88
Description: `app.config["DEBUG"] = True` and `app.run(debug=True)` enable the interactive Werkzeug debugger and expose full stack traces in all error responses.
Impact: In production, the Werkzeug debugger allows remote code execution via the interactive console.
Recommendation: Control debug mode via environment variable: `debug=os.getenv('FLASK_DEBUG','false').lower()=='true'`.

### [HIGH] Password Stored in Plaintext
File: models.py:127-128
Description: `criar_usuario()` inserts the raw password string directly into the database: `"...VALUES ('" + nome + "', '" + email + "', '" + senha + "'..."`. No hashing applied.
Impact: Any database breach or SQL injection immediately reveals all user passwords.
Recommendation: Hash passwords with `werkzeug.security.generate_password_hash()` before storing.

### [HIGH] Sensitive Data Exposed in Health Endpoint
File: controllers.py:272-282
Description: `/health` endpoint returns `"debug": True`, `"db_path": "loja.db"`, and `"secret_key": "minha-chave-super-secreta-123"` in the JSON response.
Impact: Unauthenticated endpoint leaks infrastructure details and the application secret key.
Recommendation: Remove all sensitive fields from health response. Return only `{"status": "ok", "database": "connected"}`.

### [HIGH] N+1 Query Problem — Pedidos
File: models.py:187-200
Description: `get_pedidos_usuario()` fetches all pedidos, then for each pedido opens cursor2 to fetch itens_pedido, then for each item opens cursor3 to fetch the product name. 3-level nested query loop.
Impact: 10 pedidos with 3 items each = 1 + 10 + 30 = 41 queries instead of 1 JOIN.
Recommendation: Use a single JOIN query: `SELECT p.*, ip.*, pr.nome FROM pedidos p JOIN itens_pedido ip ON ip.pedido_id = p.id JOIN produtos pr ON pr.id = ip.produto_id WHERE p.usuario_id = ?`.

### [HIGH] Business Logic Duplicated Between Controllers
File: controllers.py:30-54,74-90
Description: Fields `nome`, `preco`, `estoque` validation is duplicated word-for-word between `criar_produto()` (lines 30-54) and `atualizar_produto()` (lines 74-90). The category list `["informatica","moveis",...]` is also duplicated.
Impact: Changes to validation rules must be made in two places; inconsistencies will introduce bugs.
Recommendation: Extract to a `validate_produto(dados, required_fields)` function in the controller layer.

### [MEDIUM] Mutable Global Database Connection
File: database.py:4,8-9
Description: Module-level `db_connection = None` global is set with `check_same_thread=False` to bypass SQLite's thread-safety check.
Impact: Under concurrent requests, race conditions can corrupt the connection or return wrong results.
Recommendation: Use `flask.g` for request-scoped connections, or switch to SQLAlchemy with connection pooling.

### [MEDIUM] Passwords Returned in API Responses
File: models.py:77-87 (get_todos_usuarios), models.py:93-103 (get_usuario_por_id)
Description: Both user-fetching functions return the `senha` field in the response dict. The `GET /usuarios` and `GET /usuarios/<id>` endpoints thus expose password hashes (or plaintext passwords) to any caller.
Impact: Any unauthenticated API consumer can enumerate all user passwords.
Recommendation: Remove `senha` from all response serialization. Never expose password fields in API responses.

### [MEDIUM] Magic Numbers — Discount Thresholds
File: models.py:256-262
Description: `relatorio_vendas()` contains hardcoded business thresholds: `if faturamento > 10000: desconto = faturamento * 0.1` with three tiers. No named constants, no documentation.
Impact: Changing discount rules requires finding and editing magic numbers in business logic.
Recommendation: Extract to named constants in `config/settings.py`: `DISCOUNT_TIER_1 = 10000`, `DISCOUNT_RATE_1 = 0.10`.

### [LOW] Deprecated: debug=True in app.run()
File: app.py:88
Description: `app.run(debug=True)` is the pattern deprecated for production use since Flask 0.11. Also port `5000` is hardcoded.
Impact: Development-only flag committed to source. Port cannot be configured without code change.
Recommendation: Use `PORT=int(os.getenv('PORT', 5000))` and control debug via environment.

### [LOW] Logging via print() Instead of logging Module
File: controllers.py:9,11,57,106,161,179,208-210,219,248,250,286
Description: All logging done via `print()` statements with no severity levels, no timestamps, no structured format.
Impact: Impossible to filter log levels in production; no log aggregation support.
Recommendation: Replace with Python `logging` module: `import logging; logger = logging.getLogger(__name__)`.

### [LOW] Hardcoded String Lists Not Centralized
File: controllers.py:42-43
Description: `categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` defined inline inside the function, not shared with the rest of the codebase.
Impact: If a new category is added, the list must be found and updated inside the function.
Recommendation: Move to `config/settings.py` as a named constant `VALID_CATEGORIES`.

================================
Total: 15 findings
================================

## Refactoring Strategy
Decision: Monolith-Rewrite
Reason: Project has 4 flat source files at root with no layer separation — all code (routing, business logic, data access, configuration) is mixed across app.py, models.py, controllers.py, database.py.

Planned new structure:
src/
├── config/
│   └── settings.py
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── views/
│   └── routes.py
└── middlewares/
    └── error_handler.py
app.py  (composition root only)
