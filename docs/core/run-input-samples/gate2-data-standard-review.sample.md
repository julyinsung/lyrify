# Gate 2 Data Standard Review Run Input Sample

> 목적: Audit Profile에서 데이터 표준 검토 Run이 최소한으로 받아야 하는 입력 계약 예시다.
> 이 문서는 샘플 애플리케이션 산출물이 아니라, 에이전트가 매번 같은 기준으로 작업하도록 하는 Run 입력 예시다.

```yaml
profile: "audit"
run_type: "Design"
gate: "gate2"
skill: "data-standard-review"
persona: "review"
related_ids: [DB-001, API-001, SCR-001, SEC-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/core/GATE2_DESIGN_SEQUENCE.md
    - docs/adapters/codex-gpt/skills/data-standard-review.md
  working_documents:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md
    - docs/artifacts/02-design/data/erd/logical/logical-erd.dbml
    - docs/artifacts/02-design/data/erd/physical/physical-erd.dbml
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  reference_on_demand:
    - docs/core/DATA_STANDARD_RULES.md
    - docs/core/REFERENCE_STANDARDS.md
    - docs/templates/PROJECT_GLOSSARY_TEMPLATE.md
    - docs/templates/DATABASE_SPEC_TEMPLATE.md
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
    - docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md
    - docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md
    - docs/artifacts/02-design/data/erd/logical/logical-erd.dbml
    - docs/artifacts/02-design/data/erd/physical/physical-erd.dbml
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
  readonly:
    - docs/core/
    - docs/templates/
    - docs/seed-docs/reference-standards/
  excluded:
    - docs/ref-docs/
completion_criteria:
  - "프로젝트 단어사전에 TERM, WORD, DOMAIN 섹션이 실제 프로젝트 값으로 채워져 있다."
  - "공공데이터 공통표준 또는 프로젝트 신규 용어 여부와 등록 사유가 기록되어 있다."
  - "화면 항목명, API 필드명, DB 컬럼명, DOMAIN-ID 매핑이 작성되어 있다."
  - "개인정보/인증정보/시스템정보 등 보안 분류와 관련 SEC-ID가 연결되어 있다."
  - "DB명세서와 논리/물리 DBML의 테이블, 컬럼, PK/FK, 코드 도메인이 일치한다."
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

- 참고문서가 부족하면 `Blocked` 또는 `open_issues`로 남기고, 빈 단어사전이나 DB명세를 완료로 처리하지 않는다.
- 감리 대응 프로젝트에서는 표준용어, 프로젝트 용어, 데이터 도메인, 보안 분류, 화면/API/DB 매핑을 함께 본다.
- 데이터 표준 검토는 권장 순서상 G2-06이므로, G2-03~G2-05 설계 입력이 부족하면 먼저 보완 Run을 제안한다.
- Gate 3로 넘어가기 전 데이터 표준 보완 결과와 승인 질문을 남긴다.

