# Phase 0 Discovery Run Input Sample

> 목적: Audit Profile에서 Phase 0 Run이 프로젝트 방향과 질문을 정리할 때 사용할 입력 계약 예시다.

```yaml
profile: "audit"
run_type: "Discovery"
gate: "phase0"
skill: "orchestrator-plan"
persona: "documentation"
related_ids: [RUN-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/core/ORCHESTRATOR_PROTOCOL.md
  working_documents:
    - docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md
    - docs/artifacts/00-discovery/DOC-CORE-P0-002_Stakeholder-And-Scope_v0.1.md
    - docs/artifacts/00-discovery/DOC-CORE-P0-003_As-Is-To-Be_v0.1.md
    - docs/artifacts/00-discovery/DOC-CORE-P0-004_Risk-And-Assumption_v0.1.md
  reference_on_demand:
    - docs/core/DELIVERY_PROFILES.md
    - docs/templates/PROJECT_BRIEF_TEMPLATE.md
    - docs/templates/STAKEHOLDER_SCOPE_TEMPLATE.md
    - docs/templates/AS_IS_TO_BE_TEMPLATE.md
    - docs/templates/RISK_ASSUMPTION_TEMPLATE.md
    - docs/core/ID_SYSTEM.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - docs/artifacts/00-discovery/
    - docs/runs/
  excluded:
    - docs/ref-docs/
completion_criteria:
  - "프로젝트 목적, 사용자, 범위, 비목표가 실제 프로젝트 값으로 정리되어 있다."
  - "이해관계자와 승인자, 주요 제약, 참고문서 출처가 식별되어 있다."
  - "As-Is/To-Be와 주요 리스크/가정이 Gate 1 질문으로 이어진다."
  - "Phase 0에서 구현, 테스트 코드, 화면 증적을 만들지 않는다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
```

## Review Notes

- 첫 대화가 방향 확인 수준이면 컨시어지로 응답하고, 산출물 작성을 시작하기 전에 필요한 질문을 정리한다.
- 참고자료가 부족하면 임의로 요구사항을 확정하지 않는다.
- Phase 0 산출물을 요약하고 Gate 1로 진행해도 되는지 명시적으로 물은 뒤 대기한다.

