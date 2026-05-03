================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 3 | LOW: 2
Total findings: 12

## Findings

### [CRITICAL] God Class — AppManager
File: src/AppManager.js:1-141
Description: The `AppManager` class handles everything: database initialization, route setup, checkout business logic, financial reporting, user deletion, and database callbacks — all mixed into a single 141-line class. No separation of concerns whatsoever.
Impact: Impossible to test any piece in isolation; any change risks breaking unrelated functionality; cannot reuse business logic outside HTTP context.
Recommendation: Split into: `DatabaseManager` (DB init), `CheckoutService` (checkout logic), `ReportService` (financial report), `UserService` (user management), `routes/` (HTTP handlers).

### [CRITICAL] Hardcoded Credentials in Source
File: src/utils.js:1-8
Description: Production credentials hardcoded directly: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"`.
Impact: Anyone with repository access has production payment gateway and database credentials. Risk of financial fraud, data breach.
Recommendation: Move all secrets to environment variables (`process.env.PAYMENT_GATEWAY_KEY`, etc.). Create `.env.example` with placeholder values.

### [CRITICAL] Insecure Password Hashing — `badCrypto()`
File: src/utils.js:13-20
Description: `badCrypto()` generates a password "hash" by base64-encoding the password 10,000 times and truncating to 10 characters. This is not a hash — it is a reversible encoding. The result has extremely limited entropy (only 10 chars from base64 alphabet).
Impact: Any database breach exposes all passwords instantly. The function's own name `badCrypto` acknowledges it is insecure.
Recommendation: Replace with `bcrypt` (`npm install bcrypt`). Use `bcrypt.hash(password, 12)` and `bcrypt.compare()`.

### [HIGH] Callback Hell — 5-Level Nesting in Checkout
File: src/AppManager.js:28-78
Description: The checkout route handler nests 5 levels of sqlite3 callbacks: route → db.get(course) → db.get(user) → db.run(enrollment) → db.run(payment) → db.run(audit_log). Error handling is copy-pasted at each level.
Impact: Brittle code where adding error handling or a new step requires restructuring the entire pyramid; race conditions if any callback fires unexpectedly.
Recommendation: Use `sqlite` wrapper (`npm install sqlite`) for Promise-based API and convert to `async/await`.

### [HIGH] Business Logic Coupled Directly in Route Handler
File: src/AppManager.js:28-78
Description: The `POST /api/checkout` handler contains card validation logic (`cc.startsWith("4")`), user creation, payment processing, enrollment creation, and audit logging all in a single route function with no abstraction.
Impact: Cannot reuse checkout logic from CLI, webhooks, or batch jobs; unit testing requires the full HTTP stack.
Recommendation: Extract to `CheckoutService.processCheckout(courseId, email, name, card)` with proper async/await.

### [HIGH] Referential Integrity Violation on User Delete
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes the user row but leaves orphaned `enrollments` and `payments` rows. The code itself acknowledges this: `"...as matrículas e pagamentos ficaram sujos no banco"`.
Impact: Financial reports become corrupted; orphaned data grows over time; JOIN queries return incorrect results.
Recommendation: Use a database transaction with cascade deletes, or soft-delete the user (set `active=0`) instead of hard delete.

### [HIGH] Race Condition in Financial Report
File: src/AppManager.js:80-129
Description: The report aggregation uses manual counter variables (`coursesPending`, `enrPending`) to track async completion. If any callback fires twice or an error is silently ignored, `res.json()` is called multiple times.
Impact: Non-deterministic responses; "headers already sent" crashes; corrupt report data.
Recommendation: Convert to `async/await` with proper aggregation using Promise.all or a single JOIN query.

### [MEDIUM] Missing Input Validation in Checkout
File: src/AppManager.js:33-35
Description: Checkout validates only field presence (`if (!u || !e || !cid || !cc)`). No email format validation, no card number format validation (only checks first character), no course ID type check, no password strength check.
Impact: Invalid data persisted to database; payment processed for obviously invalid cards; malformed emails stored.
Recommendation: Add proper validation: email regex, card Luhn check (or at minimum length check), numeric cid check.

### [MEDIUM] Mutable Global State
File: src/utils.js:9-10
Description: `let globalCache = {}` and `let totalRevenue = 0` are module-level mutable variables with no synchronization, modified by `logAndCache()`.
Impact: Shared mutable state across requests causes non-deterministic behavior; cache grows unbounded; `totalRevenue` is never used but pollutes the module.
Recommendation: Remove `totalRevenue` (unused). Replace `globalCache` with request-scoped state or a proper cache library.

### [MEDIUM] No Centralized Error Handling Middleware
File: src/app.js:1-14
Description: Express app has no error handling middleware. All errors are handled inline with `return res.status(500).send("Erro DB")` strings, not consistent JSON responses.
Impact: Mixed response formats (strings vs. JSON); stack traces may leak to clients; no centralized logging.
Recommendation: Add Express error handler middleware: `app.use((err, req, res, next) => { res.status(500).json({ error: err.message }) })`.

### [LOW] Deprecated: sqlite3.verbose() is a No-Op
File: src/AppManager.js:1
Description: `require('sqlite3').verbose()` — the `.verbose()` method has been a no-op since sqlite3 v4+. It adds no debugging information.
Impact: None functionally, but signals the code was written against an older API and has not been reviewed since.
Recommendation: Replace with `require('sqlite3')` and switch to `sqlite` wrapper for Promise support.

### [LOW] Obfuscated Variable Names
File: src/AppManager.js:29-34
Description: Request body variables use abbreviations: `u` (name), `e` (email), `p` (password), `cid` (course_id), `cc` (credit card). Field names in request body (`usr`, `eml`, `c_id`, `card`) also inconsistent.
Impact: Reduces readability; "cc" could be confused with CC (carbon copy); `p` could be price or page.
Recommendation: Use full descriptive names: `userName`, `email`, `password`, `courseId`, `cardNumber`.

================================
Total: 12 findings
================================

## Refactoring Strategy
Decision: Monolith-Rewrite
Reason: All code lives in 3 files with no layer separation — `AppManager.js` handles routing, business logic, data access, and database initialization all in one class.

Planned new structure:
src/
├── config/
│   └── settings.js
├── database/
│   └── connection.js
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   └── reportModel.js
├── controllers/
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── routes/
│   └── index.js
├── middlewares/
│   └── errorHandler.js
└── app.js  (composition root)
