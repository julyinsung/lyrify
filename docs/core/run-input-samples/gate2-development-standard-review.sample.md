# Gate 2 Development Standard Review Run Input Sample

> 목적: Audit Profile에서 개발표준 검토 Run이 최소한으로 받아야 하는 입력 계약 예시다.
> 이 문서는 샘플 애플리케이션 산출물이 아니라, 에이전트가 매번 같은 기준으로 작업하도록 하는 Run 입력 예시다.

```yaml
profile: "audit"
run_type: "Design"
gate: "gate2"
skill: "development-standard-review"
persona: "development-review"
related_ids: [NREQ-001, SEC-001, PGM-001, UT-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/core/GATE2_DESIGN_SEQUENCE.md
    - docs/adapters/codex-gpt/skills/development-standard-review.md
  working_documents:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  reference_on_demand:
    - docs/core/TECH_STACK_BASELINES.md
    - docs/core/SECURITY_BASELINE.md
    - docs/templates/DEVELOPMENT_STANDARD_TEMPLATE.md
    - docs/core/ID_SYSTEM.md
    - docs/core/ORCHESTRATOR_PROTOCOL.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/DELIVERY_PROFILES.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/core/RUN_OUTPUT_CONTRACT.md
design_sequence:
  - "G2-01 Kickoff / 설계 범위 고정"
  - "G2-02 SW Architecture Draft"
  - "G2-03 Screen / User Flow"
  - "G2-04 Function Spec"
  - "G2-05 Program Design / API Spec"
  - "G2-06 Data / DB Spec"
  - "G2-07 Security Guide"
  - "G2-08 Development Standard"
  - "G2-09 SW Architecture Baseline 보강"
  - "G2-10 Design Review / Gate 3 승인 대기"
scope:
  writable:
    - docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
  readonly:
    - docs/core/
    - docs/templates/
    - docs/seed-docs/reference-standards/
  excluded:
    - docs/ref-docs/
completion_criteria:
  - "언어, 런타임, 프레임워크, DB, 빌드, 테스트 도구와 선택 근거가 작성되어 있다."
  - "TECH_STACK_BASELINES.md 중 어떤 기준을 준용하고 어떤 점을 프로젝트에 맞게 조정했는지 기록되어 있다."
  - "패키지 구조, 계층 책임, 금지 의존성, DTO/Entity 분리, 트랜잭션 기준이 구현자가 따를 수 있을 만큼 구체적이다."
  - "Spring Boot라면 base package 아래 auth/user/{feature}/security/common 구조 또는 domain 래퍼 선택 사유가 명확하다."
  - "DB pool은 HikariCP 기본 또는 대체 pool 선택 사유, 설정 위치, 검증 방법이 작성되어 있다."
  - "Lombok 사용 여부, 허용 annotation, Entity 금지 annotation이 작성되어 있다."
  - "메시지, 예외, 로그, 설정값, 외부 의존성, 주석/추적 ID 표기 규칙이 있다."
  - "로깅은 SLF4J, Logback/Log4j2 선택, Log4j 1.x 금지, logger 선언, 로그 레벨, MDC/requestId, 민감정보 금지 기준이 있다."
  - "Java/Spring 주석 기준은 클래스/메서드 JavaDoc 대상과 실제 예시를 포함한다."
  - "필수 검증 명령은 실행 위치(cwd), Windows/POSIX 명령, 성공 기준, 로그/증적 경로, Not Run/Skipped 처리 기준을 가진다."
  - "Frontend가 있으면 npm ci/npm install 선택 기준과 frontend 테스트/린트/빌드 명령이 명확하다."
  - "통합 배포가 필요하면 backend 단독 빌드와 frontend 포함 통합 빌드 명령 및 성공 기준이 구분되어 있다."
  - "보안 구현 기준이 SECURITY_BASELINE과 SEC-ID에 연결되어 있다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
verification:
  commands:
    - "python vulcan.py run-check <run-file>"
    - "python vulcan.py check-trace"
```

## Review Notes

- 단순히 "Python 사용"처럼 선택만 적는 것은 부족하다. 왜 그 스택을 쓰는지, 어떤 기준선을 따르는지, 구현자가 지켜야 할 구조와 검증 명령이 있어야 한다.
- 검증 명령은 명령 문자열만으로 충분하지 않다. 실행 위치, 성공 기준, exit code, 로그/증적 위치, 미실행 판정 기준까지 있어야 Gate 4에서 에이전트별 해석 차이를 줄일 수 있다.
- 감리 대응 프로젝트에서는 개발표준이 아키텍처, 프로그램 설계, 보안가이드, 테스트케이스로 이어져야 한다.
- 개발표준 검토는 권장 순서상 G2-08이므로, 아키텍처/프로그램/API/보안 설계가 부족하면 먼저 보완 Run을 제안한다.
- Gate 3로 넘어가기 전 개발표준 보완 결과와 승인 질문을 남긴다.

