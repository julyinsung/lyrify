---
name: vulcan-impl-wave
description: Use for Vulcan implementation phase work, BW-000 scaffold, Build Wave planning, worker Run creation, run-preflight, native subagent/thread delegation, optional agent-run/run-exec execution, run-integrate, wave-complete, and implementation traceability.
---

# Vulcan Impl Wave

Use this for `impl` Gate execution and follow-up implementation iterations.

## Preconditions

1. Confirm `session.json.current_gate` is `impl`.
2. Confirm previous Gate approval exists.
3. Run `python vulcan.py status` to confirm Gate, profile, branch, active Run/Wave, and dirty state.
4. Apply profile-specific Run weight and trace depth rules from `docs/core/DELIVERY_PROFILES.md`.
5. Use `python vulcan.py branch-status` only if branch-only detail is needed beyond `status`.

## Workflow

1. Create or review an implementation plan Run when scope is more than a tiny change.
2. If buildable skeleton is missing, check the delivery profile before starting `BW-000`.
   - In `poc`, do not create `BW-000` by default. Let the first native worker create the environment, hello/build smoke, and the core feature together unless the user asks for stricter separation.
   - In `product` or `audit`, prefer an earlier Environment Readiness Track when possible; use `BW-000 implementation-scaffold` when official contract skeleton or build smoke must be isolated.
3. Create one active Build Wave at a time.
4. Prefer `wave-start <BW-ID> --trace-seed <detailed-id>` or `run-new ... --trace-seed <id>`.
5. Narrow `scope.writable`, `target_contracts`, `interface_contract`, and verification commands before worker execution.
6. If related IDs/source documents are unclear, use `trace-scout` before finalizing the Run.
7. If the Run is important, newly generated, or previously problematic, use `run-drafter` before worker handoff.
8. Run `python vulcan.py run-preflight <run-file>` before native worker delegation. `run-exec` and `agent-run --mode work` auto-run preflight, but native subagent/thread/Agy Workspace branch delegation does not.
9. Run `python vulcan.py doctor` before retrying a worker when failure looks like local runtime readiness, for example unsupported runner, missing npm/Node, missing Playwright browser cache, locked port, or Dashboard/runtime confusion.
10. Use native worker delegation (subagent/thread/native branch agent) for code, test, UI, API, or DB implementation by default.
11. Use `agent-run --mode work` or `run-exec` only when external CLI process evidence, worktree isolation, watchdog/timeout, or cross-runner execution is needed.
12. After worker output, use `contract-reviewer` when runtime/API/DB/UI contract drift is plausible.
13. Integrate worker output only after diff/scope verification.
14. Record native subagent/thread output in `delegation_records`; include started_at, completed_at, duration_seconds, heartbeat_count/status_probe_count when available. External CLI workers also keep Run Execution Record and `_exec` logs.
15. Complete the Wave with `wave-complete` and `sync-session` only after relevant tests pass.
16. In `poc`, do not let workers chase non-blocking `run-preflight` or `run-check` warnings. If implementation tests pass and only non-blocking warnings remain, the worker records them and returns for Orchestrator judgment.
17. In `poc`, keep Build Worker scope to code, requirements/dependency files, and fast self-checks. README, final test report, browser screenshots, release/backlog, and evidence normalization belong to Gate 4/5 or a separate Evidence/Normalization Worker.

## Guardrails

- Orchestrator should not be the primary implementer.
- User silence about worker usage is not a direct-implementation exception.
- Do not mark Gate 3 planned tests as Pass during Impl just to satisfy trace checks.
- Full E2E/UI evidence belongs to Gate 4 unless explicitly scoped as smoke evidence.
- In `poc`, warning cleanup is not a worker completion goal unless the warning hides a real product failure, broken test, or scope violation.
- For PoC performance review, prefer recording file-change lifecycle fields when known: `first_file_change_at`, `last_file_change_at`, `worker_final_response_at`, `final_response_lag_seconds`.
- In `poc` Impl, do not ask the Build Worker to create final browser evidence or complete `POC_TEST_REPORT.md`; that turns the build worker into a QA/doc worker and hides the real cost.

## Verification

- `python vulcan.py run-check <run-file>`
- `python vulcan.py run-preflight <run-file>`
- Relevant backend/frontend tests for the Wave
- `python vulcan.py check-trace` after traceability updates
