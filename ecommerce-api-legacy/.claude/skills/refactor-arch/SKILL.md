---
name: refactor-arch
description: Audita e refatora projetos backend para o padrão MVC. Detecta linguagem/framework, identifica anti-patterns com severidade (arquivo:linha exatos), gera relatório estruturado, pausa para confirmação humana e executa refatoração. Valida que a aplicação continua funcionando após as mudanças. Use quando o usuário pedir auditoria arquitetural, análise de code smells, refatoração para MVC, ou invocar /refactor-arch. Funciona com Python/Flask e Node.js/Express.
---

# refactor-arch

Analyze, audit, and refactor backend projects to MVC. Three sequential phases: Analysis → Audit (with confirmation) → Refactoring (with validation).

## Operating Principles

- **Phases are sequential.** Never start Phase 3 before the user confirms Phase 2.
- **CHECKPOINT is binding.** Phase 2 ends with a mandatory `[y/n]` prompt. Do not proceed without an affirmative reply (`y`, `yes`, or `sim`).
- **Smoke test is mandatory.** Phase 3 is not complete until the application boots and all endpoints respond with non-5xx status.
- **Never delete original files** until the refactored version successfully boots.
- **No file modifications before confirmation.** Reading, grepping, and analyzing are permitted at any phase. Writing files is only permitted in Phase 3, after user confirmation.
- **Record strategy.** Always note in the audit report whether Monolith-Rewrite or Partial-Improve was chosen, and why.
- **Verify before reporting.** Every finding must be confirmed by reading the actual file — do not report based solely on grep output.

---

## PHASE 1 — Project Analysis

### Steps

1. Read the detection guide:
   ```
   Read references/stack-detection.md
   ```

2. Run the detection sequence from `stack-detection.md`:
   - Detect language (look for `requirements.txt`, `package.json`, etc.)
   - Detect framework and version
   - Detect database and tables
   - Map all endpoints (save this list — reused in Phase 3)
   - Infer business domain from tables + endpoint paths
   - Determine current architecture (monolithic vs. partially organized)

3. Count source files:
   ```bash
   find . -name "*.py" -o -name "*.js" | grep -v node_modules | grep -v .git | grep -v "__pycache__" | wc -l
   ```

4. Print the Phase 1 summary box (exact format):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <value>
Framework:     <value>
Dependencies:  <key deps>
Domain:        <inferred domain>
Architecture:  <Monolithic — N files | Partially Organized — layers: X, Y, Z>
Source files:  <N> files analyzed
DB tables:     <table1, table2, ...>
================================

Endpoints mapped:
  GET    /path1
  POST   /path2
  ...
```

5. Proceed to Phase 2.

---

## PHASE 2 — Architecture Audit

### Steps

1. Read the anti-patterns catalog:
   ```
   Read references/anti-patterns.md
   ```

2. For each of the 12 anti-patterns in the catalog:
   a. Run the detection grep command(s) listed in the catalog entry.
   b. For every grep match, read the file at the indicated line to confirm the issue.
   c. If confirmed, create a finding record: `{severity, file:line, description, impact, recommendation}`.
   d. If grep matches but reading shows it is a false positive (comment, string literal, unrelated code), discard it.

3. Sort all findings: CRITICAL first, then HIGH, MEDIUM, LOW. Within each group, order by file then line number.

4. Read the report template:
   ```
   Read references/audit-report-template.md
   ```

5. Render the full audit report using the template. Include:
   - Summary counts by severity
   - All findings with exact `file:line` references
   - Refactoring Strategy section (decision + planned structure)

6. Print the complete report.

7. Save the report:
   - Determine the project number (1, 2, or 3) from context or ask the user.
   - Save to `../../reports/audit-project-N.md` relative to the current project directory.
   - If the `reports/` directory does not exist, create it.

8. **CHECKPOINT — MANDATORY STOP:**

   Print exactly:
   ```
   ================================
   Total: N findings
   ================================

   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   **STOP. Do not proceed to Phase 3 until the user replies "y", "yes", or "sim".**
   Any other response — including "n", no response, or unrelated input — means abort.

   If you find yourself reading `refactor-playbook.md` or writing any file before the user has confirmed, you have violated this protocol. Abort immediately.

---

## PHASE 3 — Refactoring

*This phase begins only after user confirmation at the Phase 2 checkpoint.*

### Steps

1. Check for uncommitted work:
   ```bash
   git status
   ```
   If there are unstaged changes not related to this skill run, warn the user and offer to abort.

2. Read the architecture guidelines:
   ```
   Read references/mvc-architecture.md
   ```

3. Determine refactoring strategy using the algorithm in `mvc-architecture.md` (Adaptive Strategy section):
   ```bash
   layer_dirs=$(ls -d */ 2>/dev/null | grep -cE "^(models|routes|controllers|views|services|middlewares|config|src)/$")
   root_files=$(find . -maxdepth 1 \( -name "*.py" -o -name "*.js" \) 2>/dev/null | grep -vE "(app|seed|database)\.(py|js)$" | wc -l | tr -d ' ')
   ```
   - `layer_dirs >= 2` AND `root_files <= 3` → **PARTIAL-IMPROVE**
   - Otherwise → **MONOLITH-REWRITE**

   Append the decision to the audit report file.

4. Read the refactoring playbook:
   ```
   Read references/refactor-playbook.md
   ```

5. Apply transformations. For each finding from Phase 2, look up the corresponding transformation (T-01 through T-10) and apply it. Work finding-by-finding, most critical first.

6. **After every file move or rename**, immediately run:
   ```bash
   grep -Rn "from <old_module> import\|import <old_module>" . --include="*.py"
   grep -Rn "require.*<old_file>" . --include="*.js" | grep -v node_modules
   ```
   Update all references before moving to the next transformation.

7. Update the entry point (`app.py` or `app.js`) to reflect new import paths and composition structure.

8. Create `.env.example` if any secrets were moved to environment variables.

9. **Smoke Test — Read the procedure:**
   ```
   Read references/smoke-test.md
   ```

10. Execute the smoke test procedure from `smoke-test.md`:
    - Install dependencies
    - Boot server in background (save PID)
    - Poll for readiness (max 10s)
    - Test each endpoint from Phase 1 inventory
    - Teardown (kill server by PID)

11. Evaluate results:
    - All endpoints return `< 500` AND server booted without crash → **SUCCESS**
    - Any endpoint returns `5xx` OR server crashes → **FAILURE** (fix and retry before declaring done)

12. Print the Phase 3 completion box:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Strategy: <Monolith-Rewrite | Partial-Improve>

## New Project Structure
<ascii tree of actual new directory structure>

## Changes Made
  - <file created or modified>
  - ...

## Security Fixes Applied
  - <security issue resolved>
  - ...

## Validation
  ✓ GET  /path    → 200
  ✓ POST /path    → 201
  ...

Passed: N/M endpoints
================================
```

---

## Output Reference

### Phase 1 Box
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      {language}
Framework:     {framework} {version}
Dependencies:  {key dependencies}
Domain:        {domain description}
Architecture:  {architecture description}
Source files:  {N} files analyzed
DB tables:     {tables}
================================
```

### Phase 2 Box
```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: {project_name}
Stack:   {language} + {framework}
Files:   {N} analyzed | ~{lines} lines of code

## Summary
CRITICAL: {n} | HIGH: {n} | MEDIUM: {n} | LOW: {n}

## Findings
{findings list}

================================
Total: {N} findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

### Phase 3 Box
```
================================
PHASE 3: REFACTORING COMPLETE
================================
Strategy: {strategy}

## New Project Structure
{directory tree}

## Changes Made
{bullet list}

## Security Fixes Applied
{bullet list}

## Validation
{smoke test results}

Passed: {N}/{M} endpoints
================================
```

---

## Failure Handling

**Stack not detected:**
Print: "Could not detect a supported stack in this directory. Expected `requirements.txt` (Python) or `package.json` (Node.js). Aborting."

**Fewer than 5 findings:**
Print all findings found and note: "Only N findings detected. This may indicate a well-structured project or gaps in the catalog. Review manually before proceeding."

**User answers "n" at Phase 2 checkpoint:**
Print: "Refactoring aborted. No files were modified. The audit report was saved to reports/audit-project-N.md."

**Smoke test fails:**
Do NOT print the Phase 3 completion box. Instead:
1. Report the specific failure (endpoint + status code + error from server logs).
2. Investigate and fix the issue.
3. Re-run the smoke test.
4. Only print the completion box after all endpoints pass.

**Server fails to start within 10s:**
```bash
# Check for error output
kill $SERVER_PID 2>/dev/null
```
Report: "Server did not start within 10 seconds. Check for import errors or missing dependencies." Then investigate the error, fix, and retry.
