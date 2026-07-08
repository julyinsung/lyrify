# Gate 3 Test Design Run Input Sample

> 목적: Audit Profile에서 요구사항과 설계를 검증 가능한 테스트 계획으로 전개하는 기준 예시다.

```yaml
profile: "audit"
run_type: "Test"
gate: "gate3"
skill: "traceability-review"
persona: "review"
related_ids: [AC-001, SEC-001, UT-001, IT-001, UI-001]
source_documents:
  read_first:
    - AGENTS.md
    - session.json
    - docs/core/TRACEABILITY_RULES.md
    - docs/core/GATE_EXECUTION_CHECKLIST.md
    - docs/adapters/codex-gpt/skills/traceability-review.md
  working_documents:
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
  reference_on_demand:
    - docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md
    - docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md
    - docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md
    - docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md
    - docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md
    - docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md
    - docs/templates/TEST_CASE_TEMPLATE.md
    - docs/core/ID_SYSTEM.md
    - docs/core/ORCHESTRATOR_PROTOCOL.md
    - docs/core/AGENT_PERSONAS.md
    - docs/core/AGENT_RUN_PROTOCOL.md
    - docs/core/DELIVERY_PROFILES.md
    - docs/core/RUN_INPUT_CONTRACT.md
    - docs/core/RUN_OUTPUT_CONTRACT.md
scope:
  writable:
    - docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md
    - docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md
    - docs/runs/
completion_criteria:
  - "AC, SEC, NREQ가 UT, IT, UI, PT 후보로 전개되어 있다."
  - "요구사항정의서의 모든 상세 REQ-NNN-NN이 테스트케이스 문서의 상세 REQ별 테스트 매핑에 포함되어 있다."
  - "각 상세 REQ-NNN-NN은 하나 이상의 UT, IT, UI, PT 또는 승인된 검토 테스트와 연결되어 있다."
  - "각 테스트케이스에 입력, 절차, 기대결과, 증적 방식이 있다."
  - "명령 기반 테스트는 실행 위치(cwd), Windows/POSIX 명령, 성공 기준, 로그/증적 경로가 있다."
  - "UI 테스트는 화면 단위가 아니라 상태/시나리오 단위로 UI-001-01처럼 분리되어 있다."
  - "각 UI 테스트는 기대 화면과 캡처 증적 파일이 1:1로 연결되어 있다."
  - "화면 퍼블리싱 기반 화면은 UI Implementation Contract의 필수 유지/변경 허용/금지 항목을 테스트 기대결과에 반영한다."
  - "자동화 가능 테스트와 수동 검수 테스트가 구분되어 있다."
  - "구현 전에 필요한 테스트 데이터와 환경 제약이 식별되어 있다."
gate_exit_policy:
  stop_required: true
  next_gate_requires_user_approval: true
  approval_evidence_required: true
ui_evidence_policy:
  state_level_required: true
  id_pattern: "UI-001-01"
  examples:
    - "UI-001-01 회원가입 기본 화면"
    - "UI-001-02 약한 비밀번호 오류"
    - "UI-001-05 회원가입 성공 메시지"
ui_implementation_contract_policy:
  required_when: "UIREF, 화면 퍼블리싱 산출물, Figma, 이미지 시안, 기존 화면 캡처가 있는 경우"
  gate3_usage:
    - "UI 테스트 기대 화면에 관련 UICON-ID를 연결한다."
    - "필수 유지 요소와 허용 차이를 비교 방식에 포함한다."
    - "금지 변경이 발생하면 Gate 4에서 FIND로 판정할 수 있게 기준을 적는다."
```

## Review Notes

- `working_documents`에는 이번 Run이 작성/갱신할 테스트케이스와 추적표만 둔다. 요구사항과 설계 산출물은 테스트 전개가 필요할 때 `reference_on_demand`에서 관련 ID 기준으로 확인한다.
- 테스트를 실제로 실행하지 않았으면 통과로 쓰지 않는다. Gate 3는 테스트 설계 단계다.
- Gate 3에서는 테스트를 실행하지 않더라도, Gate 4에서 동일하게 실행할 수 있도록 cwd, 명령, 성공 기준, 증적 경로를 정한다.
- Gate 3 테스트 설계는 그룹 요구사항 `REQ-001`이 아니라 상세 요구사항 `REQ-001-01` 단위로 매핑한다.
- 테스트케이스 문서에는 요구사항정의서의 모든 상세 `REQ-NNN-NN`이 적어도 한 번 이상 나타나야 하며, 테스트가 불필요하면 `해당없음`과 사유를 남긴다.
- 회원가입, 로그인, TODO처럼 상태가 있는 화면은 기본/오류/성공/전환을 별도 UI-ID로 나눈다.
- 화면 퍼블리싱 기반 화면은 `UI-ID -> SCR-ID -> UIREF-ID -> UICON-ID -> 증적 경로` 흐름으로 연결한다.

