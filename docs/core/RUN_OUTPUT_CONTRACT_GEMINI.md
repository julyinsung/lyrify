# Run Output Contract (GEMINI Standard - Core)

> 상태: v0.4 (Gemini & Multi-Worker 공통 출력 표준)
> 목적: Codex, Claude, Gemini 등 모든 워커 러너가 실행 완료 시 오케스트레이터에게 반환해야 하는 결과 데이터 구조를 공통 표준화하여, 자동 정규화 및 추적 매트릭스(Traceability Matrix) 연동의 무결성을 확보한다.

---

## 1. 개요

모든 워커 러너는 실행 완료 시 본 문서에 규정된 공통 출력 데이터 구조에 맞춰 결과를 제출해야 합니다. 
어댑터는 이 공통 구조를 모델별 출력 수단(JSON, YAML, Markdown Front Matter 등)으로 변환하는 매핑만 담당하며, 출력 항목 자체를 임의로 수정하거나 변경할 수 없습니다.

```text
+----------------------+
|    Worker Runner     | (Codex, Claude, Gemini)
+----------------------+
           |  (API 응답 또는 완료 파일 작성)
           v
+----------------------+
|  Run Output Contract | (Core 공통 정규화 포맷)
+----------------------+
           |  (vulcan.py run-integrate 자동 파싱)
           v
+----------------------+
|  Traceability Matrix | (추적표 및 session.json 갱신)
+----------------------+
```

---

## 2. 공통 출력 데이터 스키마 (YAML/JSON 표준 명세)

워커가 제출해야 하는 결과 데이터의 공통 명세입니다.

```yaml
run_id: "RUN-NNN"
status: "Completed" # Completed, Blocked, Failed, In Progress 중 택일
completed_at: "YYYY-MM-DD"

# 1. 실제 수정/생성한 물리 파일 리스트 (scope 내부에 존재해야 함)
changed_files:
  - file_path: "relative/path/to/file"
    status: "Modified" # Created, Modified, Deleted 중 택일

# 2. 이번 작업을 통해 통과/연결된 추적성 식별자
related_ids:
  - "REQ-001"
  - "FUNC-005"
  - "UT-007"

# 3. 개발 표준 준수 정량 보고서 (development_standards_applied와 일치해야 함)
standard_compliance_report:
  - standard_id: "DEV-LOG-001"
    status: "Pass" # Pass, Fail, N/A 중 택일
    details: "준수한 구체적 코드 블록 설명 및 위치 기록"

# 4. 실행 검증 결과 및 증적
verification_results:
  - command: "pytest tests/test_todo.py"
    result: "passed" # passed, failed, not_run 중 택일
    summary: "테스트 통과 로그 요약 또는 파일 경로 명시"

# 5. 위임 작업 기록 (위임이 있었을 경우 필수)
delegation_records:
  - mode: "agy-branch-agent" # agy-branch-agent, external-runner, manual 등
    delegate: "build" # build, qa-execution 등
    native_agent: true
    task: "Todo backend API 구현"
    scope:
      writable:
        - "backend/app/"
    started_at: "2026-06-07T10:00:00+09:00"
    completed_at: "2026-06-07T10:08:00+09:00"
    status: "completed"
    changed_files:
      - "backend/app/todos/service.py"
    result_summary: "Todo service를 구현했다."
    orchestrator_verification:
      - command: "pytest backend/tests"
        result: "passed"

# 6. 오케스트레이터가 후속 결정해야 하는 액션 아이템
orchestrator_decision_needed:
  - item: "요청 유형" # e.g., Traceability Matrix Sync, Gate 전환, PR Merge
    reason: "판단의 이유 및 상세 설명"

# 7. 작업 중 발견된 예외 사항
open_issues: [] # 설계 누락 또는 진행 불가 리스크
findings: []    # 작업 도중 발견된 작은 설계 불일치나 QA 결함
change_requests: [] # 요구사항을 벗어나 설계 변경이 강제되는 건
```

---

## 3. 필드별 정합성 검증 규칙 (Orchestrator Validation Policy)

오케스트레이터의 통합 엔진은 워커가 반환한 결과를 통합하기 전 다음 규칙을 정적 분석으로 강제 검증합니다.

1. **상태 정합성**: `status`가 `Completed`이지만 `verification_results` 중 단 하나라도 `failed`가 있으면, 통합 프로세스는 즉시 실패 처리되고 워커에게 재작업을 지시해야 합니다.
2. **개발 표준 누락 검증**: Run Input Contract에 지정된 준수 표준 ID(e.g., `DEV-LOG-001`)가 `standard_compliance_report` 배열에 모두 존재하고, 준수 상태(`status`)가 유효하게 보고되었는지 대조합니다.
3. **쓰기 권한(Scope) 검증**: `changed_files`에 나열된 모든 경로가 Run Input의 `scope.writable`에 정의된 하위 경로 내에 존재하며, 실제로 git diff 상에서 변경된 파일과 100% 일치하는지 물리적으로 검증합니다.
