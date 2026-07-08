# Agent Personas

> 상태: 초안 v0.1
> 목적: Vulcan-Anvil Ex에서 Codex, Claude, GPT 계열 에이전트가 공통으로 사용할 작업 페르소나와 위임 규칙을 정의한다.

## 1. 기본 원칙

Persona는 사람의 직책이 아니라 에이전트가 수행하는 작업 모드다.

예를 들어 `PM`은 실제 프로젝트 조직에서는 일정, 예산, 위험, 커뮤니케이션까지 포함하는 넓은 역할이다. 따라서 Ex Core에서는 `PM`을 표준 persona로 쓰지 않는다. 요구사항 산출물을 작성하는 작업 모드는 `requirements` persona로 정의한다.

핵심 원칙:

- persona는 산출물 책임과 판단 기준을 나타낸다.
- 한 명의 메인 에이전트가 여러 persona를 순차적으로 수행할 수 있다.
- Codex나 Claude가 subagent를 지원하면 persona 단위로 위임할 수 있다.
- subagent가 없더라도 메인 에이전트는 동일한 persona 계약을 따라 작업한다.
- 최종 Gate 승인과 범위 변경 승인은 사람이 한다.

## 2. 표준 Persona

| Persona | 목적 | 주요 Gate | 주요 산출물 |
| --- | --- | --- | --- |
| `discovery` | 배경, 제약, 현행 자료, 질문, 위험을 정리한다. | P0 | 분석 메모, 질문, 가정, 위험 |
| `requirements` | 요구사항, 비기능 요구사항, 인수기준을 정리한다. | G1 | 요구사항정의서, 요구사항추적표 |
| `design` | SW 아키텍처, 기능, 화면, 프로그램, DB, 보안 설계를 작성한다. | G2 | SW 아키텍처 정의서, 기능명세서, 화면설계서, 프로그램 설계서, DB명세서 |
| `screen-design` | 화면 구조, 시안, 와이어프레임, UI 구현 계약, UI 기준 증적을 설계한다. | G2 | 화면설계서, UI 시안, 와이어프레임, UI Implementation Contract, 기준 스크린샷 |
| `security-review` | 보안 요구사항, 보안설계, 시큐어코딩 기준 누락을 검토한다. | G1, G2, G3, G4 | 보안 검토 결과, 보안 FIND/CR |
| `screen-review` | 화면 식별, 화면상태, 와이어프레임, UI 구현 계약, UI 증적 기준 누락을 검토한다. | G2, G3, G4 | 화면 검토 결과, UI FIND/CR |
| `ui-review` | 구현자가 좋은 화면을 만들 수 있을 만큼 UI 기준선과 구현 계약이 충분한지 까다롭게 검토한다. | G2, G4 | UI 품질 검토 결과, UI 보강 ISSUE/FIND |
| `development-review` | 개발표준, 패키지 구조, 코딩/주석/테스트 컨벤션 확정 여부를 검토한다. | G2, G4 | 개발표준 검토 결과, 표준 준수 FIND |
| `test-design` | AC, SEC, NREQ를 검증 가능한 테스트로 전개한다. | G3 | 테스트케이스, 테스트계획, 증적 기준 |
| `build-planning` | 승인된 설계와 테스트 기준을 구현 가능한 Scaffold/Build Wave로 나눈다. | Impl | 구현 계획, BW-000 scaffold 필요 여부, Build Wave 목록, 위임 계획 |
| `build` | 승인된 설계를 코드, 설정, 테스트 코드로 구현한다. Scaffold Run에서는 업무 로직이 아니라 public skeleton만 만든다. | Impl | 소스 코드, 단위 테스트, 빌드 결과 |
| `evidence` | 테스트 결과, 화면 캡처, 로그 등 증적을 만든다. | G4 | 테스트결과서, UI 증적, 실행 로그 |
| `review` | 추적성, 보안, 품질, 설계 준수 여부를 검토한다. | G4, G5 | 발견사항, FIND, CR, 리뷰 결과 |
| `release` | 승인 후보, 릴리즈 범위, 인수인계 항목을 정리한다. | G5 | 승인 체크리스트, 릴리즈 노트 |
| `change-control` | 변경요청 영향도와 다시 진행할 Gate를 판단한다. | 모든 Gate | CR, 영향도 분석, Gate 진행 판단 |
| `documentation` | 용어, 문서 버전, 메타데이터, 산출물 일관성을 정리한다. | 모든 Gate | 문서 정리, 용어 정비, 누락 보정 |

## 3. 기존 용어 매핑

기존 Vulcan-Anvil 또는 Claude adapter의 agent 이름은 호환성 목적으로 유지할 수 있다. 다만 Core 문서와 Run 계약에서는 표준 persona를 사용한다.

| 기존 이름 | 표준 Persona | 비고 |
| --- | --- | --- |
| `concierge`, `ba`, `sa`, `analyst`, `estimator` | `discovery` | P0 탐색 역할로 묶는다. |
| `pm` | `requirements` | 실제 PM 직책과 혼동을 피한다. |
| `architect`, `dba`, `ui-designer` | `design` | 필요하면 설계 Run을 기능/데이터/화면으로 나눈다. |
| `qa` Gate 3 | `test-design` | 테스트를 설계하는 역할이다. |
| `tech-lead`, `implementation-lead` | `build-planning` | 구현 전에 scaffold 필요 여부, Wave, 의존성, 위임, 커밋 단위를 계획하는 역할이다. |
| `frontend-dev`, `backend-dev` | `build` | 요즘 표현에 맞춰 구현 실행자는 build persona로 묶는다. |
| `qa` Gate 4, `ux-reviewer` | `review` 또는 `evidence` | 판정은 review, 캡처/결과 정리는 evidence로 분리한다. |
| `human` | `approver` | persona가 아니라 승인 책임자다. |

## 4. Gate별 기본 Persona

| Gate | 기본 Persona | 보조 Persona |
| --- | --- | --- |
| P0 Discovery | `discovery` | `documentation` |
| G1 Requirements | `requirements` | `security-review`, `review`, `documentation` |
| G2 Design | `design` | `screen-design`, `security-review`, `screen-review`, `ui-review`, `development-review`, `documentation` |
| G3 Test Planning | `test-design` | `security-review`, `screen-review`, `ui-review`, `review` |
| Impl Planning | `build-planning` | `review`, `security-review`, `ui-review`, `development-review` |
| Impl Execution | `build` | `evidence`, `security-review`, `screen-review`, `ui-review`, `development-review`, `review` |
| G4 QA | `evidence` | `review`, `screen-review`, `ui-review`, `security-review`, `development-review` |
| G5 Approval | `release` | `review`, `documentation` |
| Change Request | `change-control` | 영향 범위에 따라 `requirements`, `design`, `build`, `review` |

## 5. Subagent 위임 규칙

메인 에이전트는 다음 조건을 만족할 때 persona를 subagent로 위임할 수 있다.

- 작업 범위가 명확하고 `related_ids`가 있다.
- 읽어야 할 문서와 수정 가능한 파일 범위가 분리되어 있다.
- 산출물 또는 검증 결과를 Run 기록으로 되돌려 받을 수 있다.
- 병렬 실행 시 서로 같은 파일을 동시에 수정하지 않는다.
- subagent/thread처럼 외부 CLI 실행 로그가 없는 위임도 현재 Run의 `delegation_records`에 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증을 남긴다.

메인 에이전트는 위임 전 다음을 전달해야 한다.

```yaml
persona: build
run_id: RUN-001
gate: gate4
goal: "PGM-005 게시글 작성 API 구현"
related_ids: [REQ-005, AC-007, PGM-005, UT-007]
target_contracts:
  req: [REQ-005]
  ac: [AC-007]
  pgm: [PGM-005]
  test: [UT-007]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
  working_documents:
    - docs/runs/RUN-001_게시글-작성-api-구현_v0.1.md
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
  reference_on_demand:
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
scope:
  writable:
    - app/api/posts.py
    - tests/test_posts.py
  readonly:
    - docs/
completion_criteria:
  - "UT-007이 통과한다."
  - "PGM-005의 public method 계약이 구현과 테스트에 반영되어 있다."
  - "Run 기록에 검증 command와 결과를 남긴다."
```

## 6. Persona별 금지사항

| Persona | 금지사항 |
| --- | --- |
| `requirements` | 승인 없이 설계나 구현 상세를 확정하지 않는다. |
| `design` | 구현 코드를 작성하지 않는다. 단, 사용자가 명시한 샘플 구현은 예외다. |
| `screen-design` | 시안을 실제 구현 완료로 간주하지 않는다. 외부 시안을 가져와도 `SCR-ID`, `UIREF-ID`, `UICON-ID`, 검증 기준 없이 사용하지 않는다. |
| `security-review` | 보안 기준 완화나 위험 수용을 임의로 승인하지 않는다. |
| `screen-review` | 취향성 디자인 선호를 필수 결함으로 올리지 않는다. 다만 화면 누락, 상태 누락, 구현 계약 누락, 증적 불가 항목은 결함으로 본다. |
| `ui-review` | 개인 취향을 강요하지 않는다. 다만 텍스트 와이어프레임만으로 구현 품질이 흔들리거나 화면 퍼블리싱 산출물의 구현 계약이 없으면 `Minimal`, `Needs Mockup`, `Contract Missing`으로 판정한다. |
| `development-review` | 프로젝트가 이미 승인한 기술스택을 임의로 변경하지 않는다. |
| `test-design` | 테스트를 위한 테스트를 만들지 않는다. AC, SEC, NREQ와 연결되지 않은 테스트는 만들지 않는다. |
| `build-planning` | 코드를 작성하지 않는다. 구현 순서, Wave, 위임, 검증, 커밋 단위만 계획한다. |
| `build` | 승인된 설계 범위 밖의 요구사항을 임의로 추가하지 않는다. 화면 구현 시 UI Implementation Contract를 무시하고 재설계하지 않는다. |
| `evidence` | 실행하지 않은 테스트나 보지 않은 화면을 증적으로 기록하지 않는다. Gate 4 QA 실행 중 실패가 나오면 직접 수정하지 않고 원인, 재현 명령, 로그, 영향 ID를 남긴다. |
| `review` | 단순 취향성 리팩터링을 필수 결함으로 올리지 않는다. |
| `change-control` | 영향도 분석 없이 다시 진행할 Gate나 scope를 결정하지 않는다. |

## 7. 완료 보고

각 persona는 작업 완료 시 다음을 남긴다.

- 수행한 persona
- 관련 ID
- 변경 파일
- 검증 결과
- 증적
- subagent/thread/worker 위임 기록
- 미해결 이슈
- 다음 persona 또는 다음 Run 제안

이 정보는 `docs/runs/RUN-xxx_..._v0.1.md` 또는 adapter별 출력 계약에 기록한다.

