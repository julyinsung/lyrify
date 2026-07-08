# Gate 5 Release Approval Run Input Sample

> 목적: Audit Profile에서 릴리즈 승인, 잔여 리스크, 인수인계를 정리하는 기준 예시다.

```yaml
profile: "audit"
run_type: "Approval"
gate: "gate5"
skill: "traceability-review"
persona: "review"
related_ids: [REQ-001, RUN-001, CR-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/adapters/codex-gpt/skills/traceability-review.md
  working_documents:
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/artifacts/05-change/
    - docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md
  reference_on_demand:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md
    - docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md
    - docs/templates/RELEASE_APPROVAL_TEMPLATE.md
    - docs/templates/CHANGE_REQUEST_TEMPLATE.md
    - docs/core/ID_SYSTEM.md
    - docs/core/ORCHESTRATOR_PROTOCOL.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/DELIVERY_PROFILES.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md
    - docs/artifacts/05-change/
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
completion_criteria:
  - "릴리즈 범위, 제외 범위, 승인자, 잔여 리스크가 명확하다."
  - "미해결 FIND/CR/ISSUE의 처리 상태와 승인 조건이 기록되어 있다."
  - "요구사항, 테스트 결과, 증적, 릴리즈 승인서가 추적표로 연결되어 있다."
  - "인수인계와 운영/롤백 고려사항이 남아 있다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: false
  approval_evidence_required: true
```

## Review Notes

- `working_documents`에는 릴리즈 승인서, 변경요청, 추적표처럼 승인 판단 결과를 직접 작성/갱신할 문서만 둔다.
- Gate 5는 기능 추가 단계가 아니다. 승인 전 미해결 항목과 릴리즈 판단 근거를 고정한다.
- 릴리즈 승인 여부는 대화상 명시 승인 또는 보류 사유로 남긴다.
- audit workflow에서 구현/QA가 `workflow.integration_branch`에서 진행됐다면, Gate 5 승인 전 `python vulcan.py release-pr`로 통합 브랜치 -> 기준 브랜치 Release PR을 생성하거나 갱신한다.
- `release-pr --dry-run`은 `.vulcan/release/release-pr-body.md`에 PR body를 만들며, 현재 브랜치, base/head 브랜치, dirty worktree guard를 먼저 확인한다.
- Release PR은 릴리즈 후보 검토 단위이며 자동 merge가 아니다. PR 교차검증 결과도 merge 가능 후보일 뿐이고, merge는 사용자 명시 승인 또는 Gate 5 승인 절차 뒤에 수행한다.

