# Run Output Contract

> 상태: v0.4
> 목적: Codex, Claude, Gemini 등 모든 worker runner가 동일하게 남기는 공통 완료보고서 형식을 정의한다.

## 1. 개념

Run Output Contract는 worker 또는 Orchestrator Run의 완료보고서다.

Runner 종류가 달라도 출력은 같은 구조로 정규화한다.
Adapter는 각 runner의 stdout, last message, result file, activity log를 이 계약으로 변환할 수 있지만, 출력 형식을 runner별로 따로 정의하지 않는다.

에이전트는 단순히 "완료했습니다"라고 말하지 않고 다음 질문에 답해야 한다.

- 무엇을 변경했는가?
- 어떤 ID와 연결되는가?
- 어떤 검증을 실행했는가?
- 어떤 증적을 남겼는가?
- 어떤 개발표준을 지켰는가?
- 남은 이슈는 무엇인가?
- Orchestrator 판단이 필요한 항목은 무엇인가?
- worker, subagent, thread 중 누구에게 어떤 범위를 위임했는가?
- 다음 Run은 무엇이 적절한가?

## 2. 필수 필드

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `run_id` | 예 | 입력과 동일한 Run ID |
| `status` | 예 | `Completed`, `CompletedWithIssues`, `Blocked`, `Failed`, `AwaitingApproval` 등 |
| `summary` | 예 | 작업 요약 |
| `changed_files` | 예 | 변경 파일 목록. 없으면 빈 배열 |
| `related_ids` | 예 | 변경과 연결된 ID |
| `verification_results` | 예 | 테스트/린트/빌드/캡처 실행 결과 |
| `evidence` | 예 | 결과서, 캡처, 로그, 커밋 등 |
| `delegation_records` | 위임이 있으면 필수 | subagent/thread/외부 runner에게 맡긴 작업 범위와 결과 요약 |
| `standard_compliance_report` | 구현 Run 권장 | 적용 개발표준 준수 여부 |
| `traceability_updates` | 예 | 추적표 또는 산출물 갱신 내용. worker가 직접 확정하지 못하면 필요 항목으로 기록 |
| `open_issues` | 예 | 남은 이슈. 없으면 빈 배열 |
| `orchestrator_decision_needed` | 예 | worker가 직접 판단/수정하지 말아야 할 항목 |

## 3. 선택 필드

| 필드 | 넣는 경우 |
| --- | --- |
| `execution` | 외부 CLI runner의 model, effort, sandbox, timeout, worktree, branch, log 경로 같은 실행 메타가 필요할 때 |
| `gate_exit_summary` | Gate 종료 Run에서 산출물 요약과 다음 Gate 제안을 남길 때 |
| `approval_request` | 다음 Gate 진행 전 사용자 승인 질문을 남길 때 |
| `findings` | QA/리뷰 중 발견한 결함과 처리 결과를 남길 때 |
| `change_requests` | 요구사항, 설계, 기준선 변경이 필요한 항목을 남길 때 |
| `failure_reports` | QA 실행 중 `Fail`, `Not Run`, `environment_blocked`가 발생했을 때 |
| `next_run_suggestion` | 후속 Run을 제안할 때 |
| `failure` | `Failed` 상태의 실패 원인을 구조화할 때 |
| `blocked_reason` / `questions` | `Blocked` 상태의 질문과 차단 사유를 남길 때 |

## 4. 권장 YAML 형식

```yaml
run_id: RUN-001
status: Completed

execution:
  runner: codex-cli
  model: gpt-5.5
  effort: high
  worktree: .vulcan/worktrees/RUN-001-codex-cli
  branch: codex/run-run-001-codex-cli

delegation_records:
  - mode: external-runner
    delegate: codex-cli
    task: "PGM-005 구현"
    scope:
      writable:
        - src/api/posts.py
        - tests/test_posts.py
    started_at: "2026-06-07T10:00:00+09:00"
    completed_at: "2026-06-07T10:12:00+09:00"
    status: worker_completed
    changed_files:
      - src/api/posts.py
      - tests/test_posts.py
    result_summary: "게시글 작성 API와 테스트를 구현했다."
    run_execution_record: "docs/runs/_exec/RUN-001_codex-summary.json"

summary:
  ko: "PGM-005 게시글 작성 기능을 구현하고 관련 단위/통합 테스트를 통과시켰다."
  changed_behavior:
    - "인증 사용자는 게시글을 작성할 수 있다."
    - "비로그인 사용자의 작성 요청은 차단된다."

changed_files:
  - path: src/api/posts.py
    change_type: modified
    related_ids: [PGM-005, REQ-005, SEC-002]
  - path: tests/test_posts.py
    change_type: modified
    related_ids: [UT-007, UT-008]

related_ids:
  req: [REQ-005]
  ac: [AC-007, AC-008]
  func: [FUNC-005]
  scr: [SCR-005]
  pgm: [PGM-005]
  api: [API-005]
  db: [DB-002]
  sec: [SEC-002, SEC-004]
  test: [UT-007, UT-008, IT-004]

verification_results:
  - id: UT-007
    type: test
    cwd: repository root
    command: "python -m pytest tests/test_posts.py -p no:cacheprovider"
    os: windows
    exit_code: 0
    success_criteria: "exit code 0, 실패 0건"
    result: passed
    summary: "2 passed"
    log_path: null
    evidence_path: docs/runs/RUN-001_pgm-005-게시글-작성_v0.1.md

evidence:
  documents:
    - docs/runs/RUN-001_pgm-005-게시글-작성_v0.1.md
  files: []
  logs: []
  ui: []
  ui_contract_diffs: []
  commit: null

standard_compliance_report:
  - standard_id: DEV-DIR-001
    status: Pass
    implementation: "Router -> Service -> Repository 구조를 유지했다."
    exception_reason: null
  - standard_id: DEV-ERR-001
    status: Pass
    implementation: "공통 오류 응답 포맷을 사용했다."
    exception_reason: null

traceability_updates:
  - document: docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    update: "REQ-005 관련 테스트 결과 반영 필요"
    owner: orchestrator

open_issues: []

orchestrator_decision_needed:
  - "추적표 최종 반영과 session 갱신은 Orchestrator가 재검증 후 처리해야 한다."

findings: []
change_requests: []
failure_reports: []

next_run_suggestion:
  run_type: Review
  goal: "PGM-005 구현 결과를 독립 검수한다."
  related_ids: [PGM-005, UT-007, IT-004]
```

## 4.1 Delegation Record

`delegation_records`는 Orchestrator가 작업을 직접 수행하지 않고 다른 실행자에게 맡긴 사실을 남기는 얇은 책임 추적 기록이다.

외부 CLI runner를 사용할 때는 `Run Execution Record`와 `execution`에 상세 메타를 남긴다. subagent 또는 같은 Codex thread 계열 위임은 프로세스 로그, stderr, timeout, cache 경로까지 남기지 않아도 된다. 대신 누가, 어떤 범위로, 어떤 결과를 반환했고, Orchestrator가 무엇을 재검증했는지는 남긴다.

```yaml
delegation_records:
  - mode: codex-subagent
    delegate: build
    native_agent: false
    task: "BW-001 backend API/DB 구현"
    scope:
      writable:
        - backend/app/
        - backend/tests/
    started_at: "2026-06-07T10:00:00+09:00"
    completed_at: "2026-06-07T10:08:00+09:00"
    duration_seconds: 480
    first_file_change_at: "2026-06-07T10:01:10+09:00"
    last_file_change_at: "2026-06-07T10:06:40+09:00"
    worker_final_response_at: "2026-06-07T10:08:00+09:00"
    final_response_lag_seconds: 80
    heartbeat_count: 2
    status_probe_count: 1
    status: worker_completed
    changed_files:
      - backend/app/todos/service.py
      - backend/tests/unit/test_todo_service.py
    result_summary: "Todo service/repository/API 구현과 단위 테스트를 작성했다."
    orchestrator_verification:
      - command: "python -m pytest backend/tests -q"
        result: passed
    notes:
      - "Gate 전환과 session 갱신은 Orchestrator가 수행한다."
```

권장 `mode` 값:

| 값 | 의미 |
| --- | --- |
| `codex-subagent` | Codex Desktop/CLI 세션 안의 subagent 위임 |
| `codex-thread` | 별도 Codex thread/session 기반 위임 |
| `claude-subagent` | Claude subagent 위임 |
| `agy-branch-agent` | Antigravity/Agy workspace branch 또는 agent 위임 |
| `external-runner` | `agent-run`/`run-exec` 같은 외부 CLI runner 실행 |
| `manual` | 사람이 명시 수행한 보조 작업 |

권장 `status` 값:

| 값 | 의미 |
| --- | --- |
| `worker_running` | worker가 실행 중 |
| `worker_completed` 또는 `completed` | worker가 결과를 반환했지만 Orchestrator 재검증 전 |
| `orchestrator_verifying` | Orchestrator가 worker 결과를 재검증 중 |
| `verified` | Orchestrator가 테스트/증적/계약을 재검증해 통과로 정리 |
| `needs_review` | 결과는 있으나 보정, 사용자 판단, FIND/CR/ISSUE 분류 필요 |
| `blocked`, `failed`, `environment_blocked`, `timeout` | 진행 불가, 실패, 환경 차단, 시간 초과 |

`worker_completed`/`completed`는 완료 신호이지 검증 완료가 아니다. 완료된 Build/QA Run에 `delegation_records.status: worker_completed`만 남기고 `orchestrator_verification` 또는 최종 `verified/needs_review/blocked` 정리가 없으면 `run-check`와 `run-preflight`는 경고한다.

최소 필드:

- `mode`
- `delegate`
- `task`
- `scope.writable`
- `status`
- `changed_files`
- `result_summary`
- `orchestrator_verification`

권장 계측 필드:

- `started_at`
- `completed_at`
- `duration_seconds`
- `first_file_change_at`
- `last_file_change_at`
- `worker_final_response_at`
- `final_response_lag_seconds`
- `heartbeat_count`
- `status_probe_count`
- `self_check`

`first_file_change_at`과 `last_file_change_at`은 worker가 실제 파일 변경을 시작/마친 시각이다. `worker_final_response_at`은 worker가 최종 응답을 반환한 시각이고, `final_response_lag_seconds`는 `last_file_change_at`부터 최종 응답까지의 대기/문서 정리 시간을 나타낸다.

이 필드들은 승인 차단 조건은 아니지만, PoC/worker 병목 분석과 `vulcan.py metrics` 회고 자료를 만들 때 중요하다. 시간이 확실하지 않으면 추정하지 말고 비워두거나 `notes`에 근거를 남긴다. PoC worker는 이 값을 맞추려고 추가 루프를 돌지 않고, 알 수 있는 범위만 기록한다.

PoC profile의 짧은 실험은 Run 문서를 만들지 않을 수 있다. 이 경우에도 Gate 산출물 또는 결과 요약에 같은 항목을 간단히 남긴다.

## 5. 상태별 출력 규칙

### Completed

완료 조건을 모두 만족했을 때 사용한다.

필수:

- 모든 변경 파일
- 모든 검증 결과
- 증적 위치
- `open_issues: []`

`open_issues`가 남아 있으면 `Completed`로 닫지 않는다. 후속 이슈가 완료 조건에 영향을 주지 않는다고 판단하더라도 이슈 성격과 처리 위치를 `findings`, `change_requests`, `orchestrator_decision_needed` 중 하나로 분류한 뒤 `open_issues`를 비운다.

### Verified

Orchestrator가 worker 결과를 통합하고 담당 검증을 재실행해 Wave 또는 Run 완료 조건을 확인했을 때 사용한다.

필수:

- `open_issues: []`
- 실패/차단/미실행 항목이 `findings`, `change_requests`, `orchestrator_decision_needed`, 또는 후속 Run으로 분류되어 있다.
- Gate 4 QA Pass나 전체 릴리즈 승인과 혼동하지 않는다.

### CompletedWithIssues

주요 목표는 달성했지만 후속 조치가 남았을 때 사용한다.

예:

- API 테스트는 통과했지만 모바일 UI 캡처가 남음
- 구현은 완료했지만 데이터 표준 검토가 별도 Run으로 남음

### Blocked

사용자 질문, scope 승인, 설계 충돌 해소 없이는 진행할 수 없을 때 사용한다.

```yaml
status: Blocked
blocked_reason: "scope.writable 밖의 파일 수정이 필요함"
questions:
  - "DOC-DEV-G2-001 개발표준 문서를 이번 Run 범위에 포함해도 되는가?"
```

### Failed

시도했지만 완료 조건을 만족하지 못했을 때 사용한다.

```yaml
status: Failed
failure:
  command: "python -m pytest tests"
  observed_error: "UT-008 failed with 401 mismatch"
  affected_ids: [UT-008, SEC-002]
  retry_possible: true
```

### AwaitingApproval

Gate 산출물은 정리되었지만 다음 Gate 진행을 위해 사용자 승인이 필요할 때 사용한다.

```yaml
status: AwaitingApproval
approval_request:
  pending: true
  question: "Gate 2 산출물 검토 후 Gate 3 테스트 설계로 진행해도 될까요?"
  approval_recorded: false
  user_approved_at: null
  approval_evidence: null
```

## 6. 검증 결과 작성 규칙

각 검증 결과는 가능하면 다음 필드를 가진다.

```text
id / type / cwd / command / os / exit_code / success_criteria / result / summary / log_path / evidence_path
```

명령 문자열만으로는 불충분하다.
cwd, 성공 기준, exit code, 로그/증적 경로까지 기록해야 Gate 4에서 runner별 해석 차이를 줄일 수 있다.

검증을 실행하지 못했으면 `not_run`으로 기록한다.

```yaml
verification_results:
  - id: UI-003-01
    type: ui_capture
    cwd: repository root
    command: "npx playwright test"
    result: not_run
    reason: "Playwright browser가 설치되지 않음"
    followup: "Playwright 설치 후 재실행"
```

실패한 검증을 성공처럼 쓰지 않는다.
누락 필드와 `passed` 기록은 Gate 4 검수에서 `FIND`로 처리할 수 있다.

권장 `result` 값:

| 값 | 의미 |
| --- | --- |
| `passed` | 검증 통과 |
| `failed` | 검증 실패 |
| `not_run` | 실행하지 못함. `reason` 필수 |
| `environment_blocked` | worker 실행 환경의 권한, 인증, 네트워크, registry, cache 문제로 실행 차단. `reason`, `exit_code`, `log_path`, `followup` 필수 |
| `partial` | 일부만 실행 |

QA 실행 Run에서 `failed`, `not_run`, `environment_blocked` 결과가 있으면 `failure_reports`를 함께 남긴다.

```yaml
failure_reports:
  - qa_stage: QA-001
    failing_command: "npm run build"
    cwd: "frontend"
    exit_code: 1
    observed_error: "Next build failed with module resolution error"
    log_path: docs/artifacts/04-review/evidence/logs/QA-CMD-003_frontend-build.err.log
    reproduction_command: "cd frontend && npm run build"
    impact_ids: [IT-002, NREQ-002]
    candidate_classification: FIND
    orchestrator_decision_needed:
      - "qa-fix-loop로 수정할지 사용자와 협의 필요"
```

## 7. 증적 작성 규칙

증적은 사람이 열어볼 수 있는 경로를 남긴다.

좋은 예:

```yaml
evidence:
  documents:
    - docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md
  files:
    - docs/artifacts/04-review/evidence/ui/UI-001-01_signup_default_desktop.png
```

나쁜 예:

```yaml
evidence:
  files:
    - "캡처함"
```

UI 증적은 상태/시나리오 단위로 남긴다.

```yaml
evidence:
  ui:
    - ui_id: UI-001-01
      scr: SCR-001
      state: "회원가입 기본 화면"
      expected_screen: "이메일, 비밀번호, 비밀번호 확인, 가입 버튼이 보인다."
      expected_path: docs/artifacts/02-design/screen/ui-baseline/signup.html
      actual_path: docs/artifacts/04-review/evidence/ui/UI-001-01_signup_default_desktop.png
      capture_tool: Playwright
      command: "npx playwright test"
      result: passed
```

회원가입 성공 테스트의 기대 화면이 성공 메시지라면 로그인 화면만 있는 캡처는 Pass 증적이 아니다.
이 경우 `failed` 또는 `not_run`으로 기록하고 `FIND`를 남긴다.

UI 캡처 증적은 Playwright 실행으로 생성해야 한다.
CDP, 브라우저 수동 캡처, 런타임 Preview 캡처만 있는 경우 `passed`로 기록하지 않는다.

UIREF 또는 ui-baseline이 UI Implementation Contract로 지정된 화면은 기준 대비 차이를 별도로 남긴다.

```yaml
evidence:
  ui_contract_diffs:
    - compare_id: UICMP-001
      ui_id: UI-001-01
      contract_id: UICON-001
      baseline: docs/artifacts/02-design/screen/ui-baseline/UIREF-001/index.html
      implementation: docs/artifacts/04-review/evidence/ui/UI-001-01_signup_default_desktop.png
      differences:
        - "비밀번호 placeholder가 보안가이드에 따라 8자 이상 문구로 변경됨"
      allowed: true
      action: pass
```

허용되지 않은 차이는 `allowed: false`와 함께 `FIND-` 또는 `CR-` 조치를 연결한다.

## 8. 개발표준 준수 보고

구현 Run은 `development_standards_applied`에 대응하는 `standard_compliance_report`를 남긴다.

```yaml
standard_compliance_report:
  - standard_id: DEV-LOG-001
    status: Pass
    implementation: "표준 logger를 사용했고 민감정보를 로그에 남기지 않았다."
    exception_reason: null
```

`standard_compliance_report`는 worker의 자기 보고다.
최종 승인과 Gate 통과 판단은 Orchestrator 재검증 결과를 기준으로 한다.

## 9. Gate 종료 승인 규칙

각 Gate 종료 Run은 완료 보고 끝에 다음 Gate 진행 승인 질문을 남긴다.
사용자가 명시적으로 승인하기 전까지 다음 Gate 산출물 작성, 구현 착수, QA Pass 확정, 릴리즈 승인 선언을 하지 않는다.

승인 상태 값:

| 값 | 의미 |
| --- | --- |
| `pending` | 승인 질문을 남기고 대기 중 |
| `awaiting-approval` | Gate 산출물 완료 후 사용자 승인 대기 중 |
| `approved` | 대화상 사용자가 명시 승인함 |
| `rejected` | 사용자가 반려함 |
| `deferred` | 보완 후 재확인 필요 |

## 10. 추적성 갱신 규칙

다음 중 하나라도 변경되면 `traceability_updates`를 작성한다.

- 요구사항추적표 상태 변경
- 테스트 결과서 갱신
- 화면 캡처 증적 추가
- 보안항목 검증 결과 변경
- 미해결 이슈 Open/Closed 변경

worker는 전체 추적표나 테스트결과서를 최종 확정하지 않는다.
필요한 갱신은 `owner: orchestrator` 또는 `orchestrator_decision_needed`로 반환한다.

## 11. 사람에게 보여줄 요약

YAML 결과 뒤에는 짧은 한국어 요약을 붙일 수 있다.

```text
요약:
PGM-005 게시글 작성 기능 구현과 테스트를 완료했습니다.
관련 테스트는 모두 통과했고, Orchestrator 재검증이 필요합니다.
남은 이슈는 없습니다.
```

요약은 YAML과 모순되면 안 된다.
