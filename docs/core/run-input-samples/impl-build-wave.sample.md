# Implementation Build Wave Run Input Sample

> 목적: Audit Profile에서 구현 단계가 승인된 설계와 테스트 범위 안에서만 움직이게 하는 기준 예시다.
> 이 샘플은 세 단계로 본다. 먼저 Orchestrator가 Wave를 나누는 `implementation-plan`을 만들고, 신규 개발 또는 큰 고도화에서는 `implementation-scaffold`로 빌드 가능한 계약 skeleton을 만든 뒤, 실제 작업자에게 더 얇은 `build-wave` 계약을 전달한다.

```yaml
profile: "audit"
run_type: "Implementation"
gate: "impl"
skill: "implementation-plan"
persona: "build-planning"
related_ids: [REQ-001, PGM-001, UT-001, IT-001]
target_contracts:
  func: [FUNC-001]
  pgm: [PGM-001]
  api: [API-001]
  db: [DB-001]
  test: [UT-001, IT-001]
development_standards_applied:
  - standard_id: DEV-LOG-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "표준 logger를 사용하고 민감정보, 토큰, 비밀번호, 내부 stack trace를 로그에 남기지 않는다."
  - standard_id: DEV-COMMENT-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "주요 class와 public 업무 method에는 책임, 입력, 출력, 예외, 관련 ID를 JavaDoc/docstring/주석으로 남긴다."
  - standard_id: DEV-TEST-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "테스트는 UT/IT/UI ID와 사람이 읽을 수 있는 입력값, 기대값, 출력값 또는 Given/When/Then 설명을 가진다."
development_standard_checklist:
  logging:
    required: true
    targets: [Controller, Service, SecurityFilter, ControllerAdvice, CoreComponent]
    rule: "SLF4J LoggerFactory 또는 프로젝트 표준 logger를 선언하고 민감정보를 로그에 남기지 않는다."
  comments:
    required: true
    targets: ["주요 class", "public 업무 method", "보안/트랜잭션/권한 판단 method"]
    rule: "책임, 입력, 출력, 예외, 관련 REQ/FUNC/PGM/SEC/UT/IT ID를 JavaDoc/docstring/주석으로 남긴다."
  tests:
    required: true
    targets: ["@Test", "단위 테스트", "통합 테스트", "UI/E2E 테스트"]
    rule: "테스트 이름의 추적 ID만으로 끝내지 않고 @DisplayName 또는 Given/When/Then으로 입력값, 기대값, 출력값을 설명한다."
runner_hint:
  frontend: "claude-cli"
  backend: "codex-cli"
  evidence: "codex-cli"
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/adapters/codex-gpt/skills/implementation-plan.md
  working_documents:
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
  reference_on_demand:
    - docs/core/ID_SYSTEM.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/DELIVERY_PROFILES.md
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
orchestrator_reference:
  - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  - docs/core/TRACEABILITY_RULES.md
  - docs/core/AGENT_RUN_PROTOCOL.md
  - docs/core/ORCHESTRATOR_PROTOCOL.md
  - docs/core/RUN_INPUT_CONTRACT.md
  - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - docs/runs/
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
completion_criteria:
  - "승인된 Gate 2/3 범위 안에서만 구현 또는 구현 계획을 작성한다."
  - "신규 개발 또는 빌드 가능한 골격이 없는 프로젝트는 BW-000 Implementation Scaffold를 첫 Wave로 둔다."
  - "고도화 프로젝트는 BW-000에서 기존 코드와 Program Design의 PGM/IF/MTH 계약을 매핑하고 누락 skeleton 또는 충돌 항목을 식별한다."
  - "코딩 전 개발표준정의서의 패키지 구조, 계층 책임, 로깅, 주석, 예외/메시지, 테스트 명령을 확인하고 준수 체크리스트를 남긴다."
  - "Spring Boot 구현은 개발표준의 base package와 feature 우선 패키지 구조를 따른다. domain 래퍼는 DDD 선택 사유가 있을 때만 사용한다."
  - "로깅은 개발표준의 SLF4J/Logback 또는 Log4j2 선택, logger 선언, 로그 레벨, 민감정보 금지 기준을 따른다."
  - "Java/Spring 주요 클래스와 public 업무 메서드는 개발표준의 JavaDoc/추적 ID 기준을 따른다."
  - "Build Wave 작업지시서에는 `development_standards_applied`와 `development_standard_checklist`를 포함하고, worker는 로깅/주석/테스트 설명 준수 여부를 결과에 남긴다."
  - "화면 구현은 관련 SCR의 UI Implementation Contract와 Gate 3 UI 테스트 기준을 먼저 확인한다."
  - "Build Wave 범위, 소유 파일, 관련 ID, 검증 명령이 명확하다."
  - "Frontend Wave와 Backend Wave가 분리되어 있고, 기본 runner가 각각 claude-cli/codex-cli로 제안되어 있다."
  - "각 worker Run은 기능/프로그램 계약 단위로 분리되고 target_contracts가 명확하다."
  - "10분 내외, 최대 15분은 보조 기준이며, 시간이 부족하다는 이유로 빌드/테스트가 깨진 중간 구현을 완료 처리하지 않는다."
  - "구현 변경은 작성/갱신한 테스트케이스, Orchestrator 재실행 명령, 추적표 갱신 필요 항목과 연결된다."
  - "동시에 active 상태인 Build Wave가 하나만 유지된다."
development_standard_policy:
  required: true
  block_implementation_when_missing:
    - "base package와 backend 패키지 구조"
    - "계층 책임과 금지 의존성"
    - "로깅 API/구현체, logger 선언, 로그 레벨, 민감정보 로그 금지"
    - "클래스/메서드 주석 또는 JavaDoc 기준과 예시"
    - "필수 검증 명령의 cwd, 성공 기준, 결과 기록 위치"
  spring_boot_default:
    package_style: "feature-first"
    domain_wrapper_allowed_only_with_reason: true
    required_top_level_packages:
      - config
      - common
      - security
      - auth
      - user
      - "{featureName}"
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
worker_execution_policy:
  applies_when: "Build Wave가 subagent, codex-cli, claude-cli 등 작업자 runner에게 전달되는 경우"
  role: "worker-runner"
  forbidden_actions:
    - "Gate 전환을 수행하지 않는다."
    - "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다."
    - "사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다."
    - "Orchestrator가 요청하지 않은 신규 Run, PR, 커밋, push를 만들지 않는다."
  required_outputs:
    - "수행한 변경과 검증 결과를 Run 결과에 남긴다."
    - "Gate 전환, session 변경, 최종 승인 판단이 필요하면 Orchestrator 결정 필요 항목으로 반환한다."
ui_implementation_contract_policy:
  impl_checklist:
    - "구현 전 관련 SCR의 UI Implementation Contract를 확인한다."
    - "화면 퍼블리싱 CSS 또는 동등한 레이아웃/class 구조를 재사용했는지 기록한다."
    - "보안가이드 때문에 바꾼 문구, 필드, 흐름은 DEC/ISSUE/FIND/CR 중 하나로 기록한다."
    - "기본/오류/성공/전환 상태가 Gate 3 UI-ID와 연결되어 있는지 확인한다."
    - "구현 결과 screenshot이 기준 UIREF와 비교 가능한 위치에 저장되는지 확인한다."
```

## Review Notes

- 중간 이상 구현은 `implementation-plan`으로 Wave를 먼저 나눈 뒤 `build-wave`로 실행한다.
- 신규 개발 또는 골격이 없는 프로젝트는 실제 feature 구현 전에 `implementation-scaffold` Run으로 빌드 가능한 skeleton을 먼저 만든다.
- 고도화 프로젝트는 `implementation-scaffold` Run에서 기존 코드와 Program Design 계약을 정렬하고, 바로 구현 가능한 public signature가 이미 존재하면 생략 사유를 남긴다.
- 작은 단일 구현은 Wave 분할을 생략할 수 있지만, Orchestrator가 직접 기능 코드를 작성하는 기본 경로가 아니다. native worker(subagent/thread/native branch agent)에게 위임한다.
- `agent-run --mode work`와 `run-exec`는 필수 실행 경로가 아니라 별도 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 선택하는 옵션이다.
- 사용자가 worker 사용을 명시하지 않았다는 점은 Orchestrator 직접 구현 사유가 아니다. 구현 진행 승인이 있으면 별도 요청이 없어도 native worker 위임을 기본 절차로 둔다.
- 직접 구현 예외는 worker/subagent/thread 실행 불가, worker 결과 통합 중 충돌 해결에 필요한 최소 수정, 긴급한 1~2줄 연결 수정, 사용자의 명시적 직접 구현 승인에 한해 허용한다.
- Orchestrator가 직접 수정해야 하면 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 수정 파일, 실행 검증, 후속 검수 필요 여부를 Run에 기록한다.
- 직접 구현 예외는 2개 이하 파일, 약 30 LOC 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능한 경우로 제한한다.
- 3개 이상 파일, 약 100 LOC 이상, 15분 이상 예상, backend/frontend 동시 변경, 새 계약 추가, 테스트 본문 대량 추가가 보이면 Build Wave로 분리한다.
- 실제 `build-wave` 작업자 Run은 이 계획 Run보다 더 좁은 focused source를 사용한다. 전체 설계 산출물을 `working_documents`에 모두 넣지 않고, 현재 Build Wave Run, 개발표준, 관련 테스트케이스 또는 테스트 파일, 필요한 직접 구현 기준만 우선 작업 문서로 둔다.
- API/화면/프로그램/DB/보안 설계는 related ID나 기준 충돌이 있을 때 필요한 문서만 `reference_on_demand`에서 확인한다.
- 추적표와 Core Run 입출력/절차 문서는 worker 입력이 아니라 `orchestrator_reference`로 분리한다. worker는 갱신 필요 항목만 보고하고 Orchestrator가 추적표/session/Wave 상태를 확정한다.
- 작업 범위는 문서 목록이 아니라 `target_contracts`의 기능/프로그램 계약 단위로 닫는다.
- 목표 시간은 10분 내외, 최대 15분 권장이지만 보조 기준이다. 작업 중간에 끊지 않고, 예상 범위가 크면 시작 전에 Run을 더 작게 나눈다.
- 화면 퍼블리싱 기반 화면 구현은 UI Implementation Contract를 먼저 확인하고, 다르면 임의 재설계가 아니라 `FIND` 또는 `CR`로 분류한다.
- 구현자는 Gate 전환, session 변경, 최종 승인 판단, 추적표의 `Implemented`/`Verified` 상태 확정을 하지 않는다. Orchestrator가 worker 결과를 통합하고 worker가 만든 테스트케이스를 재실행한 뒤 추적표 상태를 반영한다.
- Wave 종료 검증은 `target_contracts`와 Gate 3 테스트 설계에 매핑된 테스트까지만 완료 판정한다. 전체 사용자 시나리오, 상태별 화면 증적, QA Pass는 Gate 4에서 판정한다.
- 구현 완료 후 Gate 4 QA로 넘어가기 전 Orchestrator가 구현 범위, 재실행한 테스트 결과, 남은 이슈를 요약하고 승인 질문을 남긴다.
- worker worktree 결과는 손으로 복사하지 않고 `python vulcan.py run-integrate --run-id RUN-NNN --dry-run`으로 scope 위반을 확인한 뒤, 위반이 없을 때만 `--apply`로 반영한다.

## Worker Scaffold 예시

신규 개발의 첫 Impl Wave는 보통 `BW-000`으로 둔다. 이 Run은 업무 로직 구현이 아니라, Program Design의 공개 계약을 실제 파일과 signature로 고정하고 빌드 smoke를 통과시키는 작업이다.

```yaml
profile: "audit"
run_type: "ImplementationScaffold"
gate: "impl"
skill: "implementation-scaffold"
persona: "build"
bw_id: "BW-000"
related_ids: [PGM-001, PGM-002, API-001, API-002, API-003, API-004, SCR-001, UT-001, IT-001, UI-001-01]
target_contracts:
  pgm: [PGM-001, PGM-002]
  api: [API-001, API-002, API-003, API-004]
  scr: [SCR-001]
  test: [UT-001, IT-001, UI-001-01]
  interface_contract:
    language: "python, typescript"
    signatures:
      - "TodoService.list_todos() -> list[TodoOut]"
      - "TodoService.create_todo(request: TodoCreate) -> TodoOut"
      - "TodoService.update_todo_completed(todo_id: int, request: TodoUpdate) -> TodoOut"
      - "TodoService.delete_todo(todo_id: int) -> None"
      - "fetchTodos(): Promise<Todo[]>"
      - "addTodo(text: string): Promise<Todo>"
      - "setCompleted(id: number, completed: boolean): Promise<Todo>"
      - "removeTodo(id: number): Promise<void>"
    schemas:
      - "TodoCreate: text"
      - "TodoUpdate: completed"
      - "TodoOut/Todo: id, text, completed, createdAt, updatedAt"
    error_contracts:
      - "TODO_TEXT_REQUIRED"
      - "TODO_TEXT_TOO_LONG"
      - "TODO_NOT_FOUND"
  contract_skeleton:
    mode: "new"
    files:
      - path: "backend/app/services/todos.py"
        create: "TodoService class and public method stubs"
      - path: "backend/app/schemas/todos.py"
        create: "TodoCreate, TodoUpdate, TodoOut"
      - path: "frontend/shared/api/todos.ts"
        create: "Todo type and API client signatures"
      - path: "frontend/features/todo/useTodos.ts"
        create: "useTodos state/action return shape"
    forbidden:
      - "업무 로직 완성"
      - "전체 E2E 또는 Gate 4 QA Pass 선언"
    smoke_commands:
      - "python -m compileall backend/app"
      - "cd frontend && npm run build"
development_standards_applied:
  - standard_id: DEV-LOG-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "표준 logger를 사용하고 민감정보를 로그에 남기지 않는다."
  - standard_id: DEV-COMMENT-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "주요 class와 public 업무 method에는 책임, 입력, 출력, 예외, 관련 ID를 JavaDoc/docstring/주석으로 남긴다."
  - standard_id: DEV-TEST-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "테스트는 UT/IT/UI ID와 사람이 읽을 수 있는 입력값, 기대값, 출력값 또는 Given/When/Then 설명을 가진다."
development_standard_checklist:
  logging:
    required: true
    targets: [Controller, Service, SecurityFilter, ControllerAdvice, CoreComponent]
    rule: "담당 skeleton 대상에 logger 선언이 필요한 위치를 표시하고 민감정보 로그 금지 기준을 남긴다."
  comments:
    required: true
    targets: ["주요 class", "public 업무 method"]
    rule: "skeleton class/method에 책임, 입력, 출력, 예외, 관련 ID를 JavaDoc/docstring/주석 기준으로 남긴다."
  tests:
    required: true
    targets: ["test stub"]
    rule: "다음 Build Wave가 채울 테스트 stub에는 UT/IT/UI ID와 Given/When/Then 또는 입력/기대/출력 설명을 남긴다."
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/adapters/codex-gpt/skills/implementation-scaffold.md
  working_documents:
    - docs/runs/RUN-020_bw-000-contract-skeleton_v0.1.md
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
  reference_on_demand:
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
scope:
  writable:
    - backend/
    - frontend/
    - docs/runs/RUN-020_bw-000-contract-skeleton_v0.1.md
  excluded:
    - session.json
    - docs/ref-docs/
    - "**/*.db"
    - "**/node_modules/"
    - "**/.next/"
completion_criteria:
  - "Program Design의 PGM/IF/MTH/DTO public contract가 실제 skeleton 파일에 존재한다."
  - "업무 로직은 TODO/stub/NotImplemented 또는 최소 wiring만 포함한다."
  - "compile/import/build smoke가 통과한다."
  - "다음 Build Wave가 구현할 method와 테스트 stub가 식별되어 있다."
verification:
  owner: "orchestrator-rerun"
  commands:
    - "python -m compileall backend/app"
    - "cd frontend && npm run build"
    - "python vulcan.py run-check docs/runs/RUN-020_bw-000-contract-skeleton_v0.1.md"
dependency_install_policy:
  worker_cache_required: true
  npm_cache_env: "npm_config_cache"
  playwright_cache_env: "PLAYWRIGHT_BROWSERS_PATH"
  if_install_blocked: "verification_results에 environment_blocked 또는 not_run으로 기록하고 Orchestrator 재실행 명령을 남긴다."
  worker_node_playwright_scope: "worker worktree의 npm/build/Playwright는 skeleton smoke 보조 검증이다. 최종 UI/Playwright 증적은 Gate 4에서 통합본 기준으로 판정한다."
worker_execution_policy:
  forbidden_actions:
    - "업무 기능 로직을 완성하지 않는다."
    - "Gate 전환, session 변경, wave-complete, sync-session, prepare-transition, check-trace를 직접 실행하지 않는다."
    - "scope.writable 밖 파일을 수정하지 않는다."
```

## Worker Build Wave 예시

작업자 runner에게 전달되는 실제 `build-wave` Run은 더 좁아야 한다.
아래 예시는 frontend 담당 worker 기준이며, backend worker라면 `frontend/`를 `backend/`와 해당 테스트 경로로 바꾼다.

```yaml
profile: "audit"
run_type: "Implementation"
gate: "impl"
skill: "build-wave"
persona: "build"
related_ids: [REQ-001, SCR-001, UI-001, UT-001]
target_contracts:
  func: [FUNC-001]
  pgm: [PGM-002]
  api: [API-001, API-002, API-003, API-004]
  scr: [SCR-001]
  ui: [UI-001]
  test: [UT-001]
  interface_contract:
    language: "typescript"
    signatures:
      - "fetchTodos(): Promise<Todo[]>"
      - "addTodo(text: string): Promise<Todo>"
      - "setCompleted(id: number, completed: boolean): Promise<Todo>"
      - "removeTodo(id: number): Promise<void>"
    schemas:
      - "Todo: id, text, completed, createdAt, updatedAt"
    error_contracts:
      - "UI error state must not expose stack, SQL, DB path, token, or internal exception details."
development_standards_applied:
  - standard_id: DEV-LOG-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "표준 logger를 사용하고 민감정보를 로그에 남기지 않는다."
  - standard_id: DEV-COMMENT-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "주요 class와 public 업무 method에는 책임, 입력, 출력, 예외, 관련 ID를 JavaDoc/docstring/주석으로 남긴다."
  - standard_id: DEV-TEST-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "테스트는 UT/IT/UI ID와 사람이 읽을 수 있는 입력값, 기대값, 출력값 또는 Given/When/Then 설명을 가진다."
development_standard_checklist:
  logging:
    required: true
    targets: [API client, state store, error boundary]
    rule: "프론트엔드는 사용자 화면/콘솔에 민감정보, token, stack, SQL/DB path를 남기지 않는다."
  comments:
    required: true
    targets: ["복잡한 상태 전이", "권한 가드", "API 오류 변환"]
    rule: "단순 렌더링 설명은 반복하지 않고, 보안 판단/상태 전이/예외 사유와 관련 ID를 주석으로 남긴다."
  tests:
    required: true
    targets: ["unit test", "component test", "Playwright test"]
    rule: "테스트는 UI/UT/IT ID와 입력값, 기대 화면/상태, 실제 확인 결과를 @DisplayName 또는 Given/When/Then으로 설명한다."
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/adapters/codex-gpt/skills/build-wave.md
  working_documents:
    - docs/runs/RUN-022_bw-001-frontend-구현-claude_v0.1.md
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
    - docs/artifacts/02-design/screen/ui-baseline/
  reference_on_demand:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
orchestrator_reference:
  - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  - docs/core/TRACEABILITY_RULES.md
  - docs/core/AGENT_RUN_PROTOCOL.md
  - docs/core/RUN_INPUT_CONTRACT.md
  - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - frontend/
    - docs/artifacts/04-review/evidence/ui/
    - docs/runs/RUN-022_bw-001-frontend-구현-claude_v0.1.md
  readonly:
    - docs/core/
    - docs/templates/
    - docs/seed-docs/reference-standards/
  excluded:
    - session.json
    - docs/ref-docs/
    - backend/
    - "**/node_modules/"
    - "**/.next/"
completion_criteria:
  - "담당 Wave 범위만 구현하고 다른 worker 범위는 수정하지 않는다."
  - "target_contracts의 기능/화면/UI/테스트 계약을 완결된 조각으로 닫는다."
  - "target_contracts.interface_contract의 public signature, schema, error contract를 다른 이름이나 타입으로 대체하지 않는다."
  - "development_standards_applied와 development_standard_checklist를 코드/테스트 작성 체크리스트로 사용하고 준수/예외를 Run 결과에 남긴다."
  - "UI Implementation Contract와 Gate 3 UI 테스트 기준을 구현 전 확인한다."
  - "10분 내외, 최대 15분은 보조 기준이며, 시간이 부족하다는 이유로 깨진 중간 구현을 완료 처리하지 않는다."
  - "담당 테스트케이스를 작성/갱신하고 Orchestrator가 재실행할 테스트, 린트, 빌드 명령을 현재 Run에 남긴다."
  - "Wave 검증은 담당 계약 테스트와 가능한 회귀 검증까지만 의미하며, 전체 E2E/QA Pass로 보고하지 않는다."
  - "가능하면 worker self-check를 실행하고, 실행하지 못하면 Not Run 사유를 남긴다."
  - "worker worktree에서 npm/build/Playwright를 못 실행해도 그 사실만으로 구현 실패를 확정하지 않고 environment_blocked/not_run과 Orchestrator 재실행 명령을 남긴다."
  - "PoC profile에서 run-preflight/run-check가 비차단 경고만 남기면 경고 제거를 반복하지 않고 경고 내용과 후속 판단 필요 항목을 보고한다."
  - "PoC profile의 Impl Build worker는 코드, dependency manifest, 빠른 self-check에 집중하고 README, 최종 테스트 결과서, browser smoke/screenshot, release/backlog, 증적 정규화는 Gate 4/5 또는 별도 worker로 넘긴다."
  - "추적표 또는 session 갱신 필요 항목은 Orchestrator 결정 필요 항목으로 반환하고, Implemented/Verified 상태를 직접 확정하지 않는다."
verification:
  owner: "orchestrator-rerun"
  commands:
    - "python vulcan.py run-preflight docs/runs/RUN-022_bw-001-frontend-구현-claude_v0.1.md"
    - "npm run lint"
    - "npm run build"
    - "python vulcan.py run-check docs/runs/RUN-022_bw-001-frontend-구현-claude_v0.1.md"
  evidence:
    required: true
    target_documents:
      - docs/runs/RUN-022_bw-001-frontend-구현-claude_v0.1.md
      - docs/artifacts/04-review/evidence/ui/
dependency_install_policy:
  worker_cache_required: true
  npm_cache_env: "npm_config_cache"
  playwright_cache_env: "PLAYWRIGHT_BROWSERS_PATH"
  if_install_blocked: "npm install/npm ci/npx playwright install이 권한, 인증, 네트워크, registry, cache 문제로 막히면 코드 실패로 단정하지 않고 environment_blocked로 보고한다."
  worker_node_playwright_scope: "worker self-check는 보조 검증이다. 화면 서버 실행과 Playwright 최종 증적은 workflow.integration_branch 기준 QA-000 workspace의 Gate 4에서 판정한다."
worker_execution_policy:
  forbidden_actions:
    - "Gate 전환, session 변경, wave-complete, sync-session, prepare-transition, check-trace를 직접 실행하지 않는다."
    - "사용자 승인, QA Pass, merge 가능 여부를 최종 판단하지 않는다."
    - "scope.writable 밖 파일을 수정하지 않는다."
  completion_rules:
    - "이 Run의 target_contracts만 완결한다."
    - "빌드 또는 담당 테스트가 깨진 상태를 완료로 보고하지 않는다."
    - "범위가 너무 크면 중간 구현하지 말고 Orchestrator 결정 필요 항목으로 반환한다."
```

