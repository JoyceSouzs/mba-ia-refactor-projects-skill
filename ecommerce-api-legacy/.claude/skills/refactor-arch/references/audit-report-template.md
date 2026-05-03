# Audit Report Template

Use this template to render the Phase 2 output. Replace all `{placeholders}`. Do not omit any section.

---

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: {project_name}
Stack:   {language} + {framework}
Files:   {file_count} analyzed | ~{line_count} lines of code

## Summary
CRITICAL: {n} | HIGH: {n} | MEDIUM: {n} | LOW: {n}
Total findings: {total}

## Findings
```

Then list each finding using this structure (one block per finding, ordered CRITICAL → HIGH → MEDIUM → LOW):

```
### [{SEVERITY}] {Anti-pattern Name}
File: {relative/path/to/file.ext}:{start_line}-{end_line}
Description: {one or two sentences describing exactly what is wrong here, with code reference}
Impact: {concrete consequence if exploited or left unaddressed}
Recommendation: {specific fix action for this project}
```

Close with:

```
================================
Total: {total} findings
================================

## Refactoring Strategy
Decision: {Monolith-Rewrite | Partial-Improve}
Reason: {one sentence explaining why this strategy was chosen based on current project structure}

Planned new structure:
{ascii tree of target directory structure}
```

---

## Filling in the fields

**{project_name}:** The directory name of the project being analyzed (e.g., `code-smells-project`).

**{file_count} / {line_count}:** Count via `find . -name "*.py" -o -name "*.js" | grep -v node_modules | wc -l` and `xargs wc -l`.

**{SEVERITY}:** Must be one of: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Use exact spelling, all caps.

**File:line format:** Use relative paths from project root. Include both start and end line when a block is affected. Example: `models.py:28` or `models.py:187-200`. This must be accurate — verify by reading the file.

**Ordering rule:** All CRITICAL findings first, then HIGH, then MEDIUM, then LOW. Within each severity, order by file then line number.

**Refactoring Strategy section:** Written before the `[y/n]` confirmation prompt. The user approves both the findings and the strategy.

---

## Example finding block

```
### [CRITICAL] SQL Injection via String Concatenation
File: models.py:28
Description: Function get_produto() builds SQL query by concatenating str(id) directly into the query string: `"SELECT * FROM produtos WHERE id = " + str(id)`. Any route calling this function is vulnerable.
Impact: Attacker can extract all database contents, modify or delete records by injecting SQL through the id parameter.
Recommendation: Replace with parameterized query: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`
```

---

## Saving the report

After rendering the report:
1. Print it to the console (the user reviews it).
2. Save a copy to `reports/audit-project-N.md` in the **repository root** (two levels up from the project directory if the project is nested). Ask the user for the project number N if not obvious from context.

The file saved must be identical to what was printed — no truncation.
