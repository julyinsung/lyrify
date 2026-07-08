# Vulcan-Anvil Ex Delivery Profiles

> 상태: 초안 v0.2
> 목적: 프로젝트 성격에 따라 문서 깊이, Gate 엄격도, 승인 절차, 증적 수준을 조절하는 기준을 정의한다.

## 1. 배경

Vulcan-Anvil Ex는 감리 대응형 프로젝트에서 강하게 동작하도록 설계되었다.
하지만 모든 작업이 공공/SI/감리 수준의 산출물과 검수 강도를 필요로 하지는 않는다.

작은 PoC, 내부 검증, 제품/업무 앱 개발, 개인 기능 개발에 같은 절차를 적용하면 개발보다 문서와 검수 비용이 더 커질 수 있다.
반대로 감리 대응 프로젝트에서 절차를 너무 줄이면 요구사항, 설계, 테스트, 증적, 변경관리의 추적성이 무너질 수 있다.

따라서 Vulcan-Anvil Ex는 프로젝트 성격별 기본값 묶음인 `Delivery Profile`을 둔다.

## 2. 용어

`Delivery Profile`은 프로젝트 성격에 따라 다음 항목의 기본 강도를 조절하는 실행 프로파일이다.

- 문서 깊이
- Gate 엄격도
- 사용자 승인 지점
- 테스트와 증적 수준
- 변경관리와 릴리즈 관리 방식
- 대시보드에서 강조할 상태 정보

Profile은 Core 규칙을 없애는 예외가 아니다.
Core의 ID, Run, Traceability, Gate 원칙은 유지하되, 프로젝트 목적에 맞게 산출물 깊이와 검증 범위를 조절한다.

Profile은 별도 Core 문서 세트가 아니라 `Core + Profile Overlay`로 운영한다.
즉 `audit`, `product`, `poc`마다 규칙을 복제하지 않고, 동일한 Core 문서와 명령을 사용하되 산출물 필수 여부, 검사 엄격도, 승인 지점, 증적 수준만 Profile Overlay로 조정한다.
Profile이 달라져도 Run, ID, Traceability, Gate, Worker, QA의 기본 의미는 바뀌지 않는다.

## 3. Profile 분류

| Profile | 대상 | 특징 | 기본 강도 |
| --- | --- | --- | --- |
| `Audit Profile` | 공공/SI/감리 대응 프로젝트 | 요구사항, 설계, 테스트, 보안, 증적, CR을 가장 엄격하게 관리 | 높음 |
| `Product Profile` | 일반 앱/제품/업무 시스템 개발 | 품질은 유지하되 감리 제출 수준의 문서/증적 밀도는 줄이고, 제품 로드맵, 릴리즈, 아키텍처 결정, 품질 기준 중심으로 운영 | 중간 |
| `PoC Profile` | 실험/검증/프로토타입 | Phase 0, Gate 1, Gate 2를 가볍게 묶고 핵심 가설 검증에 집중 | 낮음~중간 |

## 4. Profile별 운영 기준

Profile Overlay는 다음 필드를 기준으로 정의한다.

| Overlay 필드 | 의미 |
| --- | --- |
| `gate_approval` | 사용자의 명시 승인 지점과 Gate 자동 진행 금지 수준 |
| `required_artifacts` | Gate별 필수 산출물 범위 |
| `traceability_level` | ID 연결과 추적표 정합성 요구 수준 |
| `program_contract_level` | Program Design, interface, public method 계약의 상세도 |
| `security_standard_level` | 보안 기준선과 외부 표준 매핑 강도 |
| `data_standard_level` | 프로젝트 단어사전, 데이터 도메인, 외부 데이터 표준 적용 강도 |
| `qa_evidence_level` | 테스트 로그, 화면 캡처, Playwright, QA Finding 증적 수준 |
| `independent_review_level` | 독립 검수 또는 교차 검증을 요구하는 시점 |
| `run_preflight_strictness` | Run 입력 계약 사전 차단/경고 기준 |
| `release_control` | 릴리즈 승인, backlog, CR, release note 관리 수준 |

Profile은 결과물의 품질 등급이 아니다.
모든 Profile은 정상 동작, 검증 가능한 테스트, 실패/미실행의 정직한 기록을 요구한다.
차이는 문서 깊이, 증적 밀도, 독립검수 빈도, 변경관리 형식이다.

Profile별 기본 Overlay는 다음과 같다.

| Profile | `gate_approval` | `traceability_level` | `program_contract_level` | `security_standard_level` | `data_standard_level` | `qa_evidence_level` | `independent_review_level` | `run_preflight_strictness` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `audit` | 모든 Gate 명시 승인 | 전체 REQ/AC/FUNC/SCR/PGM/API/DB/SEC/UT/IT/UI | class/interface/public method 수준 | KISA/공공/고객사 기준 + OWASP/CWE | 공공데이터 공통표준 + 프로젝트 단어사전 | QA-000~QA-003, 명령 로그, UI 증적, FIND/CR | Gate 2, Gate 4, 필요 시 PR | 강한 차단 중심 |
| `product` | 주요 Gate와 릴리즈 승인 | 핵심 요구사항, API, DB, 보안, 회귀 테스트 | public API, service/usecase, DTO 수준 | OWASP ASVS/Top 10/API Top 10 + CWE | 프로젝트 단어사전 + ISO 11179식 metadata 요소 + 필요 시 공공표준 참고 | 릴리즈 회귀, 주요 UI/API 증적, 공식 UI runner 기본 | release candidate 또는 큰 변경 | scope/contract 차단, 나머지 경고 |
| `poc` | 시작/중간 점검/종료 승인 | 가설/요구사항 -> 구현 -> 결과 | 주요 인터페이스와 실험 코드 진입점 | 주요 보안 위험 식별과 제품화 전환 gap | 핵심 데이터 항목과 민감정보 식별 | smoke, 데모 캡처, 결과 로그, 필요 시 경량 UI script | 선택 | 경고 중심 |

`--trace-seed`는 모든 Profile에서 사용할 수 있다.
다만 `audit`에서는 대표 상세 ID를 기준으로 Run 입력 계약을 보강하는 것을 기본값으로 보고, `product`, `poc`에서는 필요한 경우 관련 ID 추천과 source document 축소 목적으로 사용한다.
PoC Profile에서는 `--trace-depth`가 명시되지 않으면 depth 1을 기본값으로 사용한다. 사용자가 더 넓은 영향 분석이 필요하다고 판단하면 `--trace-depth 2` 이상을 명시한다.

### 4.1 Audit Profile

공공/SI/감리 대응 프로젝트에 사용한다.

- Phase 0부터 Gate 5까지 모든 Gate를 명시적으로 운영한다.
- 요구사항정의서, 추적표, 기능명세, 프로그램 설계, 화면설계, DB명세, 보안가이드, 개발표준, 테스트케이스, 테스트결과, QA Finding, 변경요청, 릴리즈 승인서를 관리한다.
- 보안 기준은 KISA/SR, OWASP, CWE를 근거로 연결한다.
- 데이터 설계는 공공데이터 공통표준과 프로젝트 단어사전을 확인한다.
- CR은 영향도 분석, 상세 변경요청서, 관련 Gate 진행, Run 기록을 남긴다.
- 자동화 테스트는 원칙적으로 전체 실행하고, 통합/API/UI 테스트는 영향 범위를 중심으로 증적을 남긴다.
- Build Wave Run은 가능한 한 `wave-start --trace-seed <상세 ID>`로 생성하고, worker 실행 전 `scope.writable`, `interface_contract`, `contract_skeleton`, 검증 명령을 확정한다.
- Gate 4 QA는 QA-000 환경 준비, QA-001 명령 기반 검증, QA-002 UI/E2E 증적, QA-003 결과 정리와 판정 후보로 나누어 수행한다.
- Gate 4 공식 UI Pass는 `@playwright/test` runner, `npx playwright test`, HTML report/trace/screenshot 증적을 기준으로 한다. 커스텀 Playwright script는 보조 관찰로만 남긴다.

### 4.2 Product Profile

상용 제품, 사내 업무 앱, 반복 릴리즈가 필요한 제품형 개발에 사용한다.

- 문서의 목적은 감리 제출보다 제품 의사결정, 품질 유지, 릴리즈 추적에 둔다.
- 요구사항은 제품 백로그, 사용자 시나리오, 릴리즈 범위와 연결한다.
- 설계 문서는 SW Architecture, ADR, API/DB 계약, 보안/개발표준 중심으로 유지한다.
- 보안 기준은 KISA/공공 제출 근거가 아니라 OWASP ASVS, OWASP Top 10, OWASP API Security Top 10, CWE를 기본 기준선으로 사용한다.
- 설계자가 우선 읽을 기준선은 `docs/core/PRODUCT_PROFILE_BASELINE.md`, `docs/core/SECURITY_BASELINE.md`, `docs/core/DATA_STANDARD_RULES.md`다.
- ADR은 중요한 제품/아키텍처 의사결정이 있을 때 작성한다. 아직 결정이 없다면 `docs/product/ADR_LOG.md`에 `ADR-NONE` 행을 유지하고, `ADR-001 | TBD` 같은 placeholder 행은 남기지 않는다.
- KISA, 공공, 고객사 보안 기준은 Product에서 선택 참고로 둘 수 있으며, Audit 전환 시 공식 매핑과 증적으로 보강한다.
- 데이터 표준은 프로젝트 단어사전, 화면/API/DB 항목 매핑, 데이터 도메인, 개인정보/인증정보/민감정보 분류를 기본으로 한다.
- 공공데이터 공통표준은 공공/SI/Audit에서는 우선 검토 대상이지만, Product에서는 조직/도메인 표준이 없을 때 참고 표준으로 사용할 수 있다.
- 화면설계와 증적은 주요 사용자 흐름과 회귀 테스트 기준에 집중한다.
- 변경관리는 CR보다 Issue, Feature, Release Note, ADR과 연결될 수 있다.
- Gate는 유지하되 승인 절차를 가볍게 운영할 수 있다.
- Program Design은 모든 private method까지 요구하지 않고 public API, service/usecase, DTO, persistence adapter 경계를 중심으로 작성한다.
- QA는 릴리즈 후보 기준의 회귀 테스트, 주요 화면/API 증적, release note와 backlog 연결을 우선한다.
- UI Pass는 기본적으로 `@playwright/test` runner 증적을 사용한다. 단, 프로젝트가 UI 자동화 대상이 아니거나 환경 차단이 승인되면 `Not Run`, `Skipped`, `environment_blocked`로 정직하게 기록한다.
- Product 구현 Run은 `wave-start --trace-seed SCN-001`처럼 Product Scenario ID를 seed로 만들 수 있다. 이때 Run은 `docs/product/` 문서 세트를 기준으로 `SCN -> REQ/API/DATA/UI/REG` 연결을 추천하고, audit용 `docs/artifacts/` 산출물을 worker 입력 문서로 끌고 오지 않는다.
- Product Gate 5의 `release-pr --dry-run`은 Product 원장 문서와 Gate 5 승인서를 evidence 기준으로 삼는다. audit용 QA Finding/Test Result/Traceability Matrix가 없다는 이유만으로 Product release candidate를 누락으로 표시하지 않는다.

### 4.3 PoC Profile

기술 검증, 고객 데모, 기능 가설 확인에 사용한다.

- Phase 0, Gate 1, Gate 2를 짧게 묶어 목표, 가설, 성공 기준, 주요 제약을 먼저 정한다.
- 모든 산출물을 완성하려고 하지 않고 핵심 요구사항, 핵심 설계, 핵심 테스트만 작성한다.
- PoC profile의 기본 산출물 세트는 `docs/poc/POC_REQUIREMENTS.md`, `docs/poc/POC_SYSTEM_DESIGN.md`, `docs/poc/POC_TEST_REPORT.md` 3종이다.
- 새 PoC 프로젝트는 이 3종을 공식 작업 문서로 생성한다. Audit 산출물 템플릿 파일은 기본 생성하지 않으며, 필요 시 Product/Audit 승격 후보로 만든다.
- 이 3종 산출물은 audit 문서를 대체하는 최종 제출본이 아니라, 가설-설계-검증-판단과 반복별 기능 변화를 연결하는 PoC 원장이다.
- 추적성은 최소한 `가설/요구사항 -> 구현 -> 검증 결과`를 연결하는 수준으로 유지한다.
- 보안/데이터/운영 기준은 실제 배포가 아니라 위험 식별과 향후 전환 조건 중심으로 작성한다.
- PoC 결과가 제품화 또는 SI 프로젝트로 전환되면 Audit 또는 Product Profile로 승격한다.
- PoC에서 `gate-start`는 Gate 상태만 갱신하고 Orchestrator Plan Run을 자동 생성하지 않는다. Gate별 계획은 `docs/poc` 3종과 `status --check` 결과로 충분하면 생략한다.
- Run 문서는 기본 필수 산출물이 아니다. 외부 worker 실행, 독립 검수, 긴 작업 위임, 재현 가능한 실험 기록이 필요한 경우에만 compact Run을 만든다.
- PoC 구현은 메인 Orchestrator가 직접 독주하지 않고 subagent 또는 worker를 우선 사용한다. 다만 외부 CLI worker와 worktree를 반드시 요구하지는 않는다.
- PoC 구현은 `BW-000 implementation-scaffold`를 기본 생성하지 않는다. 첫 구현 worker가 환경 생성, hello/build smoke, 핵심 기능 구현을 함께 수행할 수 있다. 단, Impl worker의 완료 조건은 `코드 + dependency manifest + 빠른 self-check`로 제한한다.
- 개발환경 준비는 모든 Profile에서 Environment Readiness Track으로 앞당길 수 있다. 이 Track은 Phase 0~Gate 3 동안 병렬로 폴더 구조, dependency, lint/build/test script, hello world/health check, build smoke를 준비하되 업무 요구사항 구현과 Pass 확정은 하지 않는다.
- PoC Build worker는 `app/`, `static/`, `tests/`, `requirements.txt` 같은 구현 파일과 빠른 self-check에 집중한다. `README.md`, `POC_TEST_REPORT.md` 최종화, browser smoke/screenshot, release/backlog, 증적 로그 정규화는 Gate 4/5 또는 별도 Evidence/Normalization worker로 분리한다.
- 이미 진행 중인 Build worker가 코드 구현을 끝낸 뒤 Run 경고 제거, screenshot, README, 결과서 정리에 오래 머물면 Orchestrator가 해당 정리 작업을 회수하고, worker는 구현 변경과 self-check 결과만 보고하게 한다.
- 실패한 실험은 구현 결함으로 숨기지 않고 검증 결과, 환경 차단, 다음 판단 항목으로 기록할 수 있다.
- subagent/thread 실험이 의미 있는 코드/문서 변경을 만들었으면 Run을 만들지 않더라도 결과 요약에 `delegation_records`와 같은 최소 항목을 남긴다. 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증 명령이 기준이다.
- 가능하면 `delegation_records`에 `started_at`, `completed_at`, `duration_seconds`, `heartbeat_count`, `status_probe_count`, `self_check`를 함께 남긴다. PoC 병목은 기능 정합성보다 worker 대기/검증 시간이 원인인 경우가 많다.
- 파일 변경 완료 후 최종 응답이 늦어지는지 보려면 `first_file_change_at`, `last_file_change_at`, `worker_final_response_at`, `final_response_lag_seconds`를 선택적으로 남긴다.
- Agy `Workspace: branch` 같은 native branch worker가 Run 문서를 직접 수정하지 못해도 실패로 보지 않는다. worker는 변경 파일, self-check, 요약을 반환하고, Orchestrator가 부모 workspace에서 Run 문서와 `delegation_records`를 정규화하는 흐름을 기본값으로 둔다.
- worker/subagent 실행은 실험 범위를 분리하고 반복 기록을 남기기 위해 허용하되, 산출물 제출 품질보다 재현 가능한 명령과 결과 로그를 우선한다.
- PoC worker는 비차단 경고를 모두 제거하려고 반복하지 않는다. 구현 테스트와 `run-check`가 통과하고 `run-preflight`가 경고만 남긴 상태라면, 경고 내용과 후속 판단자를 기록한 뒤 Orchestrator에게 반환한다.
- UI 검증은 빠른 커스텀 Playwright script나 데모 캡처를 Gate 4 smoke/demo로 사용할 수 있다. Impl worker의 완료 조건은 HTTP/API smoke 또는 빠른 단위 테스트까지만 두고, 브라우저 screenshot은 Gate 4에서 판단한다. PoC 결과를 audit/product로 승격할 때는 `@playwright/test` 기반 공식 UI 증적으로 보강한다.
- PoC 정합성 평가는 "설계와 100% 일치" 같은 audit식 단정 대신 "PoC 목표 검증에 충분히 일치"와 "product/audit 승격 시 보강할 gap"을 함께 기록한다.
- Run 입력 문서는 `POC-RUN-COMPACT-STRATEGY.md` 기준으로 compact하게 생성한다. `AGENT_RUN_PROTOCOL`, `RUN_INPUT_CONTRACT`, `RUN_OUTPUT_CONTRACT`, Traceability Matrix 같은 오케스트레이터용 문서는 worker Run에 반복 삽입하지 않는다.
- `source_documents.reference_on_demand`는 trace-context 직접 관련 문서 중심으로 제한하며, 기본 후보 수는 5개 이내로 둔다.
- `TBD`, `확정필요`, `미정`은 PoC에서 허용한다. 단, 목표, 성공 기준, 실제 실행 결과는 `TBD`로 둘 수 없다.
- `TBD`가 남는 항목은 반드시 사유와 후속 판단 시점을 함께 남긴다. 예: `TBD: 배포 방식은 PoC 범위 밖. 제품화 전환 판단 시 결정`.
- `check-trace`, `run-check`, `run-preflight`는 PoC에서 상세 추적 누락, 미실행, 환경 차단, 사유 있는 TBD를 차단 이슈보다 경고/판단 항목으로 우선 분류한다. 제품 실패(`Fail`), 실제 실행 결과 허위 보고, scope 위반, 깨진 테스트는 계속 차단한다.
- `status --check`의 산출물 완성도 검사는 PoC에서 `docs/poc/` 3종을 기준으로 한다. Gate 전환 필수 요구사항도 profile별 필수 PoC 문서 존재 여부를 우선 본다.

## 5. Profile 선택 기준

| 질문 | 예라면 |
| --- | --- |
| 외부 감리, 고객 검수, 공식 산출물 제출이 필요한가? | `Audit Profile` |
| 일반 제품/업무 앱 개발이며 품질은 유지하되 감리 수준 산출물 밀도는 줄이고 싶은가? | `Product Profile` |
| 반복 릴리즈와 제품 로드맵, 품질 기준이 중요한가? | `Product Profile` |
| 핵심 가설이나 기술 가능성을 실험으로 확인하려는가? | `PoC Profile` |

## 6. 도구 적용 기준

`0.4.x` 기준 새 프로젝트의 기본 Profile은 `audit`이다.

`vulcan.py init`은 `session.json.profile`, `vulcan.config.json.delivery_profile`, `vulcan.config.json.profile_rules`에 선택한 Profile과 Overlay 기준을 기록한다.
대화형 터미널에서 Profile을 지정하지 않으면 `audit`, `product`, `poc` 중 하나를 선택할 수 있다.
기존 문서와 명령어 호환을 위해 `solution`은 `product`의 alias로 입력만 허용한다.
비대화형 자동화에서는 기존 호환성을 위해 `audit`으로 초기화한다.

사용 예:

```powershell
python vulcan.py init ../my-project "My Project" --profile audit
python vulcan.py init ../my-product "My Product" --profile product
python vulcan.py init ../my-poc "My PoC" --profile poc
```

현재 구현 상태는 다음과 같다.

| 항목 | 현재 상태 |
| --- | --- |
| `audit` | 기본 Profile이며 가장 강하게 문서화/검증된다. |
| `product` | `init --profile product`으로 선택할 수 있고, `docs/product/` 6종 산출물과 Product Overlay가 생성된다. |
| `poc` | `init --profile poc`으로 선택할 수 있고, `docs/poc/` 3종 산출물과 가설 검증 중심의 얇은 Run 입력 계약을 생성한다. |
| `profile-status` | 현재 Profile, config Profile, 적용 Profile Rules를 출력한다. |
| `profile-gap` | 현재 산출물을 목표 Profile 기준으로 볼 때 부족한 항목을 읽기 전용으로 진단한다. |
| `profile_rules` | `vulcan.config.json`에 명시적으로 기록되는 Profile Overlay 기준이다. PoC는 일부 추적성/placeholder 검사를 경고 중심으로 조정한다. |

예상 설정 예:

```json
{
  "delivery_profile": "product",
  "profile_rules": {
    "gate_approval": "major-gates",
    "traceability_level": "core",
    "program_contract_level": "public-api-and-service",
    "security_standard_level": "owasp-asvs-top10-api-top10-cwe",
    "data_standard_level": "project-glossary-field-domain-security-classification",
    "qa_evidence_level": "release-regression",
    "independent_review_level": "release-candidate",
    "run_preflight_strictness": "contract-and-scope"
  }
}
```

구현 순서는 다음을 원칙으로 한다.

1. Profile별 의미와 Overlay 기준을 문서로 먼저 고정한다.
2. `vulcan.config.json` 또는 `session.json`에 선택된 Profile과 `profile_rules` 기본값을 기록한다. (완료)
3. `profile-status`로 현재 Profile과 Overlay를 확인한다. (완료)
3-1. `profile-gap --to product|audit`로 profile 전환 전 부족 항목을 읽기 전용으로 확인한다. (파일 존재 + 내용 보완 요약 1차 완료)
4. PoC Profile의 Run 입력 계약은 가설, 성공 기준, smoke/demo 검증, 제품화 전환 보강 항목 중심으로 얇게 생성한다. (완료)
5. `run-check`, `run-preflight`의 차단/경고 심각도를 Profile별로 조절한다. (PoC TBD 경고화 1차 완료)
6. `check-trace`의 누락/OPEN/Planned 판단을 Profile별 엄격도로 조절한다. (PoC 3종 산출물 원장 기반 1차 완료)
7. Dashboard에 Profile badge와 Product 필수 산출물 범위를 표시한다. (Product 문서 세트 표시 1차 완료)
8. `product`, `poc`용 fixture smoke를 추가해 audit 규칙이 과하게 적용되지 않는지 검증한다.

Product Profile의 기본 산출물 세트는 다음 6종이다.

```text
docs/product/PRODUCT_BRIEF.md
docs/product/PRODUCT_ARCHITECTURE.md
docs/product/ADR_LOG.md
docs/product/PRODUCT_CONTRACTS.md
docs/product/PRODUCT_TRACEABILITY.md
docs/product/REGRESSION_AND_RELEASE_REPORT.md
```

이 문서들은 Gate별 제출 폴더가 아니라 제품 운영 문서 세트다.
각 문서의 `gate_scope`와 본문 섹션이 Gate 1~5 역할에 대응한다.
`profile-gap`은 Product 문서 세트의 존재 여부와 현재 Gate의 핵심 내용 보완 필요 여부를 분리해 보여준다.
예를 들어 `PRODUCT_BRIEF.md`의 목표, 주요 사용자, 성공 기준이 `TBD`이면 Phase 0 완료 전 `status --check`에서 차단된다.
Product Profile에서는 Gate 시작 시 Orchestrator Plan Run을 자동 생성하지 않는다.
Gate 계획과 판단은 `docs/product/` 문서와 `status --check`를 우선 사용하고, 구현/검수 위임이나 재현 가능한 작업 기록이 필요할 때만 Run을 만든다.

`run-new`는 Profile과 Gate, skill 조합을 보고 가능한 경우 Run 입력 계약을 자동 확장한다.

PoC Profile에서는 Phase 0부터 Gate 5까지 다음 원칙으로 Run 입력 계약을 생성한다.

- `read_first`는 `AGENTS.md`, `session.json`, `DELIVERY_PROFILES.md`, 현재 skill 카드 중심으로 제한한다.
- `working_documents`는 현재 Run 문서와 해당 Gate의 핵심 산출물 폴더를 중심으로 둔다.
- `reference_on_demand`는 이전 Gate 산출물 또는 Core 규칙 확인이 필요할 때만 읽는다.
- 완료 기준은 "문서 완성"보다 목표/가설/성공 기준, smoke/demo 결과, 실패/미실행의 정직한 기록, 제품화 또는 audit 전환 보강 항목을 우선한다.
- PoC에서 실패한 실험은 구현 결함으로 숨기지 않고 검증 결과 또는 다음 판단 항목으로 기록한다.
- PoC 회고나 성능 비교가 필요하면 `python vulcan.py metrics`를 먼저 실행해 git timeline, 파일/라인 수, Run/위임 기록 수를 확인한다. 사람이 작성한 회고 문서의 소요 시간이나 라인 수가 `metrics`와 다르면 `metrics` 기준을 우선하고, 다른 기준을 썼다면 시작/종료 범위를 명시한다.

모든 Profile에서 Impl 단계의 `check-trace`는 Gate 3 테스트케이스의 `Planned`/미실행 항목을 Gate 4 실행 대기 항목으로 취급한다.
실제 Pass/Fail/Not Run 판정은 Gate 4 QA 결과서와 증적으로 확정한다.

PoC 시작 예:

```powershell
python vulcan.py init ../my-poc "My PoC" --profile poc
cd ../my-poc
python vulcan.py profile-status
# docs/poc/POC_REQUIREMENTS.md에 목표, 가설, 성공 기준을 먼저 채운다.
python vulcan.py status --check
```

PoC 산출물 세트와 승격 전략은 `docs/reference/POC-PROFILE-TEMPLATE-SET-STRATEGY.md`와 `docs/reference/POC-PRODUCT-LIFECYCLE-INTEGRATION-DESIGN-AGY.md`를 참고한다.
PoC 실험 기록과 Environment Readiness Track 기준은 `docs/reference/FAST-POC-AND-ENV-RUNWAY-STRATEGY.md`를 참고한다.
Profile 전환은 무거운 승격 프로세스가 아니라 `docs/core/PROFILE_GAP_CHECK.md`의 gap 진단을 먼저 따른다.

Audit Profile에서는 Phase 0부터 Gate 5까지 빈 Run 껍데기를 만들지 않고 다음 항목을 포함한다.

- 먼저 읽을 최소 문서, 실제 작업 산출물, 필요 시 참고 문서의 분리
- 수정 가능 경로, 읽기 전용 경로, 제외 경로
- 감리 대응 완료 기준
- 실제 검증 명령
- 출력 계약과 질문 정책
- Gate 종료 후 사용자 승인 대기 정책
- UI 테스트와 화면 증적의 상태/시나리오별 1:1 매칭 정책

기본 preset 범위:

| Gate | 기본 Run 초점 |
| --- | --- |
| `phase0` | 프로젝트 목적, 범위, 이해관계자, As-Is/To-Be, 리스크/가정 |
| `gate1` | REQ/NREQ/AC와 추적표 초기 연결 |
| `gate2` | 설계 산출물, 보안, 데이터, 화면, 개발표준 연결 및 Gate 2 설계 순서 관리 |
| `gate3` | AC/SEC/NREQ를 UT/IT/UI/PT 테스트 기준으로 전개 |
| `impl` | 승인된 설계/테스트 범위 안의 Build Wave 계획과 실행 |
| `gate4` | 테스트 결과, 화면/로그 증적, QA Finding, fix-loop |
| `gate5` | 릴리즈 승인, 미해결 FIND/CR, 잔여 리스크, 인수인계 |

Audit Profile에서는 각 Gate 완료 후 다음 Gate로 자동 진행하지 않는다.
Run은 산출물 요약, 미해결 항목, 다음 Gate 제안, 사용자 승인 질문을 남기고 멈춘다.
대화상 명시 승인 없이 승인 완료로 기록하지 않는다.

UI 테스트는 `UI-001`처럼 화면 하나로 크게 Pass 처리하지 않고 `UI-001-01`처럼 상태/시나리오 단위로 나눈다.
예를 들어 회원가입은 기본 화면, 약한 비밀번호 오류, 비밀번호 확인 불일치, 중복 이메일, 성공 메시지, 로그인 연계를 별도 테스트와 별도 캡처로 연결한다.

Run의 `source_documents`는 다음처럼 해석한다.

| 구분 | 의미 |
| --- | --- |
| `read_first` | 작업 시작 전에 먼저 읽는 최소 문서 |
| `working_documents` | 이번 Run에서 실제로 작성하거나 검토할 산출물 |
| `reference_on_demand` | 기준 충돌, 작성 규칙 확인, 상세 판단이 필요할 때만 참고하는 문서 |

Core 문서, Template, 샘플 입력 문서는 원칙적으로 `reference_on_demand`에 둔다.
에이전트는 `working_documents`를 중심으로 작업한다.
다만 Audit Profile의 Gate 2 Run은 설계 순서를 놓치지 않도록 `docs/core/GATE2_DESIGN_SEQUENCE.md`를 `read_first`에 포함한다.
Gate 2 Run 출력에는 현재 순서 위치, 누락된 이전 단계, 다음 Gate 2 Run 후보가 남아야 한다.

예:

```powershell
python vulcan.py run-new --gate phase0 --skill orchestrator-plan --title "Phase 0 Discovery" --related-ids RUN-001
python vulcan.py run-new --gate gate1 --skill traceability-review --title "요구사항 추적성 검토" --related-ids REQ-001,AC-001
python vulcan.py run-new --gate gate2 --skill data-standard-review --title "프로젝트 단어사전 검토" --related-ids DB-001,API-001,SCR-001
python vulcan.py run-new --gate gate2 --skill development-standard-review --title "개발표준 검토" --related-ids NREQ-001,SEC-001,PGM-001
python vulcan.py run-new --gate gate3 --skill traceability-review --title "테스트케이스 전개 검토" --related-ids AC-001,UT-001,IT-001
python vulcan.py run-new --gate impl --skill implementation-plan --title "Build Wave 계획" --related-ids REQ-001,PGM-001,UT-001
python vulcan.py run-new --gate gate4 --skill qa-execution --title "QA-000 Gate 4 환경 준비 및 smoke" --related-ids NREQ-002,IT-BUILD-001
python vulcan.py run-new --gate gate4 --skill qa-execution --title "QA-001 Gate 4 명령 기반 검증" --related-ids UT-001,IT-001,NREQ-001,NREQ-002
python vulcan.py run-new --gate gate4 --skill qa-execution --title "QA-002 Gate 4 UI/E2E 증적 수집" --related-ids UI-001,UI-002
python vulcan.py run-new --gate gate4 --skill qa-execution --title "QA-003 Gate 4 결과 정리 및 판정 후보" --related-ids RV-TEST-001,NREQ-001,NREQ-002
python vulcan.py run-new --gate gate4 --skill qa-fix-loop --title "QA 결함 수정 루프" --related-ids FIND-001,UI-001
python vulcan.py run-new --gate gate5 --skill traceability-review --title "릴리즈 승인 검토" --related-ids REQ-001,RUN-001,CR-001
```

향후 `check-trace`, Dashboard, template 생성 범위, Gate 완료 기준은 위 Overlay 필드에 맞춰 Profile별로 세분화한다.
Profile별 구현은 Core 규칙을 복제하지 않고, 하나의 검사기와 하나의 Run 입력 계약이 선택된 Profile의 엄격도를 참조하도록 확장한다.
