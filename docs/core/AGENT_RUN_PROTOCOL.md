# Agent Run Protocol

> 상태: 초안 v0.1
> 목적: Vulcan-Anvil Ex에서 Codex, GPT, Claude 등 서로 다른 에이전트가 동일한 산출물과 Gate 규칙을 기준으로 작업하도록 공통 실행 규약을 정의한다.

## 1. 기본 원칙

Agent Run Protocol은 특정 모델이나 제품의 사용법이 아니다.

이 문서는 에이전트가 프로젝트 산출물을 읽고, 작업을 수행하고, 결과와 증적을 남기는 공통 계약을 정의한다. Adapter는 이 계약을 각 도구의 명령, 프롬프트, API, 세션 방식에 맞게 변환한다.

Core 원칙:

- 에이전트는 항상 승인된 문서와 추적표를 먼저 읽고 작업한다.
- 런타임 전역 메모리, 과거 세션 요약, 다른 샘플 프로젝트 기억은 현재 프로젝트의 source of truth가 아니다.
- 메모리가 자동으로 제공되더라도 요구사항, Gate 상태, Run 범위, 승인 여부, 구현 대상, 테스트 통과 여부는 현재 저장소의 `session.json`, Gate 산출물, Run 문서, 사용자 최신 지시로 다시 확인한다.
- 에이전트의 모든 작업은 `REQ`, `AC`, `FUNC`, `SCR`, `PGM`, `DB`, `SEC`, `UT`, `IT`, `PT`, `UI` 중 하나 이상과 연결되어야 한다.
- 에이전트가 임의로 범위를 확장하지 않도록 Run Scope를 명시한다.
- Gate 완료 전에는 산출물, 구현, 테스트, 증적, 미해결 이슈를 함께 남긴다.
- Gate 산출물 완료 후에는 다음 Gate로 진행하지 말고 사용자 승인 질문을 남긴 뒤 대기한다.
- 대화상 명시 승인이 없으면 Run, 릴리즈 승인서, Gate 결과에 사용자 승인으로 기록하지 않는다.
- 모델별 차이는 Adapter에서 흡수하고 Core 산출물 형식은 유지한다.

## 2. Run 단위

하나의 Run은 에이전트에게 위임 가능한 최소 작업 단위다.

Run은 다음 중 하나의 목적을 가진다.

| Run 유형 | 목적 | 대표 산출물 |
| --- | --- | --- |
| Discovery Run | 요구사항, 참조문서, 현행 코드 분석 | 분석 메모, 질문 목록, `DEC`, `RISK` |
| Design Run | 요구사항을 설계 산출물로 전개 | SW 아키텍처 정의서, 기능명세, 화면명세, 프로그램 설계, DB명세 |
| Screen Design Run | 화면 구조와 시안을 `SCR-ID`에 연결 | 화면설계서, 와이어프레임, 시안 이미지, 기준 viewport |
| Design Review Run | Gate 3 진입 전 설계 완성도를 검수 | 보안 검토, 화면 검토, 개발표준 검토 |
| Implementation Run | 승인된 설계를 코드로 구현 | 소스 코드, 설정, 리소스, 마이그레이션 |
| Test Run | 테스트 코드와 실행 결과 작성 | `UT`, `IT`, `PT`, 상태/시나리오별 `UI`, 결과서 |
| Evidence Run | 화면 캡처, 로그, 결과 파일 정리 | 증적 파일, 결과 문서 |
| Review Run | 추적성, 보안, 품질 점검 | 이슈, 변경요청, 리뷰 결과 |
| QA Fix Run | G4에서 발견된 기존 설계 범위 내 결함 수정 | `FIND`, 수정 코드, 재검증 결과 |
| Change Impact Run | 변경요청 영향도 분석과 다시 진행할 Gate 판단 | `CR`, 영향받는 ID, scope, 승인 판단 |

Run은 너무 크게 만들지 않는다.

좋은 Run 예시:

```text
REQ-005 게시글 작성 기능의 PGM-005 구현 및 UT-007/UT-008 통과
SCR-003 게시글 목록 화면 구현 및 UI-003 캡처 증적 생성
SCR-001 로그인 화면 시안을 외부 Figma 캡처와 연결하고 UI-001 비교 기준 작성
SEC-003 작성자 권한 검증 누락 여부 리뷰
FIND-001 비로그인 게시글 작성 실패 결함 수정 및 UT-008 재실행
CR-001 게시글 첨부파일 요청 영향도 분석
```

나쁜 Run 예시:

```text
게시판 전체 개발
문서 전부 정리
테스트 적당히 추가
```

## 3. Run 입력 계약

Adapter는 에이전트를 실행하기 전에 다음 입력을 구성해야 한다.

Gate 작업은 Run 문서 생성 뒤에 시작한다. `vulcan.py gate-start`는 Gate 상태를 갱신한 뒤 해당 Gate의 기본 `orchestrator-plan` Run 초안을 자동 생성한다. 이미 같은 Gate에 `Draft`, `InProgress`, `In Progress`, `Running` 상태의 Run이 있으면 중복 생성하지 않는다.

Gate 산출물이 완료되어도 사용자 승인 전에는 `done`으로 닫지 않는다. 산출물 요약과 다음 Gate 진행 질문을 남긴 뒤 `python vulcan.py session --gate <현재 Gate> --status awaiting-approval`로 현재 Gate에 머무른다. 사용자가 명시 승인한 뒤에만 `python vulcan.py session --gate <현재 Gate> --status done --approved --approval-evidence "<승인 근거>"`를 실행해 다음 Gate로 전환한다.

기본 audit workflow는 브랜치 경계를 둔다. `init`과 Phase 0~Gate 3 산출물은 `main`에서 진행한다. `impl`에 진입하면 `python vulcan.py branch-start impl`로 `vulcan.config.json.workflow.integration_branch`(기본 `dev`)를 만들거나 전환한다. Build Wave 구현, worker 실행, Gate 4 QA는 통합 브랜치에서 수행하고, Gate 5 승인 후 통합 브랜치를 `main`으로 반영한다. 현재 상태는 `python vulcan.py branch-status`로 확인한다.

이 기본 Run은 Gate 작업의 시작 계약이다. 에이전트는 이 Run을 읽고 필요한 세부 persona Run을 제안하거나 `run-new`로 추가 생성한 뒤 산출물 작성, 구현, 테스트, QA를 진행한다. Gate 종료 시에는 시작 시 만든 Run 또는 세부 Run을 완료 보고 형식으로 갱신한다.

| 입력 | 필수 여부 | 설명 |
| --- | --- | --- |
| Run ID | 필수 | 에이전트 실행 단위 ID. 예: `RUN-001` |
| Persona | 필수 | 작업 persona. 예: `requirements`, `design`, `build`, `review`. 상세는 `AGENT_PERSONAS.md`를 따른다. |
| Run 유형 | 필수 | Discovery, Design, Implementation, Test, Evidence, Review |
| 목표 | 필수 | 이번 Run에서 완료할 구체적 목표 |
| 범위 | 필수 | 수정 가능 파일, 읽기 전용 파일, 제외 파일 |
| 기준 문서 | 필수 | 요구사항, 추적표, 관련 설계문서, 개발표준 |
| 관련 ID | 필수 | `REQ`, `AC`, `FUNC`, `SCR`, `PGM`, `DB`, `SEC`, 테스트 ID |
| Gate | 필수 | 현재 Gate와 완료 조건 |
| 금지사항 | 필수 | 민감문서, 임의 리팩터링, 승인 없는 범위 변경 등 |
| 완료 조건 | 필수 | 테스트, 캡처, 문서 갱신, 리뷰 기준 |
| 질문 정책 | 필수 | 막혔을 때 질문할 조건 |

입력 예시:

```yaml
run_id: RUN-001
persona: build
run_type: Implementation
goal: PGM-005 업무 기능 API 구현
gate: G2
scope:
  writable:
    - app/api/work_items.py
    - app/services/work_item_service.py
  readonly:
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/seed-docs/reference-standards/
  excluded:
    - docs/ref-docs/
related_ids:
  req: [REQ-005]
  ac: [AC-007, AC-008]
  func: [FUNC-005]
  pgm: [PGM-005]
  sec: [SEC-002, SEC-004]
completion:
  - 구현 파일 작성
  - UT-007, UT-008 통과
  - 추적표 증적 갱신
```

## 3.1 Memory 사용 금지 경계

Codex, Claude, Gemini 등 런타임은 전역 또는 프로젝트별 memory를 자동으로 제공할 수 있다.
Vulcan-Anvil Ex에서 memory는 편의 힌트일 뿐이며 현재 프로젝트의 공식 근거가 아니다.

에이전트는 다음을 memory만 근거로 판단하지 않는다.

- 현재 Gate와 Gate 완료 여부
- 사용자 승인 여부
- 요구사항, 비목표, 범위, 관련 ID
- 사용할 기술스택, 도메인 기능, 보안 정책
- 구현 대상 파일, public method, DTO/schema
- 테스트 실행 여부와 Pass/Fail

memory 내용이 현재 프로젝트 문서와 충돌하거나 오래된 샘플 프로젝트 맥락을 포함하면 적용하지 않는다.
필요하면 `memory-derived assumption`으로 표시한 뒤 현재 산출물에서 확인하거나 질문한다.

## 4. Run 출력 계약

에이전트는 작업 완료 시 다음 결과를 남겨야 한다.

| 출력 | 필수 여부 | 설명 |
| --- | --- | --- |
| 변경 요약 | 필수 | 무엇을 왜 바꿨는지 |
| 변경 파일 | 필수 | 파일 경로 목록 |
| 관련 ID | 필수 | 변경과 연결된 추적 ID |
| 검증 결과 | 필수 | 실행한 테스트/명령/캡처 결과 |
| 증적 | 해당 시 필수 | 테스트 결과서, 스크린샷, 로그, 커밋 |
| 위임 기록 | 위임 시 필수 | subagent/thread/외부 runner에게 맡긴 작업 범위와 결과 요약 |
| 미해결 이슈 | 필수 | 남은 질문, 위험, 후속 작업 |
| 다음 Run 제안 | 선택 | 이어서 진행할 수 있는 구체 작업 |

출력은 사람에게 설명 가능한 문장과 기계가 읽을 수 있는 구조를 함께 갖는 것이 좋다.

권장 출력 형식:

```yaml
run_id: RUN-001
status: Completed
changed_files:
  - app/api/work_items.py
related_ids:
  - REQ-005
  - AC-007
  - PGM-005
verification:
  - command: python -m pytest tests
    result: passed
evidence:
  - DOC-QA-G4-002_Test-Result_v0.1.md
delegation_records:
  - mode: codex-subagent
    delegate: build
    task: PGM-005 구현
    scope:
      writable:
        - app/api/work_items.py
    status: worker_completed
    changed_files:
      - app/api/work_items.py
    result_summary: "API 구현 완료"
    orchestrator_verification:
      - command: python -m pytest tests
        result: passed
open_issues: []
```

## 5. Gate별 실행 규칙

| Gate | 에이전트 역할 | 완료 조건 |
| --- | --- | --- |
| P0 | 배경, 제약, 참조문서 파악 | 질문/가정/위험이 기록됨 |
| G1 | 요구사항과 인수기준 정리 | `REQ`, `NREQ`, `AC`가 추적표에 반영됨 |
| G2 | SW 아키텍처, 기능, 화면, 프로그램, DB, 보안 설계 및 설계 검수 | `CNT`, `CMP`, `FLOW`, `ADR`, `FUNC`, `SCR`, `PGM`, `DB`, `SEC`, 개발표준 연결과 보안/화면/개발표준 검수 완료 |
| G3 | 테스트 계획 작성 | `UT`, `IT`, `PT`, `UI`가 `AC`/`SEC`와 연결됨 |
| G4 | 구현, 테스트, 증적 생성 | 테스트 결과와 화면/로그 증적이 추적표에 연결됨 |
| G5 | 승인, 릴리즈, 인수인계 | 승인본, 변경이력, 릴리즈 증적 정리 |

에이전트는 현재 Gate의 완료 조건을 만족하지 못하면 다음 Gate로 넘어갔다고 선언하지 않는다.

에이전트는 `session.json.current_gate`보다 앞선 Gate의 작업을 임의로 수행하지 않는다. Run 문서의 `gate:` 값은 실제 진행 상태를 바꾸지 않는다. 현재 상태와 다음 행동은 먼저 `python vulcan.py status`로 확인하고, Gate 전환 가능성은 기본적으로 `python vulcan.py status --check`로 진단한다. 실제 Gate 상태 갱신은 `vulcan.py gate-start`, `vulcan.py session`, `vulcan.py sync-session`으로 수행한다. `prepare-transition`은 상세/호환 진단이 필요할 때 직접 실행하고, `check-trace`는 추적성 오류를 상세 분석하거나 trace-only 회귀 검증이 필요할 때 직접 실행한다.
`vulcan.py gate-start`, `vulcan.py session`, `vulcan.py wave-start`, `vulcan.py wave-complete` 같은 상태 변경 명령은 대시보드용 stats 캐시를 함께 갱신해야 한다. `vulcan.py sync-session`은 수동 복구 또는 재계산이 필요할 때 사용하는 보조 명령이다.

현재 Gate별 금지 예시는 다음과 같다.

| 현재 Gate | 사용자 추가 승인 없이 금지되는 작업 |
| --- | --- |
| `phase0` | 확정 요구사항 작성, 설계 확정, 구현 파일/테스트 코드 생성 |
| `gate1` | 기능/화면/프로그램/DB 설계 확정, 구현 파일/테스트 코드 생성 |
| `gate2` | 테스트 결과서 작성, 구현 파일 생성, 완료된 QA 증적 선언 |
| `gate3` | 구현 파일 생성, 실제 테스트 결과를 완료 증적으로 확정 |
| `impl` | QA 승인, 릴리즈 승인 선언 |
| `gate4` | 미해결 FIND/CR/ISSUE를 숨기고 최종 승인 선언 |

사용자가 완성된 앱이나 기능을 요청해도, 현재 Gate가 앞 단계라면 에이전트는 먼저 현재 Gate 산출물과 다음 Gate 승인 질문을 만들고 멈춘다. 예외적으로 화면 퍼블리싱 산출물 또는 시범 구현이 필요한 경우에는 사용자에게 명시적으로 확인하고, 예외 범위와 후속 정리 항목을 Run의 `open_issues` 또는 `change_requests`에 기록한다.

Gate 1의 인수기준은 요구사항 충족 여부를 판단하는 검증 가능한 문장과 검증 방식까지만 작성한다. `Given/When/Then`, 선행조건, 예외조건, 검증 데이터, 테스트 절차, 자동화 파일명은 Gate 3 테스트케이스 문서에 작성한다.

## 5.1 Gate 종료 승인 규칙

각 Gate Run의 마지막 출력은 다음 순서를 따른다.

1. 이번 Gate에서 작성 또는 수정한 산출물과 관련 ID를 요약한다.
2. 미해결 `open_issues`, `FIND`, `CR`, `ISSUE`를 숨기지 않고 나열한다.
3. 다음 Gate에서 수행할 Run 후보를 제안한다.
4. "다음 Gate로 진행해도 되는지"를 명시적으로 질문한다.
5. 사용자가 승인하기 전까지 다음 Gate 산출물, 구현, QA Pass, 릴리즈 승인 작업을 시작하지 않는다.

승인으로 볼 수 있는 표현은 사용자가 다음 Gate 진행을 직접 허용한 경우다.
예: "Gate 2로 진행해", "승인", "다음 단계 진행해".
단순한 작업 지시나 "계속 확인해줘"를 전체 Gate 승인으로 넓게 해석하지 않는다.

## 5.2 UI 테스트와 증적 매칭 규칙

UI 테스트는 화면 하나를 크게 Pass 처리하지 않는다.
상태와 시나리오별로 `UI-001-01`처럼 나누고, 각 UI-ID에 기대 화면과 실제 증적 파일을 1:1로 연결한다.

예:

| UI-ID | 상태/시나리오 | 기대 증적 |
| --- | --- | --- |
| UI-001-01 | 회원가입 기본 화면 | 이메일/비밀번호/비밀번호 확인/가입 버튼 |
| UI-001-02 | 약한 비밀번호 오류 | 오류 메시지와 가입 차단 상태 |
| UI-001-03 | 비밀번호 확인 불일치 | 불일치 오류 메시지 |
| UI-001-04 | 중복 이메일 오류 | 중복 이메일 오류 메시지 |
| UI-001-05 | 회원가입 성공 | 가입 완료 메시지와 로그인 안내 |
| UI-001-06 | 성공 후 로그인 연계 | 로그인 화면 전환과 성공 메시지 또는 이메일 연계 |

기대 화면이 회원가입 성공 메시지인데 실제 증적이 단순 로그인 화면이면 Pass가 아니다.
이 경우 `Fail` 또는 `Not Run`으로 기록하고 `FIND`를 남긴다.

## 5.3 Implementation Plan과 Build Wave

구현 단계는 작업 규모에 따라 운영 강도를 조절한다. 구현 범위가 중간 이상이거나 subagent, 여러 커밋, 여러 모듈, UI 증적이 함께 필요한 경우에는 `implementation-plan` Run을 만들고 승인된 범위를 `Implementation Scaffold`와 여러 `Build Wave`로 나눈다. 작은 단일 구현은 Build Wave 분할을 생략할 수 있지만, Orchestrator 직접 구현을 의미하지 않는다. 실제 코드/테스트/UI/API 구현은 기본적으로 `build` persona의 native worker(subagent/thread/native branch agent)가 수행한다.

`agent-run --mode work`와 `run-exec`는 기본 구현 경로가 아니다. 별도 CLI 프로세스, cross-runner 검증, worktree/timeout/watchdog 증적이 필요할 때 선택하는 옵션이다.
worker 실패가 unsupported model, runner 미감지, npm/Playwright/cache, 포트, Dashboard 같은 로컬 실행 환경 문제로 보이면 재시도나 FIND 확정 전에 `python vulcan.py doctor`를 실행한다. `doctor`는 환경 차단 여부를 분류하기 위한 보조 진단이며, 구현 계약 위반 여부는 별도 테스트와 Orchestrator 재검증으로 판단한다.

신규 개발 또는 빌드 가능한 골격이 없는 프로젝트는 feature 구현 전에 `BW-000 Implementation Scaffold`를 먼저 수행한다. 고도화 프로젝트도 기존 코드가 Program Design의 `PGM/IF/MTH/DTO` 계약과 맞는지 확인하는 scaffold/alignment Run을 둘 수 있다. Implementation Plan은 scaffold 필요 여부를 반드시 기록하며, 생략할 때는 `contract_skeleton.mode: not-required`와 확인 근거를 남긴다.

| 개념 | 의미 | 산출물 |
| --- | --- | --- |
| Implementation Plan Run | 전체 구현을 Wave로 나누는 운영 Run | `BW-ID`, 의존성, 위임 계획, 테스트/커밋 계획 |
| Implementation Scaffold Run | feature 구현 전 빌드 가능한 계약 뼈대를 만드는 Run | 폴더/빌드 설정, class/interface/method/DTO skeleton, compile/build smoke |
| Build Wave Run | 하나의 검증 가능한 구현 배치이자 worker 작업지시서 | 코드, 테스트, 추적표 갱신 필요 항목, 검증 결과, 커밋 후보 |

`Build Wave`는 다음 기준을 만족해야 한다.

- 하나의 Wave는 관련 `REQ/AC/PGM/SCR/DB/SEC/UT/IT/UI`를 가진다.
- 하나의 Wave는 독립적으로 검증 가능한 테스트 또는 확인 기준을 가진다.
- 하나의 Wave가 끝나면 Run 기록에는 변경 파일, 테스트, 추적표 갱신 필요 항목이 남고, 요구사항추적표 상태 반영은 Orchestrator가 재검증 후 수행한다.
- 하나의 Wave는 기본적으로 하나의 커밋 후보가 된다.
- Wave 간 의존성이 있으면 Implementation Plan에 순서를 명시한다.
- 신규 개발의 첫 Wave는 보통 `BW-000` 또는 `SCF-001` scaffold로 두고, 이후 `BW-001`부터 feature 구현을 수행한다.
- 구현 중 active Wave는 하나만 둔다. 여러 Wave를 동시에 코드 수정 상태로 진행하지 않는다.
- 한 Wave를 여러 runner에게 나누어 동시에 구현시키지 않는다. backend/frontend처럼 작업지시서가 분리되어야 하면 서로 다른 `build-wave` Run, 보통 서로 다른 `BW-ID`로 나눈 뒤 순차 실행한다.
- Orchestrator는 기능 구현의 주 작성자가 아니라 작업지시, 검토, 통합, 검증, 상태 갱신 책임자다.
- 작은 기능, 단일 파일, 단일 테스트 변경이라도 Orchestrator가 곧바로 구현하지 않는다. 먼저 단일 worker Run 또는 Build Wave Run으로 작업 범위와 검증 기준을 만든다.
- Wave 시작과 완료는 `session.json` 수동 편집이 아니라 `vulcan.py wave-start`, `vulcan.py wave-complete`, `vulcan.py sync-session`으로 처리한다.
- Build Wave Run 생성 시 Orchestrator는 관련 ID를 손으로 넓게 나열하지 않고, 가능하면 상세 요구사항 또는 계약 seed를 사용해 `vulcan.py wave-start <BW-ID> --trace-seed <ID>` 또는 `vulcan.py run-new ... --trace-seed <ID>`를 먼저 사용한다.
- `--trace-seed`가 보강한 `related_ids`, `target_contracts`, `source_documents.reference_on_demand`는 추천값이다. Orchestrator는 worker 실행 전에 `scope.writable`, `target_contracts.interface_contract`, `contract_skeleton`, 검증 명령을 Program Design, Gate 3 테스트케이스, 실제 수정 범위 기준으로 확인하고 확정한다.

Wave 완료 검증은 전체 Gate 4 QA와 구분한다.

| 구분 | 책임 | 목적 | 예 |
| --- | --- | --- | --- |
| Worker self-check | worker | 자기 Run 범위가 깨지지 않았는지 확인 | 단위 테스트, API 계약 테스트, 컴포넌트 테스트, lint/build |
| Wave 종료 검증 | Orchestrator | 통합된 현재 코드가 Wave 계약과 기존 회귀 기준을 깨지 않았는지 확인 | worker 테스트 재실행, 전체 build, 관련 run-check |
| Gate 4 QA 검증 | QA/review/evidence | 사용자 시나리오, 화면 증적, 설계 계약 준수, 최종 테스트 결과를 판정 | `check-contract`, Playwright E2E, 상태/시나리오별 UI 증적, QA Finding/Test Result |

Wave가 전체 사용자 시나리오를 완성하지 않았다면 Wave 종료 시 전체 E2E나 최종 화면 증적을 요구하지 않는다.
Wave 검증은 Gate 3 테스트 설계 중 해당 Wave의 `target_contracts`에 매핑된 `UT/IT/UI` 또는 smoke 기준까지만 수행한다.
전체 통합 시나리오, 화면 상태별 증적, QA Pass 판정은 Gate 4에서 수행한다.
단, 하나의 Wave가 vertical slice를 완성했다면 해당 slice의 smoke 또는 제한된 E2E를 실행할 수 있다.
이 경우에도 보고 문구는 "전체 통합 테스트 완료"가 아니라 "해당 Wave 범위의 계약 테스트와 가능한 회귀 검증 완료"로 쓴다.

Gate 4 QA 검증은 가능하면 `qa-execution` worker Run으로 수행한다. QA worker는 테스트 명령, Playwright, 로그/증적 생성, 후보 FIND/CR/ISSUE 분류를 담당하고 소스코드 수정은 하지 않는다. 실패가 나오면 `Fail`, `Not Run`, `Skipped`, `environment_blocked` 중 하나로 기록하고 원인 가설, 재현 명령, 로그 경로, 영향 ID를 남긴다. Orchestrator는 이 보고를 사용자와 검토한 뒤 승인된 설계 범위 안의 결함만 별도 `qa-fix-loop` Run으로 수정한다.

`qa-fix-loop`는 코드/테스트 수정 Run이다.
파일명에는 `qa-fix-loop`와 대상 `FIND-ID`를 포함하고, `run_type: QAFix`로 작성한다.
Orchestrator는 `qa-fix-loop` Run의 수정 범위와 검증 명령을 확정한 뒤 native worker(subagent/thread/native branch agent)에게 구현 수정을 맡긴다. 외부 CLI 실행 증적이나 runner 격리가 필요하면 `agent-run`/`run-exec`를 선택할 수 있다.
Orchestrator는 직접 구현하지 않고 worker 결과 통합, `check-contract`, 관련 테스트, `run-check` 재검증, FIND 닫힘/CR 승격 후보 판단을 담당한다.
새 API, 새 메소드, 새 화면 상태, DB/보안/요구사항 계약 변경이 필요하면 `qa-fix-loop`에서 구현하지 않고 CR 후보로 멈춘다.

Gate 4 QA는 전체를 한 Run에 밀어 넣지 않는다. 구현 소스가 통합됐다는 사실은 QA 입력일 뿐이며, QA 시작 시 다시 실행 가능성을 확인해야 한다. 권장 QA Run 순서는 다음과 같다.

| QA Run | 목적 | 최소 산출물 |
| --- | --- | --- |
| `QA-000` 환경 준비/스모크 | 통합된 소스, 의존성, DB/포트/환경변수, backend/frontend 기동 가능성, Playwright 설치/브라우저 캐시 확인 | 환경 체크 로그, 차단 여부, 다음 QA Run 진행 가능 여부 |
| `QA-001` 명령 기반 검증 | backend/frontend test, lint, build, `check-contract`, `run-check` 실행. 필요 시 `check-trace` 상세 진단도 실행 | `QA-CMD-*` 로그, exit code, Pass/Fail/Not Run |
| `QA-002` UI/E2E 증적 | `QA-000`이 기록한 QA workspace에서 서버 기동 후 UI-ID별 Playwright screenshot/log/trace 생성 | `UI-*` screenshot, Playwright report/trace, UI-ID 매핑 |
| `QA-003` 결과 정리/판정 후보 | QA Finding/Test Result 정리, 추적표 반영 후보, Gate4 완료 판단 필요 항목 작성 | `DOC-QA-G4-001`, `DOC-QA-G4-002`, FIND/CR/ISSUE, 승인 질문 후보 |

QA workspace는 `QA-000`에서 한 번 정한다. 기본값은 `workflow.integration_branch`의 현재 작업공간이며, `QA-000`은 Gate 4 전체에서 재사용할 QA workspace 경로를 Run 결과에 기록해야 한다. Detached QA worktree는 프로젝트 정책에서 명시적으로 활성화한 경우에만 사용한다. `QA-001`, `QA-002`, `QA-003`은 그 경로를 기준으로 실행하며, 임의로 다른 workspace를 만들거나 기준선/통합 브랜치 작업공간을 섞어 실행하지 않는다. `QA-000` workspace가 없거나 차단되면 후속 QA Run은 `environment_blocked` 또는 Orchestrator 결정 필요 항목으로 반환한다.

Gate 4의 실제 테스트 실행 상태는 `DOC-QA-G4-002_Test-Result_v0.1.md`의 `결과` 컬럼을 원본으로 한다.
Gate 3 테스트케이스 문서는 계획과 기대 기준을 담는 문서이며, QA-003에서 Gate 3 문서의 `Planned` 상태를 `Pass`로 덮어써서 실행 결과를 표현하지 않는다.
`check-trace`는 Gate 4에서 QA 테스트 결과서를 우선 읽고, 결과서에 실행 상태가 없을 때만 Gate 3 테스트케이스를 fallback으로 참조한다.

`QA-000`의 최소 체크리스트는 다음이다.

- `python vulcan.py doctor --json` 결과를 `docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.json`에 저장했는가
- Gradle wrapper 또는 프로젝트 지정 backend 빌드 도구가 로컬 캐시/권한 기준으로 실행 가능한가
- backend 최소 smoke test, test discovery, 또는 컴파일 확인이 가능한가
- frontend 의존성이 설치되어 있거나 `npm ci`/`npm install`을 실행할 수 있는가
- Playwright package와 browser cache가 있거나 `npx playwright install`을 실행할 수 있는가
- backend/frontend 개발 포트(예: 8080, 5173 또는 프로젝트 지정 포트)가 사용 가능한가
- SQLite 또는 프로젝트 지정 DB 파일을 생성/접근할 수 있는가
- 필수 환경변수, test profile, 임시 디렉터리, 로그/증적 출력 디렉터리가 준비되어 있는가

QA-000 전 또는 QA-000 중 로컬 환경 차단이 의심되면 `python vulcan.py doctor --json`을 실행하고 결과 요약과 JSON 경로를 QA-000 로그 또는 Run 결과에 연결한다. `doctor`의 `fail`/`warn`은 QA 명령 실행 결과가 아니므로 UI/통합 테스트를 Pass/Fail로 대신 판정하지 않는다.

`QA-000`이 `environment_blocked` 또는 `Fail`이면 `QA-001`/`QA-002`를 억지로 진행하지 않는다. `QA-003`은 QA Pass를 확정하지 않고 Orchestrator가 사용자와 협의할 판정 후보만 정리한다.
이때 Orchestrator는 QA-000 Run의 doctor JSON과 evidence 로그를 먼저 확인하고, 환경 문제이면 `ISSUE`/`environment_blocked`로 보류하며, 제품 수정이 필요하다고 판단될 때만 사용자 결정 후 `qa-fix-loop`를 만든다.

Implementation Plan이 Wave 4개를 정의했다면, 실행 기록은 보통 다음처럼 1:N 구조가 된다.

```text
RUN-010_implementation-plan-...md
RUN-011_build-wave-BW-001_...md
RUN-012_build-wave-BW-002_...md
RUN-013_build-wave-BW-003_...md
RUN-014_build-wave-BW-004_...md
```

`Implementation Plan Run`은 전체 지도이고, `Build Wave Run`은 해당 Wave의 작업지시서이자 결과보고서다. backend와 frontend처럼 실제 지시서가 달라져야 하는 범위는 하나의 Wave 안에서 병렬 subagent로 나누지 말고 별도 Build Wave Run으로 분리한다. subagent에게는 전체 프로젝트 맥락을 과도하게 넘기기보다 해당 Wave Run의 목표, 관련 ID, 수정 허용 범위, 테스트, 완료 조건을 전달한다. worker는 요구사항추적표의 `Implemented` 또는 `Verified` 상태를 직접 확정하지 않고, 반영해야 할 ID와 증적 후보를 Orchestrator 결정 필요 항목으로 반환한다.

native worker(subagent/thread/native branch agent) 또는 외부 CLI runner 실행 전에 Orchestrator는 현재 실행할 Build Wave Run에 대해 `python vulcan.py run-preflight <run-file>`을 실행한다. `wave-start`와 `run-new --skill build-wave`는 Run 초안 생성 직후 preflight 경고/차단 항목을 안내한다. `run-exec`와 `agent-run --mode work`는 내부적으로 preflight를 자동 실행하며, 차단 항목이 있으면 worker를 시작하지 않는다. 단, native subagent/thread/Agy Workspace: branch 위임은 `run-exec` 경로를 타지 않으므로 Orchestrator가 직접 preflight를 실행해야 한다. 이 두 명령은 필수 실행 경로가 아니라 외부 CLI runner를 선택했을 때 쓰는 실행 옵션이다. `run-check`는 필수 필드와 완료 문서 형식을 확인하고, `run-preflight`는 worker에게 넘겨도 되는 작업지시서인지 확인한다. Preflight가 차단 항목을 반환하면 worker 실행 전에 Run을 보정한다.

`prepare-transition`은 현재 Gate에서 완료된 worker Run에 대해 preflight를 다시 돌려 차단 항목을 사후 점검한다. 이는 native 위임 전 preflight 누락을 발견하기 위한 안전망이며, worker 실행 전 검사 절차를 대체하지 않는다.

`Implementation Scaffold Run`은 업무 기능을 완성하는 Run이 아니다. 이 Run의 책임은 다음으로 제한한다.

- 개발표준정의서의 패키지/폴더/빌드 기준에 맞는 프로젝트 골격 생성
- Program Design의 `PGM/IF/MTH/DTO/Entity/Component` public contract를 실제 파일, class, interface, method signature로 생성
- Gate 3 테스트 설계에 대응하는 테스트 파일 또는 테스트 이름 skeleton 생성
- build/import/compile smoke 통과
- 다음 Build Wave가 채울 TODO/stub와 관련 ID 표시

Scaffold worker는 업무 로직, 전체 E2E, Gate 4 QA Pass, 릴리즈 판단을 완료 처리하지 않는다. 메소드 내부는 `TODO`, `NotImplemented`, 최소 wiring, 빈 adapter처럼 빌드가 깨지지 않는 수준으로만 둔다. 기능 구현은 이후 Build Wave worker가 담당한다.

`BW-000` scaffold Run은 요구사항, 테스트, UI 상태를 `Implemented`, `Verified`, `Pass`로 확정하지 않는다. skeleton 생성, build/import/compile smoke, 다음 Wave가 채울 TODO/stub 확인만 보고하고, 기능 구현 상태 반영은 `BW-001` 이후 또는 Orchestrator 재검증 뒤에 수행한다.

Scaffold Run의 권장 상태:

| 프로젝트 유형 | Scaffold 기준 |
| --- | --- |
| 신규 개발 | `contract_skeleton.mode: new`로 프로젝트 폴더, 빌드 설정, public signature, DTO/schema, 테스트 skeleton을 생성한다. |
| 고도화 | `contract_skeleton.mode: existing-alignment`로 기존 코드와 Program Design 계약을 매핑하고, 누락 skeleton은 보강하며, 설계와 기존 코드 충돌은 `ISSUE` 또는 `CR`로 반환한다. |
| 이미 정렬됨 | `contract_skeleton.mode: not-required`와 생략 사유, 확인한 파일/명령을 Run에 남긴다. |

작업자 runner에게 전달하는 `Build Wave Run`은 Orchestrator 통합 Run보다 얇아야 한다.
작업자 Run의 `working_documents`에는 현재 Run 문서, 담당 구현에 직접 필요한 개발표준/테스트케이스/UI 기준선만 두고, 요구사항정의서와 전체 설계 산출물은 `reference_on_demand`에 둔다.
작업자 Run의 `scope.writable`에는 담당 코드 경로, 담당 테스트 경로, 자기 Run 문서만 포함한다.
화면 증적처럼 worker가 직접 만들어야 하는 파일이 있을 때만 담당 증적 경로를 추가한다.
`session.json`, Gate 상태, 전체 추적표 갱신, 테스트 결과서 확정, `wave-complete`, `sync-session`, `prepare-transition`은 Orchestrator가 통합 단계에서 수행한다. `check-trace`는 추적성 상세 진단이 필요할 때 Orchestrator가 별도로 수행한다.

Build Wave Run의 `target_contracts.interface_contract`는 구현 worker에게 전달되는 핵심 계약이다. `skill: build-wave`인 Run에 `interface_contract`가 없으면 Orchestrator는 누락 사유를 명시해야 하며, class/method/schema 이름이 이미 Program Design에 있는데도 빠졌다면 Run을 보완한 뒤 실행한다.
Scaffold Run의 `target_contracts.contract_skeleton`은 필수다. 신규 개발인데 skeleton 대상 파일과 smoke 검증이 없으면 feature 구현으로 넘어가지 않는다.

Orchestrator는 worker worktree의 파일을 손으로 복사하지 않는다.
worker 완료 후 `python vulcan.py run-integrate --run-id RUN-NNN --dry-run`으로 변경 파일을 수집하고, `scope.writable`/`scope.excluded` 위반 여부를 먼저 판정한다.
위반 파일이나 충돌이 있으면 Orchestrator가 직접 수정하지 않고 재작업 Run, QA Fix Run, Traceability Run, FIND/CR/ISSUE 중 하나로 돌려보낸다.
`run-integrate --apply`는 허용 diff를 반영하는 팬인 동작일 뿐이며, 테스트 작성, 코드 보정, 추적표 보정, Gate/session 갱신을 대신하지 않는다.

단, scope 위반 파일이 `playwright.config.*`, `vite.config.*`, `vitest.config.*`, `tsconfig*.json`, `eslint.config.*`, `pytest.ini`, `pyproject.toml`, `package.json`, lockfile처럼 테스트/빌드 실행 설정일 수 있으면 `run-integrate --dry-run`은 `Config Hotfix Candidate`로 분류할 수 있다.
이 분류는 자동 승인이 아니다. Orchestrator는 다음 중 하나를 명시적으로 선택해야 한다.

1. Config Hotfix로 수용하고 Run의 `scope.writable` 또는 결과 기록을 보정한 뒤 검증을 재실행한다.
2. 승인된 설계 범위 안의 결함 수정이면 `qa-fix-loop`로 분리한다.
3. 의존성, 보안, API/DTO/DB/UI 계약 변경이면 `CR` 후보로 승격한다.
4. 해당 변경이 부적절하면 worker 변경을 거부하거나 되돌린다.

`package.json`, lockfile, `pyproject.toml`은 dependency/security 영향이 있을 수 있으므로 Config Hotfix 후보로 보이더라도 dependency review가 필요하다.

Codex desktop의 `spawn_agent`, Codex thread, Claude subagent, Agy workspace branch agent 같은 런타임 native worker는 같은 Gate/Run 계약 안에서 우선 사용할 수 있다.
외부 CLI runner(`agent-run`/`run-exec`)는 장시간 독립 실행, cross-runner 검증, 별도 프로세스 로그/timeout/watchdog 증적이 필요한 경우에 사용한다.

subagent/thread가 직접 작업했다면 Orchestrator는 결과를 현재 Run 또는 별도 Run에 `delegation_records`로 정규화한다.
이 기록은 `Run Execution Record`보다 얇다. stderr, jsonl, cache, timeout policy 같은 외부 프로세스 메타는 필요 없지만, 위임 대상, 작업 범위, 변경 파일, 결과 요약, Orchestrator 재검증 명령은 남긴다.

`delegation_records.status`는 worker lifecycle과 Orchestrator 검증 lifecycle을 분리해서 쓴다. `worker_completed` 또는 `completed`는 worker가 결과를 반환했다는 뜻이고, `verified`는 Orchestrator가 테스트/증적/계약을 재검증한 뒤에만 쓴다. worker 완료만 기록된 Run은 `run-check`/`run-preflight`에서 경고가 날 수 있으므로, Orchestrator는 `orchestrator_verification` 또는 `needs_review`/`blocked` 같은 판정 후보를 남긴다.
PoC 병목 분석이 필요하면 `first_file_change_at`, `last_file_change_at`, `worker_final_response_at`, `final_response_lag_seconds`를 함께 남겨 코드 변경 시간과 최종 응답 지연을 구분한다. 알 수 없는 값은 추정하지 않고 비워두거나 notes에 근거를 남긴다.
변경 파일은 `scope.writable` 안에 있는지 확인하고, worker/subagent가 만든 테스트케이스와 관련 회귀 검증을 Orchestrator가 재실행한다.

Orchestrator 직접 수정 예외:

- 사용자가 "worker를 사용하라"고 명시하지 않았다는 점은 Orchestrator 직접 구현 사유가 아니다.
- 구현 승인이 떨어지면 Orchestrator는 별도 요청이 없어도 native worker(subagent/thread/native branch agent) 위임을 기본 절차로 적용한다. `agent-run`/`run-exec`는 외부 CLI runner가 필요할 때 선택한다.
- 허용 예외: worker 결과 통합 중 충돌 해결에 필요한 최소 연결 수정, 문서/추적표/session 갱신, 검증 명령 보정, 명백한 오타나 경로 오류 수정.
- 추가 허용 예외: worker/subagent/thread 실행 불가가 확인된 경우, 긴급한 1~2줄 연결 수정, 사용자가 Orchestrator 직접 구현을 명시 승인한 경우.
- 금지 기본값: 신규 기능 코드 작성, API/DB/UI 동작 구현, 테스트 케이스 본문 작성, 개발표준 위반 리팩터링을 Orchestrator가 혼자 완료 처리하는 것.
- 예외 사용 시 Run에 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 실행 검증, 후속 worker 또는 QA 검수 필요 여부를 남긴다.
- 직접 구현 예외는 순 변경량 약 30 LOC 이하, 수정 파일 2개 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능할 때만 허용한다.
- 예외 Run에는 `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, `direct_edit_scope.verification`, `direct_edit_scope.followup_review_required`를 남긴다.
- 위 기준을 넘거나 판단이 애매하면 작업을 Build Wave Run 또는 worker Run으로 나눈다. 3개 이상 파일, 약 100 LOC 이상, 15분 이상 예상, backend/frontend 동시 변경, 새 API/메소드/DTO/DB/SCR/PGM 계약 추가는 분리 신호다.
- subagent를 여러 개 병렬로 호출해 구현했다면 직접 구현이 아니라 Build Wave 실행으로 기록한다. 해당 Wave Run의 `target_contracts`, `scope.writable`, worker/subagent 목록, 통합 검증을 남긴다.

CLI worker 실행에서는 `docs/runs/_exec/<TARGET-ID>_<runner>-status.json` heartbeat를 남긴다.
worker는 정확한 시간 간격을 맞추는 대신 시작, 컨텍스트 로딩, 편집, 테스트, 결과 작성, 완료/차단/실패처럼 단계가 바뀔 때 `phase`와 `current_task`를 갱신한다.
Orchestrator와 대시보드는 이 파일의 수정시각과 한 줄 `current_task`를 보고 worker가 실제로 움직이는지 판단한다.
Codex/Claude처럼 resume 가능한 runner는 `thread_id` 또는 `session_id`가 남아 있으면 무결과/준비응답 실패를 1회 재지시로 회수할 수 있다.
resume도 대시보드에 보이게 하려면 원시 CLI 명령을 직접 실행하지 않고 `python vulcan.py agent-resume --target-id RV-NNN|RUN-NNN --runner codex-cli|claude-cli`로 실행한다.

Gate 4 QA Finding 문서는 결함이 없어도 Draft 빈 문서로 남기지 않는다. 신규 FIND가 없으면 `No Findings`로 명시하고, 근거 Run/Test Result/증적을 연결한다.
Playwright dialog는 무조건 accept해서 숨기지 않는다. 예상된 dialog는 메시지와 증적을 남기고 처리할 수 있지만, 예상하지 않은 dialog는 Fail 또는 FIND 후보로 기록한다.

Build Wave 분할을 생략하는 경우에도 구현 Run은 worker 실행 단위여야 하며 다음을 남긴다.

- 생략 이유
- 단일 Run으로 처리할 구현 범위
- 담당 worker 또는 subagent
- 관련 ID
- 실행할 테스트와 검증 명령

PoC에서 구현 worker는 `app/`, `static/`, `tests/`, `requirements.txt`와 최소 self-check를 담당한다. README, 최종 테스트 결과서, browser smoke/screenshot, release/backlog, 증적 로그 정규화까지 맡기면 Impl 비용이 실제 코드 비용처럼 보이므로 worker handoff 전에 분리한다.
PoC Impl worker의 완료 기준은 `코드 변경 + 빠른 self-check + 남은 판단 항목 보고`다. Gate 4 smoke/evidence/report는 별도 QA/Evidence 단계가 담당한다. 이미 worker가 진행 중이고 코드 구현은 끝난 상태에서 문서/경고 정리에 오래 머문다면 Orchestrator가 증적 정리와 Run 경고 정규화를 회수한다.
Agy `Workspace: branch` 또는 native branch worker가 격리 workspace 안에서 Run 문서를 직접 수정하지 못한 경우도 정상 경로로 처리할 수 있다. worker는 변경 파일과 self-check 결과를 반환하고, Orchestrator가 부모 workspace에서 `delegation_records`, Run 결과, scope 검증을 정규화한다.
- 추적표 갱신 기준
- 커밋 메시지 후보

권장 상태값:

| 상태 | 의미 |
| --- | --- |
| `Planned` | 계획됨 |
| `In Progress` | 구현 중 |
| `Implemented` | 코드 작성 완료 |
| `Verified` | Wave 검증 통과, `open_issues` 없음 |
| `CompletedWithIssues` | 주요 결과는 있으나 후속 보정/검수/CR/FIND/ISSUE 분류가 필요 |
| `Blocked` | 질문, 설계 누락, 환경 문제로 중단 |
| `Rolled Back` | 해당 Wave 변경을 되돌림 |

Gate 2에서 Gate 3로 넘어가기 전에는 다음 검수가 완료되어야 한다.

SW 아키텍처는 Gate 2 안에서 점진적으로 성숙시킨다.
Gate 2의 세부 산출 순서는 `docs/core/GATE2_DESIGN_SEQUENCE.md`를 기준으로 한다.
Orchestrator는 각 Gate 2 Run에 현재 순서 위치와 다음 Gate 2 Run 후보를 남긴다.

| 시점 | Orchestrator 책임 | 권장 검증 |
| --- | --- | --- |
| Gate 2 시작 | Architecture Draft를 만들고 C1/C2, 주요 CNT, 주요 ADR 후보, Pending 항목을 드러낸다 | `python vulcan.py check-architecture --level draft` |
| 상세 설계 작성 후 | 기능/프로그램/API/DB/화면/보안가이드 내용을 아키텍처의 CMP/FLOW/품질속성/상세 설계 연결로 되돌려 반영한다 | `python vulcan.py check-architecture --level baseline` |
| Gate 3 진입 전 | Gate 3 테스트 설계에 영향을 주는 Pending을 닫거나 RISK/ASM/Q/ISSUE/CR로 분류한다 | `python vulcan.py status --check` |

SW 아키텍처의 물리/운영 상세가 필요한 경우 `DOC-ARCH-G2-002_Deployment-Infrastructure-Architecture_v0.1.md`를 함께 작성한다.
이 문서는 인프라 담당자의 상세 장비/네트워크 설정서를 대체하지 않고, SW 운영자가 알아야 할 배포 토폴로지, L2/L3/L4/WAF/FW/WAS/DB/Storage/Monitoring 연결, 이중화, 포트/프로토콜, TLS 종료 위치, health check, 세션, DB failover, 파일 저장소, 로그/백업/모니터링 영향을 기록한다.
사용자나 인프라 담당자가 정보를 주지 않은 값은 추측해서 채우지 않는다. `TBD`로 두되 확인 질문, 미확정 영향, 확인 책임, 목표 시점, Gate 전 처리 필요 여부를 반드시 남긴다.
구현이나 QA에 영향을 주는 인프라 `TBD`는 Gate 3 또는 Impl 전에 `RISK`, `ASM`, `Q`, `ISSUE`, `CR` 중 하나로 분류한다.

Gate 2가 작지 않으면 하나의 설계 Run에 모든 산출물을 밀어 넣지 않는다.
화면, API, DB, 보안, 개발표준이 함께 바뀌거나 아키텍처 Pending/ADR 후보가 여러 개면 Gate 2를 작은 Run으로 나누고, 마지막 Run에서 SW Architecture Baseline과 전체 설계 일관성을 검수한다.

| 검수 | 책임 Persona | 최소 확인 |
| --- | --- | --- |
| 요구사항 대비 설계 검수 | `review` 또는 `design` | 모든 `REQ/AC`가 `FUNC/SCR/PGM/DB/SEC` 중 필요한 산출물과 연결됨 |
| 보안 검수 | `security-review` | `SECURITY_BASELINE.md` 기준 보안항목 누락 여부, `KISA/SR`, `OWASP`, `CWE` 매핑 |
| 화면 검수 | `screen-review` | 화면 목록, 화면 상태, 와이어프레임/시안, 메시지, UI Implementation Contract, UI 증적 기준 |
| UI 품질 검수 | `ui-review` | 구현자가 임의 해석하지 않도록 UI 기준선 유형, 구현 계약, 레이아웃 밀도, 상태 표현, 모바일 기준이 충분한지 확인 |
| 개발표준 검수 | `development-review` | 언어/프레임워크, 기술스택 베이스라인, 패키지 구조, 메시지 관리, 주석/코딩/테스트 컨벤션, 빌드/실행 명령 |
| 배포·운영 인프라 검수 | `architecture` 또는 `review` | L4 health check, TLS 종료, WAS/DB 이중화, 포트/프로토콜, 파일 저장소, 로그/백업/모니터링 미확정 영향 |

위 검수 중 하나라도 `Failed` 또는 `Blocked`이면 Gate 3 테스트 설계로 넘어가지 않는다.

화면이 있는 기능은 다음 흐름을 가진다.

| 단계 | 책임 Persona | 최소 산출물 |
| --- | --- | --- |
| Gate 2 | `screen-design` | `SCR-ID`, 화면 상태, 시안/와이어프레임 경로, 기준 viewport, 비교 기준 |
| Gate 2 | `screen-design` | 화면 퍼블리싱 산출물 또는 외부 시안이 구현 기준이면 UI Implementation Contract 작성 |
| Gate 2 Review | `screen-review`, `ui-review` | 화면 누락, 상태 누락, 시안 연결, 구현 계약, 증적 가능 여부와 UI 품질 기준선 검토 |
| Gate 3 | `test-design` | `UI-ID`, viewport, 사용자 흐름, 기대 화면, Contract 반영 캡처/비교 기준 |
| Impl | `build` | UI Implementation Contract를 확인하고 시안을 실제 UI 코드로 구현 |
| Gate 4 | `evidence`, `screen-review` | Playwright 설치/실행 결과, 상태별 스크린샷, 기준 UIREF 대비 구현 차이, 허용 여부, UI Finding 또는 승인 |

화면 QA 증적은 Playwright를 기준으로 한다.
Playwright가 설치되어 있지 않으면 `npm install -D @playwright/test`와 `npx playwright install`을 실행한 뒤 `npx playwright test`로 재검증한다.
CDP, 브라우저 수동 캡처, 런타임 Preview 캡처는 보조 관찰로만 남길 수 있으며, Playwright 실행 결과 없이 UI Pass를 확정하지 않는다.

외부에서 가져온 시안도 Anvil 산출물이다. 외부 Figma, 이미지, PPT, 손그림, 기존 시스템 캡처는 화면설계서에 출처와 경로를 기록하고 `SCR-ID`와 연결해야 한다.
화면 퍼블리싱 산출물이나 외부 시안이 구현 기준이면 `UI Implementation Contract`로 승격해야 한다.
계약에는 기준 파일, 기준 CSS/토큰, 필수 유지 요소, 변경 허용 항목, 변경 금지 항목, 비교 방식, 차이 발생 시 FIND/CR 판정 기준이 있어야 한다.
계약이 없으면 구현자는 시안을 참고자료로만 볼 수 있으므로 Gate 3 또는 구현으로 넘기지 않는다.

Implementation Run은 다음 조건을 만족해야 완료할 수 있다.

개발표준정의서는 구현자가 참고해도 되는 선택 문서가 아니라 구현 계약이다.
구현 착수 전에 build persona 또는 Build Wave Run은 개발표준정의서의 패키지 구조, 계층 책임, 로깅, 주석, 예외/메시지, 테스트 명령 기준을 확인하고 작업지시서에 준수 항목을 남겨야 한다.
Build Wave Run에는 `development_standards_applied`와 `development_standard_checklist`를 포함해 로깅, 주석/JavaDoc/docstring, 테스트 설명 기준을 worker에게 직접 전달한다.
worker는 logger 선언, 주요 class/public 업무 method 설명, 테스트의 입력값/기대값/출력값 또는 Given/When/Then 설명 준수 여부를 결과에 남긴다.
Spring Boot 프로젝트에서 `domain/{feature}` 래퍼를 쓰려면 DDD 구조 선택 사유가 개발표준정의서에 있어야 하며, 사유가 없으면 base package 바로 아래 `auth/`, `user/`, `{feature}/`, `security/`, `common/` 구조를 기준으로 구현한다.
로깅과 주석 기준이 비어 있거나 구현자가 바로 적용할 수 없으면 코딩으로 넘어가지 않고 개발표준 보완 `FIND` 또는 범위 변경 `CR`로 분류한다.
프로그램 설계서는 구현 계약이다. 구현 worker는 관련 `PGM-ID`, 컴포넌트 책임, Interface Contract, Abstract Base Contract, Public Method Contract, DTO/Entity/Data Contract, 오류/예외/메시지, 트랜잭션/보안/로깅 기준을 확인한 뒤 작업한다.
Build Wave와 worker Run은 시간이나 파일 개수가 아니라 닫힌 기능/프로그램 계약 단위로 나눈다. 10분 내외, 최대 15분 권장은 보조 기준이며, 시간이 부족하다는 이유로 빌드/테스트가 깨진 중간 구현을 완료 처리하지 않는다.

| 조건 | 최소 확인 |
| --- | --- |
| 개발표준 준수 | 개발표준정의서가 Draft가 아니고 언어, 기술스택 베이스라인, 구조, 메시지, 주석, 테스트, 보안 기준, 필수 검증 명령을 가진다. |
| 프로그램 계약 준수 | 관련 프로그램 설계서의 컴포넌트, 인터페이스, public method, DTO/Entity, 오류/보안/로깅 계약과 구현이 모순되지 않는다. |
| Run 분할 적정성 | worker Run의 `target_contracts`가 완료 가능한 기능/프로그램 계약 단위이고 시간 기준은 보조 기준으로만 사용된다. |
| 구현 파일 연결 | 요구사항추적표의 증적에 실제 구현 파일 경로가 연결된다. |
| 추적 ID 표시 | 구현 또는 테스트 파일 안에 관련 `REQ`, `PGM`, `SCR`, `SEC`, `UT`, `IT` 중 하나 이상의 ID가 남는다. |
| 테스트 실행 | Gate 3에서 정의한 테스트와 개발표준정의서의 필수 검증 명령이 실행되고 Pass/Fail/Skip/Not Run 상태가 기록된다. |
| 화면 구현 검증 | 화면이 있으면 Playwright로 기준 시안 또는 화면설계서와 실제 구현 화면을 desktop/mobile에서 확인하고, UI Implementation Contract 대비 차이를 기록한다. |
| 문서 갱신 | 구현 결과가 테스트케이스와 Run 기록에 반영되고, 추적표 상태는 Orchestrator 재검증 후 반영된다. |

## 6. 승인과 질문 규칙

에이전트는 다음 상황에서 작업을 멈추고 질문해야 한다.

- 요구사항이 서로 충돌한다.
- 승인된 ID를 변경해야 한다.
- 현재 Gate보다 앞선 산출물, 구현, 테스트, 증적을 생성해야 한다.
- Run Scope 밖의 파일을 수정해야 한다.
- 민감문서 또는 제외 경로를 읽거나 포함해야 한다.
- 보안 기준을 낮추는 선택이 필요하다.
- 테스트 결과를 통과로 볼 수 없는 애매한 상태가 발생한다.
- 개발표준정의서의 필수 검증 명령을 실행하지 못했거나 실행 결과를 남기지 못했다.

다음 상황에서는 에이전트가 합리적으로 판단하고 진행할 수 있다.

- 문서의 기존 패턴과 일치하는 필드 추가
- 명백한 오탈자 수정
- 테스트 통과를 위한 좁은 범위의 구현 보정
- `.gitignore`에 생성물 제외 규칙 추가
- 추적표에 이미 존재하는 ID의 증적 경로 추가

## 7. 산출물 갱신 규칙

에이전트가 코드를 변경하면 최소한 다음 항목을 점검한다.

- 관련 프로그램 설계의 `PGM` 설명과 실제 구현이 맞는가
- 관련 화면명세의 `SCR` 설명과 실제 화면이 맞는가
- 관련 테스트케이스의 `UT`, `IT`, `PT`, `UI`가 존재하는가
- 테스트 결과서가 최신 실행 결과를 반영하는가
- 요구사항추적표의 상태와 증적이 갱신되었는가

문서 갱신이 이번 Run 범위 밖이면 `ISSUE` 또는 다음 Run 제안으로 남긴다.

## 8. Adapter 책임

Adapter는 Core 규약을 특정 에이전트 실행 방식으로 변환한다.

Adapter가 책임지는 것:

- Core 입력 계약을 모델별 프롬프트나 명령으로 변환
- 세션 컨텍스트 길이에 맞춰 문서 요약/선별
- 도구 사용 가능 여부 확인
- 실행 결과를 Core 출력 계약으로 정규화
- 실패, 중단, 사용자 질문을 일관된 상태로 기록

Adapter가 책임지지 않는 것:

- Core ID 체계 임의 변경
- 프로젝트 산출물 종류 임의 축소
- 승인 없이 Gate 완료 기준 완화
- 민감문서 커밋 또는 외부 전송

## 9. 상태 값

Run 상태는 다음 값을 사용한다.

| 상태 | 의미 |
| --- | --- |
| Planned | 실행 전 |
| Running | 실행 중 |
| Blocked | 질문, 승인, 환경 문제로 중단 |
| Completed | 완료 조건 충족 |
| CompletedWithIssues | 주요 결과는 있으나 후속 이슈 존재 |
| Failed | 완료 조건 미충족 |
| Cancelled | 사용자 또는 상위 계획에 의해 취소 |

## 10. 실패 기록 규칙

실패는 숨기지 않는다.

실패한 Run은 다음을 남긴다.

- 실패한 명령 또는 작업
- 관찰된 오류
- 영향받는 ID
- 재시도 여부
- 후속 조치 제안

예시:

```yaml
run_id: RUN-004
status: Blocked
blocked_reason: "브라우저 캡처 도구가 networkidle 대기 옵션을 지원하지 않음"
affected_ids:
  - UI-003
resolution: "load 상태 대기와 명시적 안정화 대기로 캡처 재시도"
```

## 11. 최소 파일 구조

프로젝트는 에이전트 실행 기록을 다음 위치 중 하나에 둘 수 있다.

```text
docs/runs/
```

권장 파일명:

```text
RUN-001_{run-name}_v0.1.md
```

Adapter별 내부 로그는 필요하면 다음 위치를 사용한다.

```text
docs/adapters/{adapter-name}/
```

단, 모델별 내부 로그에는 민감정보, 토큰, 외부 비공개 데이터가 포함되지 않아야 한다.
