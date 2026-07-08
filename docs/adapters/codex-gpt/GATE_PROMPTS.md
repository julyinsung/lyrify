# Codex/GPT Gate Prompts

> 목적: Codex/GPT runner가 Vulcan-Anvil Ex Core 규칙을 실행할 때 사용할 얇은 Gate별 체크리스트를 제공한다.

## 1. 사용 방식

이 문서는 Core 규칙을 대체하지 않는다.
Codex/GPT 실행 시에는 먼저 현재 Gate와 Run 입력을 확인하고, 필요한 Core 문서와 skill 카드만 읽는다.

필수 Core:

- `docs/core/ORCHESTRATOR_PROTOCOL.md`
- `docs/core/GATE_EXECUTION_CHECKLIST.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/INDEPENDENT_EXECUTION_PROCESS.md`

출력은 `docs/core/RUN_OUTPUT_CONTRACT.md`를 따른다.

## 2. 공통 체크

- `session.json.current_gate`, 사용자 요청, 관련 Run을 먼저 확인한다.
- 현재 Gate보다 앞선 산출물, 구현, 테스트, 증적을 사용자 승인 없이 만들지 않는다.
- 의미 있는 변경은 관련 `REQ/AC/FUNC/SCR/PGM/API/DB/SEC/UT/IT/UI/FIND/CR/RUN`과 연결한다.
- 실행하지 않은 테스트를 Pass로 기록하지 않는다.
- 전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기억은 현재 프로젝트의 근거로 사용하지 않는다. 현재 `session.json`, Run 문서, Gate 산출물, 사용자 최신 지시로 다시 확인한다.
- Gate 산출물 완료 후에는 요약, 미해결 항목, 다음 제안, 사용자 승인 질문을 남기고 멈춘다.
- `docs/ref-docs/`는 민감 자료일 수 있으므로 커밋하거나 원문 인용하지 않는다.
- Claude 전용 `.claude/` 문서는 Codex 실행 계약으로 보지 않는다.

## 3. Gate별 체크리스트

| Gate | 목표 | 확인할 Core/Skill |
| --- | --- | --- |
| Phase 0 | 목표, 사용자, 제약, 질문, 위험, 가정을 정리한다 | `AGENT_RUN_PROTOCOL.md`, `DELIVERY_PROFILES.md` |
| Gate 1 | 테스트 가능한 `REQ/NREQ/AC`와 추적표를 만든다 | `TRACEABILITY_RULES.md`, `ID_SYSTEM.md` |
| Gate 2 | 요구사항을 아키텍처, 화면, 기능, API, DB, 보안, 개발표준으로 전개한다 | `GATE2_DESIGN_SEQUENCE.md`, `screen-design`, `security-review`, `development-standard-review`, `data-standard-review` |
| Gate 3 | 요구사항, 보안, UI 계약을 검증 가능한 테스트와 증적 기준으로 전개한다 | `TRACEABILITY_RULES.md`, `RUN_INPUT_CONTRACT.md` |
| Impl | 승인된 Build Wave 범위 안에서 구현하고 테스트, 증적, 추적성 delta를 남긴다 | `implementation-plan`, `implementation-scaffold`, `build-wave`, `TECH_STACK_BASELINES.md` |
| Gate 4 | 테스트 결과, Playwright 증적, 추적성, FIND/CR/ISSUE를 검수한다 | `CHANGE_CONTROL_PROCESS.md`, `traceability-review`, `ui-review` |
| Gate 5 | 릴리즈 승인 근거, 잔여 위험, 인수인계 항목을 정리한다 | `DOCUMENT_METADATA.md`, `CHANGE_CONTROL_PROCESS.md` |

## 4. Gate별 핵심 주의

### Phase 0

- 즉시 구현하지 않는다.
- 확정되지 않은 내용은 질문, 가정, 위험, Backlog 후보로 분리한다.

### Gate 1

- 요구사항과 인수기준을 설계/구현 상세로 밀어 넣지 않는다.
- `Given/When/Then`, 선행조건, 테스트 데이터는 Gate 3 입력으로 넘긴다.

### Gate 2

- `docs/core/GATE2_DESIGN_SEQUENCE.md`의 순서를 따른다.
- SW Architecture는 Draft로 시작하고 상세 설계를 거쳐 Baseline 후보로 보강한다.
- 화면 퍼블리싱 산출물이나 UIREF가 있으면 단순 참고인지 구현 기준인지 분류하고, 구현 기준이면 UI Implementation Contract를 작성한다.
- 보안가이드와 개발표준은 구현자가 바로 사용할 수 있는 정책값, 적용 위치, 검증 명령을 가진다.

### Gate 3

- UI 테스트는 화면 단위가 아니라 상태/시나리오 단위로 나눈다.
- 명령 기반 테스트는 cwd, Windows/POSIX 명령, 성공 기준, 로그/증적 경로를 가진다.
- 보안가이드에 없는 정책값을 테스트가 새로 만들지 않는다.

### Impl

- Orchestrator는 구현 주 작성자가 아니다.
- 작은 기능, 단일 파일, 단일 테스트 변경이라도 먼저 worker Run 또는 Build Wave Run을 만들고 native worker(subagent/thread/native branch agent)에게 위임한다. `agent-run --mode work`와 `run-exec`는 별도 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 선택한다.
- Orchestrator가 직접 코드를 수정해야 하면 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 실행 검증, 후속 검수 필요 여부를 Run에 남긴다.
- Build Wave가 있으면 현재 `BW-ID` 범위만 수행한다.
- 신규 개발 또는 빌드 가능한 골격이 없으면 feature 구현 전 `implementation-scaffold`로 class/interface/method/DTO skeleton과 build smoke를 먼저 만든다.
- `build-wave` Run은 Program Design의 public signature를 `target_contracts.interface_contract`로 가져온 뒤 실행한다.
- 개발표준, 보안가이드, 테스트케이스가 비어 있으면 구현 완료로 선언하지 않는다.
- 화면 구현 전 UI Implementation Contract와 Gate 3 UI 테스트 기준을 확인한다.

### Gate 4

- 테스트 실행과 증적 수집은 가능하면 `qa-execution` worker Run으로 분리한다.
- Gate 4 QA는 `QA-000` 환경 준비/스모크, `QA-001` 명령 기반 검증, `QA-002` UI/E2E 증적, `QA-003` 결과 정리/판정 후보 순서로 나눈다.
- `QA-000`에서 통합 소스, 의존성, DB/포트/환경변수, backend/frontend 기동, Playwright 설치 가능성을 먼저 확인하고 후속 QA Run이 재사용할 QA workspace 경로를 기록한다. 기본 workspace는 `workflow.integration_branch`의 현재 작업공간이다.
- `QA-001`, `QA-002`, `QA-003`은 `QA-000`이 기록한 같은 QA workspace에서 실행한다.
- Orchestrator는 실패를 발견해도 즉시 코드를 수정하지 않고 원인, 재현 명령, 로그, 영향 ID를 기록한 뒤 사용자와 처리 방향을 협의한다.
- 수정이 승인된 설계 범위 안이면 별도 `qa-fix-loop` Run으로 처리한다.
- 화면 증적 Pass는 Playwright 결과를 기준으로 한다.
- CDP 캡처, 브라우저 수동 캡처, Preview 캡처만으로 UI Pass를 확정하지 않는다.
- 승인된 범위 안의 결함은 `FIND`, 기준선 변경은 `CR`, 판단 보류는 `ISSUE`로 남긴다.

### Gate 5

- Release Approval과 CR을 혼동하지 않는다.
- 미해결 Open 항목이 있으면 승인 완료로 선언하지 않는다.

## 5. 완료 응답 형식

```text
완료 요약:
- ...

변경 파일:
- ...

검증:
- cwd / command / exit code / result / evidence

미해결:
- ...

다음 제안:
- ...

승인 질문:
- ...
```
