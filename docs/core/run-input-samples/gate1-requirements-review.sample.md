# Gate 1 Requirements Review Run Input Sample

> 목적: Audit Profile에서 요구사항과 인수기준을 추적 가능한 설계 입력으로 만드는 기준 예시다.

```yaml
profile: "audit"
run_type: "Requirements"
gate: "gate1"
skill: "traceability-review"
persona: "review"
related_ids: [REQ-001, AC-001, NREQ-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/adapters/codex-gpt/skills/traceability-review.md
  working_documents:
    - docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md
    - docs/artifacts/00-discovery/DOC-CORE-P0-002_Stakeholder-And-Scope_v0.1.md
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  reference_on_demand:
    - docs/templates/REQUIREMENTS_SPEC_TEMPLATE.md
    - docs/templates/TRACEABILITY_MATRIX_TEMPLATE.md
    - docs/core/ID_SYSTEM.md
    - docs/core/ORCHESTRATOR_PROTOCOL.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/DELIVERY_PROFILES.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
completion_criteria:
  - "REQ, NREQ, AC가 실제 기능/품질 요구로 작성되어 있다."
  - "각 요구사항에 출처, 우선순위, 승인 상태, 관련 리스크가 연결되어 있다."
  - "보안, 데이터, 화면, 인터페이스 후보가 Gate 2 설계 입력으로 넘어간다."
  - "요구사항과 인수기준이 추적표에 연결되어 있다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
```

## Review Notes

- 요구사항이 모호하면 구현으로 넘어가지 말고 질문 또는 `open_issues`로 남긴다.
- Gate 1 완료는 문서 상태값만이 아니라 추적표 연결과 사용자 승인으로 판단한다.
- Gate 2 설계로 넘어가기 전 요구사항/AC 요약과 승인 질문을 남긴다.

