# Run Input Contract

> 상태: v0.4
> 목적: Codex, Claude, Gemini 등 모든 worker runner가 동일하게 읽는 공통 작업지시서 형식을 정의한다.

## 1. 개념

Run Input Contract는 Orchestrator가 worker에게 전달하는 공통 작업지시서다.

Runner 종류가 달라도 worker는 같은 계약을 읽고 같은 방식으로 움직여야 한다.
Adapter는 이 계약을 런타임별 CLI 호출, 프롬프트, 로그, 상태파일로 변환할 뿐이며 계약 형식을 따로 정의하지 않는다.

이 계약의 목적은 다음을 줄이는 것이다.

```text
작업 범위 확장
문서 누락
임의의 class/method/schema 생성
테스트 없는 완료 선언
worker별 다른 구현 구조
전역 memory 또는 과거 샘플 프로젝트 기억의 현재 Run 오염
```

## 2. 문서 사용 경계

이 문서는 하나만 유지한다.
다만 내부에서 두 영역을 명확히 나눈다.

| 영역 | 대상 | 용도 |
| --- | --- | --- |
| Worker 입력 계약 | worker runner | 실제 Run 문서의 YAML 또는 작업지시 블록으로 전달한다. |
| Orchestrator 작성/검증 규칙 | Orchestrator, `vulcan.py`, adapter | worker 입력 계약을 생성, 축약, 검증, 전달할 때 사용한다. worker payload에 장문으로 반복하지 않는다. |

worker에게는 가능한 한 `3. Worker 입력 계약`과 해당 Run에 필요한 보조 블록만 전달한다.

worker 실행 전 Orchestrator는 `python vulcan.py run-preflight <run-file>`로 현재 Run 입력 계약을 사전 검사한다. `wave-start`와 `run-new --skill build-wave`는 Run 초안 생성 직후 preflight 경고/차단 항목을 안내한다. `run-exec`와 `agent-run --mode work`는 preflight를 자동 실행하고 차단 항목이 있으면 worker 실행을 시작하지 않는다. native subagent/thread/Agy Workspace: branch 위임은 이 자동 실행 경로를 타지 않으므로 Orchestrator가 위임 전에 직접 `run-preflight`를 실행해야 한다. `prepare-transition`은 완료된 worker Run에 대한 사후 안전망으로 preflight를 다시 확인하지만, 위임 전 preflight를 대체하지 않는다. `run-preflight`는 완성된 구현 결과를 판단하지 않고, worker가 scope 밖으로 나가거나 Gate/session/추적표 확정을 직접 수행할 위험이 있는지 확인한다.

Build Wave Run이나 구현 worker Run을 생성할 때 대표 상세 ID가 있으면 Orchestrator는 `run-new --trace-seed <ID>` 또는 `wave-start --trace-seed <ID>`를 우선 사용한다. 이 옵션은 추적성 그래프에서 `related_ids`, `target_contracts`, `source_documents.reference_on_demand`를 추천하지만, `interface_contract`, `contract_skeleton`, `scope.writable`, 검증 명령은 Orchestrator가 Program Design과 실제 작업 범위에 맞게 확정해야 한다.
`6. 작성/검증 규칙` 이후의 내용은 Orchestrator와 도구가 보는 작성 기준이다.

Run 입력 계약 형식은 runner별로 나누지 않는다. 대신 `source_documents.read_first`만 adapter에 맞게 달라진다. 모든 runner는 `docs/core/GATE_EXECUTION_CHECKLIST.md`를 공통으로 읽고, Codex는 `docs/adapters/codex-gpt/GATE_PROMPTS.md`, Claude는 `docs/adapters/claude/GATE_PROMPTS.md`, Gemini/Antigravity는 `docs/adapters/gemini/GATE_PROMPTS_GEMINI.md`를 추가로 읽는다. 한 runner의 전용 prompt를 다른 runner의 Run 입력에 섞지 않는다.

## 3. Worker 입력 계약

### 3.1 필수 필드

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `run_id` | 예 | 실행 단위 ID. 예: `RUN-001` |
| `persona` | 예 | 표준 작업 persona. 예: `requirements`, `design`, `build`, `review` |
| `skill` | 권장 | worker가 사용할 작업 절차 카드. 예: `build-wave`, `traceability-review` |
| `run_type` | 예 | `Discovery`, `Design`, `Implementation`, `ImplementationScaffold`, `QAFix`, `Test`, `Evidence`, `Review` |
| `gate` | 예 | 현재 Gate. 예: `gate2`, `impl`, `gate4` |
| `goal` | 예 | 이번 Run에서 달성할 구체 목표 |
| `related_ids` | 예 | 요구사항, 설계, 보안, 테스트 ID |
| `target_contracts` | 구현/검수 Run 필수 | 이번 Run이 닫을 기능/프로그램/API/DB/보안/테스트 계약 묶음 |
| `source_documents` | 예 | 먼저 읽을 문서, 작업 대상 문서, 필요 시 참고 문서 |
| `orchestrator_reference` | worker Run 권장 | worker 입력이 아니라 Orchestrator가 결과 통합/추적성/상태 갱신 판단에 사용할 운영 문서 |
| `scope` | 예 | 수정 가능/읽기 전용/제외 경로 |
| `completion_criteria` | 예 | 완료 판정 조건 |
| `verification` | 예 | worker self-check 또는 Orchestrator 재실행 검증 명령 |
| `development_standards_applied` | 구현 Run 권장 | 이번 Run에 직접 적용할 개발표준 규칙 ID |
| `output_requirements` | 예 | 결과 보고 형식과 포함 항목 |

### 3.2 보조 필드

| 필드 | 넣는 경우 |
| --- | --- |
| `target_contracts.interface_contract` | 구현 Run과 scaffold Run에서는 필수. worker가 구현할 public interface, method signature, schema를 고정한다. |
| `target_contracts.contract_skeleton` | Impl 첫 scaffold Run 또는 기존 코드 정렬 Run에서 필수. 생성/확인할 뼈대 파일과 public signature를 고정한다. |
| `trace_context` | `--trace-seed`로 Run 초안을 만들었을 때. seed, depth, direction, source를 남겨 관련 ID 추천 근거를 추적한다. |
| `verification.test_cases_stub` | 구현 Run과 scaffold Run에서 권장. worker가 작성하거나 통과시켜야 할 테스트 함수/파일/검증 의도를 고정한다. |
| `dependency_install_policy` | Node/Playwright 같은 외부 의존성 설치가 worker self-check에 필요할 때. cache env와 설치 차단 시 보고 기준을 명시한다. |
| `ui_evidence_policy` | UI 테스트, 화면 캡처, Playwright 증적이 이번 Run의 직접 결과일 때 |
| `ui_implementation_contract_policy` | UIREF/ui-baseline을 기준으로 구현 또는 검수할 때 |
| `qa_execution_policy` | Gate 4에서 worker가 테스트 실행, 로그, 화면 증적, 후보 FIND/CR/ISSUE를 수집할 때 |
| `qa_failure_report_contract` | Gate 4 QA worker가 실패/미실행/환경 차단을 구조화해 보고해야 할 때 |
| `delegation_record_policy` | subagent/thread/native branch agent처럼 외부 CLI 실행 로그가 없는 위임을 추적해야 할 때 |
| `gate_exit_policy` | Orchestrator Run이 Gate 종료와 사용자 승인 질문을 직접 다룰 때 |
| `worker_execution_policy` | 기본 worker 금지사항을 Run 안에 명시적으로 재기입해야 할 때 |
| `question_policy` / `security_policy` | 프로젝트별 질문/보안 예외가 기본 Core 규칙보다 더 좁거나 다를 때 |

## 4. 권장 YAML 골격

권장 YAML은 Run 문서 전체가 아니라 worker가 바로 실행할 수 있는 입력 계약 골격이다.
실제 Run에는 이번 작업에 필요한 값만 채우고, 장문의 정책 전문은 반복해서 넣지 않는다.

```yaml
run_id: RUN-000
persona: <persona>
skill: <skill>
run_type: <Discovery|Design|Implementation|ImplementationScaffold|QAFix|Test|Evidence|Review>
gate: <phase0|gate1|gate2|gate3|impl|gate4|gate5>
goal: "<이번 Run의 한 문장 목표>"

related_ids:
  req: []
  ac: []
  func: []
  scr: []
  pgm: []
  api: []
  db: []
  sec: []
  test: []

target_contracts:
  func: []
  pgm: []
  api: []
  db: []
  sec: []
  test: []
  interface_contract:
    language: ""
    signatures: []
    schemas: []
    error_contracts: []
  contract_skeleton:
    mode: "<new|existing-alignment|not-required>"
    files: []
    smoke_commands: []

development_standards_applied:
  - standard_id: DEV-000
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "<이번 Run에서 반드시 지킬 개발표준 규칙>"

source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - <현재 Run 문서>
    - <현재 skill 문서>
  working_documents:
    - <이번 Run에서 직접 작성/갱신/실행 기준으로 삼을 문서>
  reference_on_demand:
    - <필요할 때만 펼칠 요구사항/설계/테스트 기준 산출물>

orchestrator_reference:
  - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  - docs/core/TRACEABILITY_RULES.md
  - docs/core/AGENT_RUN_PROTOCOL.md
  - docs/core/RUN_INPUT_CONTRACT.md
  - docs/core/RUN_OUTPUT_CONTRACT.md

scope:
  writable:
    - <수정 허용 경로>
  readonly:
    - docs/core/
  excluded:
    - session.json
    - docs/ref-docs/

completion_criteria:
  - "<완료 판정 기준>"

verification:
  owner: orchestrator-rerun
  commands:
    - "<검증 명령>"
  test_cases_stub:
    - id: UT-000
      file: "<테스트 파일 경로>"
      test_name: "<테스트 함수명>"
      description: "<검증 의도>"
      required_assertions: []

output_requirements:
  format: RUN_OUTPUT_CONTRACT.md
  include:
    - changed_files
    - related_ids
    - verification_results
    - delegation_records
    - standard_compliance_report
    - open_issues
    - orchestrator_decision_needed
```

`delegation_records`는 외부 CLI runner뿐 아니라 Codex subagent, Codex thread, Claude subagent, Agy workspace branch agent 같은 native 위임에도 사용한다. 외부 CLI runner는 별도의 `Run Execution Record`와 stderr/jsonl/summary 파일을 남길 수 있지만, subagent/thread는 그 수준의 프로세스 메타가 없을 수 있다. 이 경우에도 위임 대상, 작업 범위, 변경 파일, 결과 요약, Orchestrator 재검증 명령은 반드시 남긴다.

## 5. 구현 worker 예시

구현 worker 예시는 실제 구현에 필요한 문서만 넣는다.
요구사항정의서, 기능명세서, 프로그램 설계서, API/DB/보안/화면 설계서는 `target_contracts` 확인이 필요할 때만 `reference_on_demand`에서 펼친다.
추적표와 Core Run 입출력/절차 문서는 worker 입력이 아니라 `orchestrator_reference`로 분리한다.

### 5.1 Scaffold worker 예시

신규 개발 또는 큰 고도화에서는 기능 구현 전에 `ImplementationScaffold` Run을 먼저 만든다.
이 Run은 업무 로직을 완성하지 않고, Program Design의 `PGM/IF/MTH/DTO` 계약을 실제 파일과 public signature로 고정하고 build/import smoke를 통과시키는 것이 목적이다.

```yaml
run_id: RUN-020
persona: build
skill: implementation-scaffold
run_type: ImplementationScaffold
gate: impl
goal: "Todo 앱의 backend/frontend 계약 skeleton을 생성하고 빌드 smoke를 통과시킨다."

related_ids:
  pgm: [PGM-001, PGM-002]
  api: [API-001, API-002, API-003, API-004]
  scr: [SCR-001]
  test: [UT-001, IT-001, UI-001-01]

target_contracts:
  pgm: [PGM-001, PGM-002]
  api: [API-001, API-002, API-003, API-004]
  test: [UT-001, IT-001, UI-001-01]
  interface_contract:
    language: "python, typescript"
    signatures:
      - "class TodoService"
      - "TodoService.list_todos() -> list[TodoOut]"
      - "TodoService.create_todo(request: TodoCreate) -> TodoOut"
      - "fetchTodos(): Promise<Todo[]>"
      - "addTodo(text: string): Promise<Todo>"
      - "setCompleted(id: number, completed: boolean): Promise<Todo>"
      - "removeTodo(id: number): Promise<void>"
    schemas:
      - "TodoCreate: text"
      - "TodoUpdate: completed"
      - "TodoOut: id, text, completed, createdAt, updatedAt"
    error_contracts:
      - "TODO_TEXT_REQUIRED"
      - "TODO_TEXT_TOO_LONG"
      - "TODO_NOT_FOUND"
  contract_skeleton:
    mode: new
    files:
      - path: backend/app/services/todos.py
        create: "TodoService class and public method stubs only"
      - path: backend/app/schemas/todos.py
        create: "TodoCreate, TodoUpdate, TodoOut schemas"
      - path: frontend/shared/api/todos.ts
        create: "Todo type and API client function signatures"
      - path: frontend/features/todo/useTodos.ts
        create: "useTodos hook return shape"
    forbidden:
      - "업무 로직 완성"
      - "전체 E2E Pass 선언"
    smoke_commands:
      - "python -m compileall backend/app"
      - "cd frontend && npm run build"

scope:
  writable:
    - backend/
    - frontend/
    - docs/runs/RUN-020_todo-contract-skeleton_v0.1.md
  excluded:
    - session.json
    - docs/ref-docs/
    - "**/*.db"
    - "**/node_modules/"

completion_criteria:
  - "Program Design의 public signature가 실제 파일에 존재한다."
  - "업무 로직은 stub/TODO/NotImplemented 또는 최소 wiring만 포함한다."
  - "compile/import/build smoke가 통과한다."
  - "다음 Build Wave가 채울 method와 테스트 stub가 식별되어 있다."
```

### 5.2 Feature worker 예시

```yaml
run_id: RUN-021
persona: build
skill: build-wave
run_type: Implementation
gate: impl
goal: "PGM-005 게시글 작성 기능을 구현하고 담당 테스트케이스를 만든다."

related_ids:
  func: [FUNC-005]
  pgm: [PGM-005]
  api: [API-005]
  db: [DB-002]
  sec: [SEC-002, SEC-004]
  test: [UT-007, IT-004]

target_contracts:
  func: [FUNC-005]
  pgm: [PGM-005]
  api: [API-005]
  db: [DB-002]
  sec: [SEC-002, SEC-004]
  test: [UT-007, IT-004]
  interface_contract:
    language: python
    signatures:
      - name: create_post
        signature: "def create_post(db: Session, request: PostCreateRequest) -> PostResponse"
        rules:
          - "제목과 본문은 빈 값일 수 없다."
          - "작성 성공 시 생성된 게시글 ID와 생성 시각을 반환한다."
    schemas:
      - name: PostCreateRequest
        fields:
          title: "str, required, max_length=100"
          body: "str, required, max_length=4000"
    error_contracts:
      - code: VALIDATION_FAILED
        condition: "title 또는 body가 비어 있거나 길이 제한을 초과한다."
        status: 422

development_standards_applied:
  - standard_id: DEV-DIR-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "정해진 Router -> Service -> Repository 구조를 따른다."
  - standard_id: DEV-ERR-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "공통 오류 응답 포맷과 글로벌 예외 매핑을 사용한다."

source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/adapters/codex-gpt/skills/build-wave.md
  working_documents:
    - docs/runs/RUN-021_pgm-005-게시글-작성-구현_v0.1.md
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - tests/test_posts.py
  reference_on_demand:
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md

scope:
  writable:
    - src/api/posts.py
    - src/services/post_service.py
    - tests/test_posts.py
    - docs/runs/RUN-021_pgm-005-게시글-작성-구현_v0.1.md
  readonly:
    - docs/core/
    - docs/templates/
  excluded:
    - session.json
    - docs/ref-docs/
    - "**/*.db"
    - "**/__pycache__/"

completion_criteria:
  - "target_contracts의 기능/프로그램/API/DB/보안/테스트 계약을 완결된 조각으로 닫는다."
  - "interface_contract의 public signature, schema, error contract와 구현이 모순되지 않는다."
  - "담당 테스트케이스를 작성/갱신하고 Orchestrator가 재실행할 검증 명령을 남긴다."
  - "Wave/worker 검증은 담당 계약 테스트와 가능한 회귀 검증까지만 의미하며, 전체 E2E/QA Pass로 보고하지 않는다."
  - "추적표, session, Gate 전환 필요 항목은 Orchestrator 결정 필요 항목으로 반환한다."

verification:
  owner: orchestrator-rerun
  commands:
    - "python -m pytest tests/test_posts.py -p no:cacheprovider"
    - "python vulcan.py run-check docs/runs/RUN-021_pgm-005-게시글-작성-구현_v0.1.md"
  test_cases_stub:
    - id: UT-007
      file: tests/test_posts.py
      test_name: test_create_post_success
      description: "정상 제목/본문 입력 시 게시글 생성과 응답 DTO를 검증한다."
      required_assertions:
        - "응답에 id, title, body, created_at이 있다."
        - "저장소에 동일 게시글이 존재한다."
    - id: UT-008
      file: tests/test_posts.py
      test_name: test_create_post_validation_error
      description: "빈 제목 또는 길이 초과 입력 시 VALIDATION_FAILED를 반환한다."
      required_assertions:
        - "오류 코드가 VALIDATION_FAILED다."
        - "HTTP 상태 또는 예외 타입이 error_contract와 일치한다."

output_requirements:
  format: RUN_OUTPUT_CONTRACT.md
  include:
    - changed_files
    - related_ids
    - verification_results
    - standard_compliance_report
    - open_issues
    - orchestrator_decision_needed
```

## 6. 필드 작성 규칙

### 6.1 `goal`

`goal`은 한 문장으로 쓴다.

좋은 예:

```text
SCR-003 게시글 목록 화면을 구현하고 UI-003 캡처 증적을 생성한다.
```

나쁜 예:

```text
화면 좀 정리
```

### 6.2 `related_ids`와 `target_contracts`

`related_ids`는 전체 관련 맥락이다.
`target_contracts`는 이번 Run에서 worker가 실제로 닫아야 하는 구현/검수 경계다.

구현 Run은 `FUNC`, `PGM`, `API`, `DB`, `SEC`, `UT/IT/UI` 중 가능한 항목을 좁게 묶는다.
worker는 이 묶음 밖의 기능을 확장하지 않는다.

`target_contracts.interface_contract`는 worker가 작성할 코드의 뼈대다.
Orchestrator는 구현 Run을 만들 때 임의의 네이밍, 타입, schema, 오류 응답 편차를 막을 수 있도록 이 블록을 작성해야 한다.
worker는 이 블록에 명시된 public signature, schema, error contract를 따라야 하며, 다른 이름이나 다른 타입으로 대체하지 않는다.
`skill: build-wave` 또는 `run_type: Implementation`인데 `interface_contract`가 없으면 Orchestrator는 생략 사유를 Run에 명시해야 한다.
`skill: implementation-scaffold` 또는 `run_type: ImplementationScaffold`이면 `contract_skeleton`은 필수다.

| 대상 | 작성 내용 |
| --- | --- |
| API endpoint | OpenAPI Spec JSON/YAML의 method/path, request/response DTO, status/error mapping을 삽입한다. |
| Backend method/class | 선택 언어의 type hint, interface, abstract class, public function/method signature, docstring, DTO/schema, error contract, transaction boundary를 명시한다. |
| Frontend component/hook/client | Props interface, state type, event handler signature, API client signature, rollback/refetch rule을 명시한다. |
| DB/repository | entity/table, query method signature, constraint, transaction owner를 명시한다. |

private helper의 내부 알고리즘까지 고정하지 않는다.
공개 계약과 외부에서 관찰되는 동작을 고정한다.

`target_contracts.contract_skeleton`은 구현 전 뼈대 생성 또는 기존 코드 정렬 범위다.

| 모드 | 사용 시점 | 완료 기준 |
| --- | --- | --- |
| `new` | 신규 개발 Impl 첫 Wave | 프로젝트 골격, public signature, DTO/schema, smoke build가 존재한다. |
| `existing-alignment` | 고도화/레거시 프로젝트 | 기존 코드와 Program Design의 PGM/IF/MTH 매핑, 누락 skeleton 보강, 충돌 ISSUE/CR 반환 |
| `not-required` | 이미 빌드 가능한 골격과 public signature가 존재 | 생략 사유와 확인 근거를 남긴다. |

### 6.3 `development_standards_applied`

`development_standards_applied`는 worker가 개발표준 전체를 매번 정독하지 않아도 이번 Run에 해당되는 표준을 바로 확인하게 하는 바인딩이다.
Orchestrator는 개발표준정의서의 규칙 ID를 직접 매핑해야 한다.
worker는 이 목록을 준수 체크리스트로 사용하고, 결과 보고에 `standard_compliance_report`를 남긴다.

예:

```yaml
development_standards_applied:
  - standard_id: DEV-LOG-001
    source: docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    rule: "표준 logger를 사용하고 민감정보를 로그에 남기지 않는다."
```

로깅 작업이면 `DEV-LOG-001`, REST API 오류 응답 작업이면 `DEV-API-001` 또는 `DEV-ERR-001`처럼 이번 Run의 직접 구현 판단에 필요한 규칙만 넣는다.
개발표준 문서에 아직 규칙 ID가 없으면 Orchestrator는 Gate 2에서 규칙 ID를 먼저 보강하거나, Run 안에 임시 `standard_id`와 출처를 명시한다.

### 6.4 `development_standard_checklist`

`development_standard_checklist`는 구현 worker가 코드를 작성하면서 바로 체크해야 하는 로깅, 주석, 테스트 설명 기준이다.
개발표준정의서에 기준이 있더라도 Build Wave Run에 이 체크리스트가 없으면 worker가 구현 중 놓칠 수 있으므로, Orchestrator는 구현 Run 생성 시 직접 포함해야 한다.

최소 필드는 다음과 같다.

```yaml
development_standard_checklist:
  logging:
    required: true
    targets: [Controller, Service, SecurityFilter, ControllerAdvice, CoreComponent]
    rule: "프로젝트 표준 logger를 선언하고 민감정보, 토큰, 비밀번호, 내부 stack trace를 로그에 남기지 않는다."
  comments:
    required: true
    targets: ["주요 class", "public 업무 method", "보안/트랜잭션/권한 판단 method"]
    rule: "책임, 입력, 출력, 예외, 관련 REQ/FUNC/PGM/SEC/UT/IT ID를 JavaDoc/docstring/주석으로 남긴다."
  tests:
    required: true
    targets: ["@Test", "단위 테스트", "통합 테스트", "UI/E2E 테스트"]
    rule: "테스트 이름의 추적 ID만으로 끝내지 않고 @DisplayName 또는 Given/When/Then으로 입력값, 기대값, 출력값을 설명한다."
```

worker는 Run 결과에 준수 여부와 예외 사유를 남긴다.
기준이 기술스택과 맞지 않으면 임의로 생략하지 않고 `open_issues`, `FIND`, 또는 Orchestrator 결정 필요 항목으로 반환한다.

### 6.5 `direct_edit_scope`

`direct_edit_scope`는 Orchestrator가 구현 단계에서 예외적으로 직접 수정할 때만 사용한다.
기본 구현 경로는 Build Wave worker이며, Orchestrator 직접 구현은 작은 연결 수정, 충돌 해소, 오타/경로/설정 보정 같은 예외로 제한한다.

직접 수정 예외는 다음 조건을 모두 만족해야 한다.

- 수정 파일 2개 이하
- 순 변경량 약 30 LOC 이하
- public API, PGM/IF/MTH, DTO/schema, DB migration, security boundary, SCR/UI contract 변경 없음
- 기존 테스트 또는 작은 테스트 보정으로 검증 가능

예:

```yaml
orchestrator_direct_edit_reason: "worker 결과 통합 중 import 경로 충돌을 해소하기 위한 1파일 연결 수정"
direct_edit_scope:
  files:
    - backend/src/main/java/com/example/todo/auth/AuthConfig.java
  estimated_loc: 8
  contract_changed: false
  verification:
    - "./gradlew :backend:test --tests '*AuthConfig*'"
  followup_review_required: true
```

위 조건을 넘으면 `direct_edit_scope`로 처리하지 않고 Build Wave Run 또는 worker Run으로 분리한다.

### 6.6 `source_documents`

`source_documents.read_first`는 worker가 작업 시작 전에 반드시 먼저 읽는 최소 문서다.
보통 `AGENTS.md`, `session.json`, 현재 skill 문서만 둔다.

`source_documents.working_documents`는 이번 Run에서 실제로 작성하거나 검토할 산출물이다.
worker는 이 문서에 가장 많은 주의를 둔다.
일반적으로 `scope.writable`의 산출물 문서와 일치해야 하며, 요구사항/설계/테스트 기준처럼 입력으로만 쓰는 문서는 여기 넣지 않는다.

`source_documents.reference_on_demand`는 항상 정독하는 문서가 아니다.
기준 충돌, 작성 규칙 확인, 보안/데이터/개발표준 판단처럼 필요할 때만 펼쳐본다.

`orchestrator_reference`는 worker가 구현 판단을 위해 읽는 입력 계약이 아니다.
Orchestrator가 worker 결과를 받은 뒤 추적표 반영, Run 입출력 정규화, session/Wave 상태 갱신, Gate 판단을 수행할 때 사용하는 운영 문서다.
worker Run에는 `Traceability Matrix`, `AGENT_RUN_PROTOCOL`, `RUN_INPUT_CONTRACT`, `RUN_OUTPUT_CONTRACT`를 `source_documents`에 반복해서 넣지 않는다.

`source_documents`에 없는 전역 memory, 과거 rollout summary, 다른 샘플 프로젝트 문서는 현재 Run의 입력 계약이 아니다.
런타임이 memory를 자동으로 제공하더라도 worker는 현재 Run의 `source_documents`, `target_contracts`, `scope`, 최신 사용자 지시만 작업 근거로 삼는다.

### 6.7 `verification`

`verification.commands`에는 Orchestrator가 worker 결과를 받은 뒤 재실행할 담당 테스트케이스 명령, 빌드/린트, `python vulcan.py run-check <현재 Run>`처럼 작업자 범위에서 재현 가능한 명령만 넣는다.

worker는 가능하면 같은 명령을 self-check로 실행하고 결과를 보고한다.
다만 권위 있는 테스트 결과와 테스트 결과서 반영은 Orchestrator가 재실행한 결과를 기준으로 한다.

`verification.test_cases_stub`는 worker가 구현하거나 통과시킬 테스트의 최소 골격이다.
Orchestrator는 "테스트를 작성한다"처럼 포괄적으로 쓰지 않고, `file`, `test_name`, `description`, `required_assertions`를 명시해야 한다.
worker는 테스트 스터브를 기반으로 테스트 코드를 작성하거나 기존 테스트를 갱신해야 한다.
테스트 이름만 쓰지 말고 검증 의도와 필수 assertion을 함께 쓴다.

## 7. Worker 실행 경계

작업자 runner는 Run 계약 수행자가 될 수 있지만 Orchestrator가 아니다.

worker는 다음을 직접 수행하지 않는다.

```text
Gate 전환
session.json current_gate/gate_status/completed 변경
wave-start/wave-complete
sync-session
status --check 또는 prepare-transition을 통한 Gate 전환 가능 판단
check-trace를 통한 추적성 상세 진단
전체 추적표 통합 확정
테스트 결과서 최종 확정
QA Pass 최종 선언
릴리즈 승인
merge 가능 여부 최종 판단
```

worker가 위 항목이 필요하다고 판단하면 직접 실행하지 않고 완료 보고의 `orchestrator_decision_needed`에 반환한다.
PoC worker는 `run-preflight`/`run-check` 경고가 비차단이면 이를 실패로 간주하지 않는다. 담당 구현과 self-check를 완료한 뒤 경고, 재현 명령, 후속 판단 필요 여부를 결과에 남기고 종료한다.
PoC 구현 worker는 README, 최종 테스트 결과서, browser smoke/screenshot, release/backlog, 증적 로그 정규화를 기본 완료 범위로 삼지 않는다. 이 작업들은 Gate 4/5 또는 Evidence/Normalization worker가 담당한다.

worker Run에는 Orchestrator가 Run을 나눌 때 쓰는 `worker_run_sizing_policy` 전체 블록을 반복하지 않는다.
대신 `worker_execution_policy.completion_rules`에 worker가 직접 지킬 완료 기준만 짧게 둔다.

```yaml
worker_execution_policy:
  completion_rules:
    - "이 Run의 target_contracts만 완결한다."
    - "빌드 또는 담당 테스트가 깨진 상태를 완료로 보고하지 않는다."
    - "범위가 너무 크면 중간 구현하지 말고 Orchestrator 결정 필요 항목으로 반환한다."
    - "PoC에서 비차단 경고만 남으면 경고 제거 루프를 반복하지 않고 내용과 후속 판단자를 기록한 뒤 반환한다."
    - "PoC 구현 Run이면 browser smoke/screenshot, 최종 테스트 결과서, README/release/backlog 정리는 Orchestrator 결정 필요 항목으로 반환한다."
```

`scope.writable` 밖의 파일 수정은 원칙적으로 금지한다.

## 8. Worker Run 분할 기준

이 섹션은 worker에게 전달하는 입력 payload가 아니라 Orchestrator가 Run을 작성할 때 사용하는 분할 기준이다.
worker는 이미 분할된 Run을 수행하며, 범위가 과도하다고 판단하면 작업을 임의로 반쪽 완료하지 않고 `orchestrator_decision_needed`로 반환한다.

Run 하나는 끝났을 때 빌드/테스트/리뷰 가능한 완결 조각이어야 한다.

| 기준 | 규칙 |
| --- | --- |
| 1차 기준 | 기능/계약 단위로 나눈다. |
| 완결성 | Run 하나가 끝나면 담당 테스트와 리뷰가 가능해야 한다. |
| 머지 가능성 | 해당 Run만 반영해도 코드베이스가 깨지지 않아야 한다. |
| 시간 기준 | 목표 10분 내외, 최대 15분 권장. 시간은 Orchestrator의 분할 보조 기준이다. |
| 분리 기준 | 15분을 넘길 것 같으면 개발 중단이 아니라 더 작은 기능/계약 단위로 다시 나눈다. |
| 금지 | 컴파일/테스트가 깨지는 반쪽 구현, 시간 종료에 따른 미완성 종료, unrelated 리팩터링 |

## 9. UI 작업 보조 계약

UI 검증이 포함된 Run은 화면 단위가 아니라 상태/시나리오 단위로 테스트와 증적을 분리한다.
각 UI 테스트는 기대 화면과 실제 캡처 파일이 1:1로 연결되어야 한다.

```yaml
ui_evidence_policy:
  test_by_state: true
  official_runner: "@playwright/test"
  official_runner_command: "npx playwright test"
  official_runner_required_profiles: [audit, product]
  poc_fallback_allowed: true
  fallback_rule: "PoC에서는 커스텀 Playwright script를 smoke/demo 증적으로 허용할 수 있지만, audit/product의 공식 UI Pass는 @playwright/test 실행 결과를 기준으로 한다."
  required_artifacts:
    - "playwright-report/index.html 또는 동등한 HTML report"
    - "test-results/ trace, screenshot, video 중 프로젝트가 선택한 증적"
    - "docs/artifacts/04-review/evidence/ui/ 상태별 screenshot"
  required_evidence:
    - ui_id: UI-001-01
      state: "기본 화면"
      expected_visual_elements:
        - "가입 버튼"
        - "이메일 입력"
        - "비밀번호 입력"
      evidence_file: docs/artifacts/04-review/evidence/ui/UI-001-01.png
```

`ui_implementation_contract_policy`는 화면 퍼블리싱 산출물 또는 외부 시안이 있는 화면 작업에서 사용한다.
Gate 2에서는 시안을 참고자료로 둘지 구현 계약으로 둘지 분류하고, 구현 계약이면 필수 유지, 변경 허용, 변경 금지, 비교 방식을 작성한다.
Gate 3에서는 이 계약을 UI 테스트 기대결과에 반영한다.
Impl에서는 구현 전 체크리스트로 확인하고, Gate 4에서는 기준 UIREF와 구현 screenshot의 차이를 `Pass`, `FIND`, `CR`로 판정한다.

## 9.1 Worker 의존성 설치와 UI 검증 경계

worker worktree의 Node/Playwright 실행은 보조 self-check다.
`npm install`, `npm ci`, `npm run build`, `npm run dev`, `npx playwright install`, `npx playwright test`가 worker 환경에서 실패해도 그 사실만으로 구현 실패를 확정하지 않는다.

worker는 다음 원칙을 따른다.

- Node/Playwright 명령이 필요하면 `npm_config_cache`와 `PLAYWRIGHT_BROWSERS_PATH`를 사용한다.
- 권한, 인증, 네트워크, registry, cache 문제로 설치 또는 실행이 막히면 `environment_blocked` 또는 `not_run`으로 기록한다.
- 실패한 명령, cwd, exit code, log path, Orchestrator 재실행 명령을 남긴다.
- 화면 서버 실행과 Playwright 최종 증적은 `workflow.integration_branch` 기준의 `QA-000` QA workspace에서 Gate 4 QA 입력으로 판정한다. 별도 QA worktree는 프로젝트 정책에서 명시적으로 활성화한 경우에만 사용한다.

## 9.2 Gate 4 QA 실행 worker 경계

`skill: qa-execution` 또는 `persona: evidence`인 Gate 4 worker는 테스트 실행자와 증적 수집자다.
이 worker는 결함 수정자가 아니다.

QA 실행 worker는 다음을 수행할 수 있다.

- Gate 3 테스트케이스와 개발표준정의서의 필수 검증 명령 확인
- backend/frontend test, lint, build, `check-contract`, Playwright 실행
- 로그, screenshot, trace, JSON report, 테스트 결과서 초안 작성
- 후보 `FIND`, `CR`, `ISSUE`, `environment_blocked`, `Not Run` 기록

Gate 4 QA 실행은 다음 QA Run 순서로 쪼갠다.

| QA Run | 목적 | Worker 입력 계약에 포함할 것 |
| --- | --- | --- |
| `QA-000` | 환경 준비/스모크 | `doctor --json` 환경 증적, 통합 소스 존재 확인, 의존성 설치 가능성, DB/포트/환경변수, backend/frontend 기동 가능성, Playwright 설치/브라우저 캐시, 차단 시 후속 QA 중단 조건 |
| `QA-001` | 명령 기반 검증 | Gate 3/개발표준의 필수 명령, `check-contract`, `check-trace`, `run-check`, 로그 파일 경로, exit code 기록 기준 |
| `QA-002` | UI/E2E 증적 | UI-ID 목록, viewport, 서버 기동 절차, `@playwright/test` 공식 runner 명령, HTML report/trace/screenshot/log 경로, 상태/시나리오별 1:1 증적 기준 |
| `QA-003` | 결과 정리/판정 후보 | QA Finding/Test Result 갱신 범위, 추적표 반영 후보, FIND/CR/ISSUE 후보, Orchestrator 결정 필요 항목 |

QA-003의 실행 상태 원본은 `DOC-QA-G4-002_Test-Result_v0.1.md`다.
Gate 3 테스트케이스 문서는 계획/기준 문서이므로 QA-003에서 `Planned` 값을 `Pass`로 덮어쓰지 않는다.
Gate 4 `check-trace`는 QA 테스트 결과서의 `결과` 컬럼을 우선 읽고, 결과서에 실제 실행 상태가 없을 때만 Gate 3 테스트케이스를 fallback으로 참조한다.

`QA-000`은 Gate 4 전체에서 재사용할 QA workspace를 준비하는 Run이다. 기본값은 `workflow.integration_branch`의 현재 작업공간이다.
별도 QA worktree는 프로젝트 정책에서 명시적으로 활성화한 경우에만 사용한다.
`QA-000` Run 결과에는 `qa_workspace_path`, 기준 브랜치/커밋, 의존성 설치 상태, 서버/포트/DB 준비 상태를 남긴다.
`QA-000`은 기본적으로 `python vulcan.py doctor --json` 결과를 `docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.json`에 저장하고, 필요하면 사람이 읽을 로그를 `QA-000-doctor.log`로 함께 남긴다.
`doctor`의 `fail`/`warn`은 제품 결함으로 바로 확정하지 않고 `environment_blocked` 또는 ISSUE 후보로 분리한다.
`QA-001`, `QA-002`, `QA-003` Run 입력 계약에는 `QA-000`이 기록한 같은 `qa_workspace_path`를 포함해야 한다.
후속 QA Run은 새 workspace를 임의로 만들지 않고 같은 workspace에서 실행한다.

`QA-000` Run 입력 계약에는 다음 체크리스트를 포함한다.

| 확인 항목 | 작성 기준 |
| --- | --- |
| Doctor JSON | `python vulcan.py doctor --json` 출력, `summary.fail`/`summary.warn`, checks 목록, JSON 증적 경로를 기록한다. |
| Backend 빌드 도구 | Gradle wrapper 또는 프로젝트 지정 빌드 도구가 로컬 캐시/권한 기준으로 실행 가능한지 기록한다. |
| Backend smoke | backend 최소 smoke test, test discovery, 컴파일 확인 중 하나 이상을 실행하거나 미실행 사유를 기록한다. |
| Frontend 의존성 | `node_modules` 존재 여부 또는 `npm ci`/`npm install` 실행 가능 여부를 기록한다. |
| Playwright | `@playwright/test`와 browser cache 존재 여부 또는 `npx playwright install` 가능 여부를 기록한다. |
| 포트 | backend/frontend 개발 포트(예: 8080, 5173 또는 프로젝트 지정 포트)의 사용 가능 여부를 기록한다. |
| DB | SQLite 또는 프로젝트 지정 DB 파일 생성/접근 가능 여부를 기록한다. |
| 환경변수/출력 경로 | test profile, 필수 환경변수, 임시 디렉터리, 로그/증적 출력 디렉터리를 기록한다. |

하나의 `qa-execution` Run이 Gate 4 전체를 모두 수행한다고 쓰지 않는다.
`QA-000`이 통과하지 않으면 `QA-001`/`QA-002`를 실행하지 않고 `environment_blocked` 또는 `Not Run`으로 반환한다.
후속 QA가 차단되면 QA-000의 doctor JSON과 evidence 로그를 근거로 제품 결함과 환경 차단을 분리하고, 환경 문제는 `ISSUE`/`environment_blocked`로 보류하며, 수정이 필요할 때만 승인된 `qa-fix-loop`로 넘긴다.

Audit/Product Profile에서 공식 UI Pass는 `@playwright/test` 러너 실행 결과를 기준으로 한다.
권장 기준은 `playwright.config.ts` 또는 동등 설정, `tests/e2e/**/*.spec.*`, `npx playwright test`, `playwright-report/`, `test-results/`, 상태별 screenshot을 연결하는 것이다.
`playwright` 라이브러리를 직접 호출하는 커스텀 Node 스크립트는 PoC smoke/demo 또는 보조 관찰로 남길 수 있지만, audit/product의 Gate 4 UI Pass 근거로 단독 사용하지 않는다.

QA 실행 worker는 다음을 수행하지 않는다.

- 소스코드 수정
- 새 API, 새 메소드, 새 화면 상태 생성
- `qa-fix-loop`까지 이어서 수행
- QA Pass, Gate 완료, 릴리즈 가능 여부 확정

실패가 나오면 worker는 즉시 수정하지 않고 `failure_reports`에 원인 가설, 재현 명령, 로그 경로, 영향 ID를 남긴다.
Orchestrator는 사용자와 처리 방향을 정한 뒤 승인된 설계 범위 안의 결함만 별도 `qa-fix-loop` Run으로 보낸다.
요구사항/API/DB/보안/화면 계약 변경이 필요하면 `CR` 후보로 분류한다.

## 9.3 Gate 4 QA 수정 worker 경계

`skill: qa-fix-loop`인 Run은 QA 실행 중 발견된 `FIND`를 승인된 설계 범위 안에서 수정하는 worker Run이다.
QA 실행과 결함 수정은 같은 Run에서 이어서 수행하지 않는다.

`qa-fix-loop` Run 작성 기준:

- 파일명에는 `qa-fix-loop`와 대상 `FIND-ID`를 포함한다.
- `run_type`은 `QAFix`를 사용한다.
- `related_ids`에는 대상 `FIND-ID`와 수정할 `REQ/AC/PGM/API/IF/DB/SEC/UT/IT/UI`를 넣는다.
- `target_contracts`에는 수정할 설계 계약과 테스트 계약을 좁게 넣는다.
- `scope.writable`은 수정 대상 코드/테스트/자기 Run/필요한 증적 로그로 제한한다.
- `session.json`, Gate 전환, 추적표 최종 상태 확정은 worker writable scope에 넣지 않는다.
- worker는 수정 후 지정된 self-check를 실행하거나 `Not Run` 사유를 남긴다.
- Orchestrator는 worker 결과를 받은 뒤 `check-contract`, 관련 테스트, `run-check`를 재실행하고 FIND 닫힘 또는 CR 승격 후보를 판단한다.

예:

```yaml
run_id: RUN-018
gate: gate4
persona: build
skill: qa-fix-loop
run_type: QAFix
related_ids: [FIND-017-01, IF-003, PGM-003, UT-001, IT-001]
target_contracts:
  if: [IF-003]
  pgm: [PGM-003]
  test: [UT-001, IT-001]
```

QA 실행 worker의 Run 입력 계약에는 실패 보고 기준을 포함한다.

```yaml
qa_failure_report_contract:
  required_when: [Fail, Not Run, environment_blocked]
  required_fields:
    - qa_stage
    - failing_command
    - cwd
    - exit_code
    - observed_error
    - log_path
    - reproduction_command
    - impact_ids
    - candidate_classification
    - orchestrator_decision_needed
  candidate_classification_values: [FIND, CR, ISSUE, environment_blocked]
  forbidden_actions:
    - source_code_edit
    - new_api_or_method_creation
    - qa_fix_loop_execution
    - gate_pass_decision
```

## 10. Worker 전달 프롬프트 기본형

Adapter는 YAML 입력 뒤에 다음 실행 지침을 붙일 수 있다.
호출 방식과 세션/로그 처리는 adapter가 담당하지만, 지침 내용은 runner 공통이다.

```text
너는 Vulcan-Anvil Ex worker runner다.
Runner 종류가 Codex, Claude, Gemini 중 무엇이든 아래 Run 입력 계약을 기준으로만 작업한다.

작업 순서:
1. source_documents.read_first를 먼저 읽고 관련 ID와 현재 Gate를 확인한다.
2. target_contracts의 FUNC/PGM/API/DB/SEC/TEST 묶음을 실제 작업 경계로 삼는다.
3. target_contracts.interface_contract가 있으면 public signature, schema, error contract를 우선 지킨다.
4. source_documents.working_documents를 중심으로 실제 산출물을 작성하거나 검토한다.
5. source_documents.reference_on_demand는 target_contracts 확인, 기준 충돌, 상세 설계 판단이 필요할 때만 참고한다.
6. 전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기억은 현재 Run의 근거로 사용하지 않는다.
7. scope.writable 안에서만 수정한다.
8. completion_criteria를 모두 만족하도록 구현/문서/테스트를 갱신한다.
9. verification.test_cases_stub가 있으면 지정된 테스트 파일, 테스트 이름, 필수 assertion을 반영한다.
10. 가능한 경우 verification.commands를 self-check로 실행하고 결과를 보고한다.
11. Node/Playwright self-check가 worker 환경 문제로 막히면 environment_blocked 또는 not_run으로 기록하고 Orchestrator 재실행 명령을 남긴다.
12. UI 검증이 있으면 상태/시나리오별 UI-ID와 캡처 증적을 1:1로 연결한다. 단, worker worktree의 Playwright는 보조 검증이며 최종 UI 증적은 Gate 4 통합본 기준이다.
13. Gate 4 QA 실행 worker라면 실패를 발견해도 소스코드를 수정하지 않고 원인 가설, 재현 명령, 로그 경로, 영향 ID, 후보 FIND/CR/ISSUE를 남긴다.
14. 범위가 너무 커서 완결 구현이 어렵다면 중간 구현을 완료 처리하지 않고 Orchestrator 결정 필요 항목으로 반환한다.
15. Gate 전환, session 변경, 최종 승인 판단을 하지 않고 Orchestrator 결정 필요 항목으로 반환한다.
16. RUN_OUTPUT_CONTRACT 형식으로 결과를 보고한다.

금지:
- docs/ref-docs/를 읽거나 커밋하지 않는다.
- memory-derived assumption을 현재 프로젝트 사실처럼 확정하지 않는다.
- 과거 sample 프로젝트의 기능, 스택, 파일명, Run ID를 현재 Run에 임의 적용하지 않는다.
- 관련 없는 리팩터링을 하지 않는다.
- 테스트를 실행하지 못했으면 통과로 보고하지 않는다.
- worker self-check 결과를 최종 테스트 결과로 확정하지 않는다.
- QA 실행 worker가 결함 수정까지 이어서 수행하지 않는다.
- 추적표/결과서/session/Gate 갱신이 필요하면 Orchestrator 결정 필요 항목으로 반환한다.
- 시간이 끝났다는 이유로 빌드/테스트가 깨진 중간 구현을 완료 처리하지 않는다.
- 기대 화면과 다른 캡처를 UI 증적으로 Pass 처리하지 않는다.
```

## 11. Worker 출력 요구

worker는 `RUN_OUTPUT_CONTRACT.md`를 따른다.
구현 Run은 가능한 한 다음 항목을 포함한다.

```markdown
### 개발 표준 준수 보고

| 표준 ID | 준수 여부 | 구현 및 준수 방식 | 미준수 사유 및 대체 방식 |
| --- | --- | --- | --- |
| DEV-DIR-001 | Pass | 지정된 패키지 구조에 파일을 배치했다. | - |
| DEV-ERR-001 | Pass | 공통 오류 응답 포맷을 사용했다. | - |
```

`standard_compliance_report`는 worker가 자기 구현의 준수 여부를 보고하는 참고 자료다.
최종 승인과 Gate 통과 판단은 Orchestrator 재검증 결과를 기준으로 한다.

## 12. Orchestrator 작성/검증 규칙

Run 시작 전 Orchestrator 또는 `vulcan.py`는 다음을 확인한다.

| 체크 | 기준 |
| --- | --- |
| 관련 ID 존재 | 추적표 또는 산출물에 관련 ID가 존재한다 |
| target 계약 명확 | `target_contracts`가 이번 Run의 실제 경계를 좁게 정의한다 |
| interface 계약 명확 | 구현 Run이면 필요한 public signature/schema/error contract가 있다 |
| 테스트 stub 명확 | 구현 Run이면 테스트 파일, 테스트 이름, 검증 의도, 필수 assertion이 있다 |
| 개발표준 연결 | 이번 Run에 적용할 개발표준 규칙이 식별되어 있다 |
| 먼저 읽을 문서 존재 | `source_documents.read_first` 파일이 존재한다 |
| 작업 대상 명확 | `source_documents.working_documents`가 이번 Run 산출물 중심으로 작성되어 있다 |
| 참고문서 분리 | Core/Template/Sample/상류 산출물이 `reference_on_demand`로 분리되어 있다 |
| 운영문서 분리 | 추적표와 Run 입출력/절차 문서는 worker 입력이 아니라 `orchestrator_reference`에 있다 |
| 수정 범위 명확 | `scope.writable`이 비어 있지 않다 |
| 작업자 범위 제한 | worker Run에는 `session.json`, Gate 전환, 전체 추적표 통합, `sync-session`/`status --check`/`prepare-transition`/`check-trace`가 포함되지 않는다 |
| 제외 경로 포함 | `docs/ref-docs/`가 제외되어 있다 |
| 완료 조건 명확 | 테스트 또는 증적 기준이 하나 이상 있다 |
| 출력 형식 지정 | `RUN_OUTPUT_CONTRACT.md`를 참조한다 |

초기 대화에서 사람이 최소 입력만 줄 수 있다.

```yaml
goal: "게시글 작성 기능 구현"
related_ids: [REQ-005]
```

이 경우 Orchestrator 또는 도구는 추적표와 산출물을 읽어 완전 입력으로 확장한다.
완전 입력을 만들 수 없으면 `Blocked` 상태로 질문한다.

## 12.1 Branch/Worktree 기준

기본 audit workflow에서 worker Run은 브랜치 경계를 전제로 작성한다.

- Phase 0~Gate 3 산출물 Run은 `main` 기준으로 작성한다.
- `impl`의 `implementation-plan`, `implementation-scaffold`, `build-wave` Run은 `workflow.integration_branch` 통합 브랜치 기준으로 작성한다. 기본값은 `dev`지만 프로젝트 설정에 따라 다른 브랜치명을 사용할 수 있다.
- Gate 4의 `qa-execution` Run은 기본적으로 `workflow.integration_branch`의 현재 작업공간을 `QA-000` QA workspace로 기록하고, `QA-001`~`QA-003`이 이를 재사용하는 것으로 작성한다. QA worktree는 명시적으로 활성화한 프로젝트에서만 사용한다.
- Run 입력 계약에는 브랜치 전환 명령을 worker 작업으로 넣지 않는다. Orchestrator가 `python vulcan.py branch-start impl`과 `python vulcan.py branch-status`로 준비한다.
- worker는 feature 브랜치/worktree에서 작업할 수 있지만, 최종 통합 판단과 `main` 반영 판단은 Orchestrator와 Gate 5 승인 절차가 담당한다.

## 13. 통합 규칙

worker worktree 결과는 손으로 복사하지 않는다.

Orchestrator는 다음 흐름을 사용한다.

```text
1. run-integrate --dry-run으로 변경 파일과 scope 위반 확인
2. 위반이 없으면 run-integrate --apply로 허용 diff 반영
3. verification.commands 재실행
4. 결과에 따라 Run, 테스트결과서, 추적표, session을 Orchestrator 책임으로 갱신
```

`run-integrate`가 실패하면 Orchestrator가 임의로 직접 고치지 않고 재작업 Run, QA Fix Run, Traceability Run, FIND/CR/ISSUE 중 하나로 분기한다.
