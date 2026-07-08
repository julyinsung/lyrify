# Vulcan-Anvil Ex Core

이 디렉터리는 Vulcan-Anvil Ex의 모델 독립 Core 규칙을 정의한다.

`0.4.0` 기준 Core 문서:

- `ID_SYSTEM.md`: ID Prefix, 문서 ID, 파일명, 버전 규칙
- `TRACEABILITY_RULES.md`: 요구사항, 설계, 보안, 테스트, 증적 간 필수 연결 규칙
- `GATE_EXECUTION_CHECKLIST.md`: runner 공통 Gate 실행 체크리스트와 승인/위임 경계
- `ORCHESTRATOR_PROTOCOL.md`: 메인 에이전트의 계획, 위임, 검증, handoff 판단 규칙
- `ORCHESTRATOR_CLI_GUIDE.md`: Orchestrator가 우선 사용할 `status` 중심 CLI 표면과 원자 명령 사용 기준
- `DOCUMENT_METADATA.md`: 공식 문서에 공통으로 들어갈 메타데이터 필드
- `REFERENCE_STANDARDS.md`: 보안 가이드와 공공데이터 표준 참조 및 준용 규칙
- `SECURITY_BASELINE.md`: KISA/SR, OWASP, CWE를 연결한 보안 요구사항/설계/테스트 기준선
- `KISA_SECURITY_RULES.md`: KISA 개발보안 가이드의 반복 사용 항목을 설계/구현 규격 작성용으로 정리한 근거 기준표
- `DATA_STANDARD_RULES.md`: 프로젝트 단어사전, 용어, 도메인, 데이터 항목명 관리 규칙
- `AGENT_PERSONAS.md`: 단계별 에이전트 persona와 subagent 위임 규칙
- `AGENT_RUN_PROTOCOL.md`: Codex, GPT, Claude 등 에이전트 실행 단위와 Gate별 작업 계약
- `INDEPENDENT_EXECUTION_PROCESS.md`: 교차검증, PR 검증, Build Wave, Evidence Run을 별도 세션/worktree에서 실행하는 공통 모델
- `INDEPENDENT_REVIEW_PROCESS.md`: 별도 세션 또는 worktree 기반 독립 검수 절차
- `CODEX_MODEL_POLICY.md`: Codex runner의 역할별 model/effort 선택 정책과 실행 기록 기준
- `GATE2_DESIGN_SEQUENCE.md`: Gate 2 설계 산출 순서와 SW 아키텍처 반복 갱신 기준
- `CHANGE_CONTROL_PROCESS.md`: QA 발견사항, 변경요청, 백로그, 승인된 CR의 Gate 진행 프로세스
- `DELIVERY_PROFILES.md`: Audit, Product, PoC 프로젝트별 문서 깊이와 Gate 강도 조절 기준
- `TECH_STACK_BASELINES.md`: Spring Boot, Spring Security, React, Next.js, Vue.js, FastAPI 기술스택별 코딩/주석/테스트 기본 규칙
- `REFACTORING_PROCESS.md`: 리팩토링의 DEBT/FIND/CR 분류, 문서 영향 판단, 검증 기록 기준

관련 운영 참고 문서:

- `../reference/SUBMISSION-DOCUMENT-STRATEGY.md`: 작업용 Markdown 원천 문서와 제출용 DOCX/XLSX/HWPX 합본 문서의 생성 전략

이 문서들은 특정 프로젝트의 감리 문서관리 규칙보다 의도적으로 단순하게 유지한다. 프로젝트 Adapter는 고객사나 SI 프로젝트에 필요한 더 엄격한 규칙을 추가할 수 있지만, Core는 Claude, Codex, Cursor, Copilot, 사람의 작업 흐름 모두에서 사용할 수 있도록 이식성을 우선한다.

## 0.4.0 기준 핵심 변화

- Codex와 Claude adapter가 같은 Core 규칙을 공유하도록 persona, Run, Gate 지침을 정리했다.
- 구현 단계는 작은 Run과 Build Wave를 모두 허용하되, 중간 이상 작업은 Wave 단위로 작업지시/검증/상태 갱신을 남기도록 했다.
- audit workflow에서 `workflow.integration_branch`를 구현/QA 통합 브랜치 역할로 사용하고, 기본값 `dev`는 프로젝트별로 바꿀 수 있게 했다.
- Gate 4 QA를 `QA-000` 환경 준비, `QA-001` 명령 검증, `QA-002` UI/E2E 증적, `QA-003` 결과 정리로 나누고 같은 QA workspace를 재사용하도록 했다.
- 변경관리는 rollback 대신 승인된 CR의 필요한 Gate 진행과 Run 기록으로 처리한다.
- SW Architecture, DBML ERD, 보안가이드, 개발표준, 릴리즈 승인 산출물을 Gate 2~5 흐름에 연결했다.
- Gate 2에서 SW Architecture Draft로 시작해 상세 설계를 거쳐 Baseline으로 보강하는 설계 순서 기준을 추가했다.
- 기술스택 선택 시 개발표준정의서가 참조할 Spring Boot, Spring Security, React, Next.js, Vue.js, FastAPI 베이스라인을 추가했다.
- 리팩토링을 추적 가능한 개선 작업으로 다루기 위해 DEBT/FIND/CR 분기와 문서 영향 판단 기준을 정의했다.
- 작업용 Markdown 산출물과 제출용 DOCX/XLSX/HWPX 합본의 관계는 `../reference/SUBMISSION-DOCUMENT-STRATEGY.md`를 기준으로 한다.
- 감리 대응, 제품/업무 앱 개발, PoC를 같은 문서/증적 밀도로 다루지 않기 위해 Delivery Profile을 도입 방향으로 정의했다.
- Gate 2와 Gate 4에서 작성 세션과 분리된 독립 검수를 기본 권장 절차로 사용할 수 있도록 절차를 추가했다.
- 교차검증, PR 검증, Build Wave를 같은 독립 실행 모델로 다루기 위해 Independent Execution 개념을 추가했다.
