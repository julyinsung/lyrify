# Gate 2 Design Review Run Input Sample

> 목적: Audit Profile에서 설계 산출물이 구현과 테스트로 넘어갈 수 있는지 검토하는 공통 기준 예시다.

```yaml
profile: "audit"
run_type: "Design"
gate: "gate2"
skill: "traceability-review"
persona: "review"
related_ids: [REQ-001, FUNC-001, SCR-001, PGM-001, DB-001, SEC-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/core/GATE2_DESIGN_SEQUENCE.md
    - docs/adapters/codex-gpt/skills/traceability-review.md
  working_documents:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md
    - docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
  reference_on_demand:
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
    - docs/artifacts/02-design/
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
completion_criteria:
  - "REQ/AC가 FUNC, SCR, PGM, API, DB, SEC 설계 ID로 전개되어 있다."
  - "설계 산출물 간 화면, API, 프로그램, 데이터, 보안 연결이 모순되지 않는다."
  - "Gate 2 산출 순서와 현재 Run 위치가 Run 기록에 남아 있다."
  - "SW 아키텍처 Draft/Baseline Candidate/Baseline 성숙도와 Pending/ADR 상태가 기록되어 있다."
  - "화면 퍼블리싱 산출물 또는 외부 시안이 있으면 UI Implementation Contract로 기준 파일, 필수 유지, 변경 허용/금지, 비교 방식을 확정한다."
  - "개발표준과 아키텍처 기준이 구현자가 사용할 수 있을 만큼 구체적이다."
  - "Gate 3 테스트 설계에 넘길 검증 후보가 식별되어 있다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
ui_implementation_contract_policy:
  required_when: "UIREF, 화면 퍼블리싱 산출물, Figma, 이미지 시안, 기존 화면 캡처가 있는 경우"
  gate2_required_fields:
    - 기준 파일 또는 URL
    - 기준 CSS 또는 디자인 토큰
    - 필수 유지 요소
    - 변경 허용 항목
    - 변경 금지 항목
    - 구현 비교 방식
    - 차이 발생 시 FIND/CR 판정 기준
```

## Review Notes

- Gate 2에서는 구현 코드를 만들지 않는다. 구현이 필요하면 Gate 3와 구현 승인 이후 Build Wave로 넘긴다.
- SW 아키텍처는 Gate 2의 첫 Draft이자 마지막 Baseline 검토판이다.
- 화면 퍼블리싱 산출물이 있으면 `참고자료`인지 `구현 기준`인지 먼저 판정하고, 구현 기준이면 UI Implementation Contract로 승격한다.
- Run 종료 시 현재 Gate 2 순서 위치, 누락된 이전 단계, 다음 Gate 2 Run 후보를 남긴다.
- Gate 3 테스트 설계로 넘어가기 전 설계 산출물 요약과 승인 질문을 남긴다.

