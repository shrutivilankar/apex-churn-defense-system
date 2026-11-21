# Review — commit `655ad88` ("determine risk profile")

Reviewed against:
1. Keep code very minimalistic — no try/catch when a global catch exists.
2. No unnecessary value checks when the payload can be trusted and is internal.
3. Remove boilerplate and ensure absolute simplification.

## Rule 1 — minimalistic, no redundant try/except

**Pass, with one caveat.**

- The risk package has no try/except. Upstream degradation uses
  `asyncio.gather(..., return_exceptions=True)` + `_resolve`
  (`src/risk/risk_profile_service.py:54-64`, `:141`), which is the intended
  partial-data behavior, not defensive noise.
- There is no global exception handler in the app (only
  `RequestValidationError`, `src/main.py:10`), so the existing client
  try/excepts are still needed. No change required here.
- Caveat: `_resolve` (`:141`) is an untyped mini-dispatcher
  (`result, source, sources, data_gaps, empty`). It works, but its loose
  typing is more machinery than the job needs.

## Rule 2 — no unnecessary value checks on trusted internal payloads

**2 clear violations.**

- `src/risk/risk_scoring_service.py:22` —
  `if profile.grievance_max_severity in severity_points:` is redundant.
  The field is `Optional[Severity]`, already validated by Pydantic, so a
  direct lookup is safe:

  ```python
  if profile.grievance_max_severity:
      churn_rules["grievance_severity"] = severity_points[profile.grievance_max_severity]
  ```

- `src/risk/risk_profile_service.py:43` —
  `if not party_id: raise ValueError(...)` duplicates the same guard
  already present in `payment_service.py:21` and other services. If
  `party_id` is internal/trusted, drop it (or drop the duplicate one, not
  both).
- Minor: `_normalize_severity` (`:277-288`) accepts 9 aliases and silently
  returns `None` for anything else; for an internal, typed source this is
  more validation than the contract needs.
- Keep the `Optional` checks on model fields (`paymentDate`,
  `creationDate`, `amount`) — those fields are genuinely optional in the
  models, so those guards are not redundant.

## Rule 3 — remove boilerplate / absolute simplification

**Fails.**

- **`src/workflow.py` is broken and should not have been committed.**
  Verified: `import src.workflow` raises
  `ModuleNotFoundError: No module named 'langraph'`.
  - `:1` typo `langraph` (dependency added is `langgraph`).
  - `:9`, `:24` reference `ChurnDefenseState` and `TroubleTicketCreate`
    that are never imported (and the class is declared at `:41`, after use).
  - `:27` uses undefined `state`.
  - `:30-31` reference undefined `score_subscriber_value` /
    `score_churn_risk`.
  - `:37` executes at import with `TroubleTicketCreate(id="111")`, which
    is invalid (required fields missing) — even if imports were fixed,
    this crashes on import.
  - Debug `print` statements (`:11`, `:34`); no graph compile/return.
- **Unused dependency:** `pyproject.toml` adds `langgraph`, but no working
  code imports it. Remove until the workflow exists.
- **Three copy-paste pagination loops** (`risk_profile_service.py:98`,
  `:111`, `:126`) — identical offset/totalCount logic. Collapse into one
  generic `_collect(fetch_page, ...)`.
- **Type mismatch / noise:** `sources: dict[str, str]` (`:59`) vs
  `dict[str, SourceStatus]` in the model (`risk_models.py:26`). Use
  `SourceStatus` and drop the string literals.
- **`unit_set` flag** (`:157`, `:171-173`) — small but avoidable
  bookkeeping; first captured amount's unit is sufficient.
- `src/risk/__init__.py:14-31` — `evaluate_risk` is a thin wrapper over two
  calls. Borderline; keep only if callers actually use it (currently
  nothing does).
- `.gitignore` adds `.delete/` — unrelated leftover; drop it.

## Verification

- `uv run pytest -q` → **17 passed** (risk profile/scoring are green).
- `import src.workflow` → **fails**; no test covers it.

## Verdict

The `src/risk` package mostly respects the rules (rule 1 passes; rules 2
and 3 have localized fixes). `src/workflow.py` + the `langgraph` dependency
violate all three and are the only blocking issues — remove or finish them
before the next commit.
