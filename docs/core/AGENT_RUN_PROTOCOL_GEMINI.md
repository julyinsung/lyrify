# Agent Run Protocol (GEMINI Standard - Core)

> 상태: v0.2 (Gemini & Multi-Worker 공통 실행 프로토콜)
> 목적: Vulcan-Anvil Ex 프레임워크에서 오케스트레이터와 다양한 워커가 동적 타입 계약 및 JSONL 실시간 스트림 파이프라인을 바탕으로 안전하게 협업하는 런타임 실행 프로토콜을 정의한다.

---

## 1. 개요 및 원칙

본 **Agent Run Protocol (GEMINI Standard)**는 워커 에이전트의 런타임 자율성이 프레임워크의 거버넌스(Gate Rules, Traceability)와 정합성을 훼손하지 않도록 제어하는 런타임 조율 프로토콜입니다.

* **인터페이스 계약 엄격성**: 워커는 임의의 함수 시그니처나 파일 수정을 하지 않고, 주입된 `interface_contract`와 `scope` 내에서만 개발합니다.
* **비동기 정합성 확보**: 워커의 실시간 진행 이력은 JSONL 스트림으로 오케스트레이터에게 파이프라이닝되며, 최종 산출물은 `RUN_OUTPUT_CONTRACT` 규격으로 취합되어 기계적으로 검증됩니다.

---

## 2. 런타임 실행 단계 및 프로토콜 절차

오케스트레이터가 워커를 기동하고 완료를 반영하기까지의 5단계 프로토콜 절차입니다.

```text
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ 1. Run 생성    │ ───> │ 2. Input 빌드  │ ───> │ 3. 워커 기동   │
│ (vulcan.py)    │      │ (Signature주입)│      │(Subagent/Branch)│
└────────────────┘      └────────────────┘      └────────┬───────┘
                                                         │
                        ┌────────────────┐               │ (JSONL 파이프라인)
                        │ 5. 통합 & 갱신  │ <─── [4. 완료 및 반환]
                        │ (run-integrate)│      (Output 검증)
                        └────────────────┘
```

### 1단계: Run 문서 초안 작성 (Orchestrator)
* `vulcan.py gate-start` 및 오케스트레이터 계획에 따라, 대상 기능 단위에 부합하는 `RUN-NNN` 문서를 작성합니다.

### 2단계: Run Input 완전화 및 계약 주입 (Orchestrator Adapter)
* 오케스트레이터는 [RUN_INPUT_CONTRACT.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/core/RUN_INPUT_CONTRACT.md) 규격에 맞춰 다음 동적 계약을 주입합니다.
  * **TBD 플레이스홀더 제거**: 초안(Draft)의 `target_contracts`와 `interface_contract`에 남아 있는 `"TBD:"` 플레이스홀더를 프로그램 설계서(Program-Design)의 실제 코드 시그니처와 스키마로 완전히 대체하여 바인딩합니다.
  * **Interface Signature**: Gate 2 설계서에서 명세된 함수 시그니처 및 Pydantic/TypeScript DTO 코드 블록.
  * **Test Stub**: Gate 3 테스트 설계서에서 도출된 필수 테스트 함수명 및 검증 시나리오 목록.
  * **Standard ID**: 이번 구현에서 준수해야 할 개별 개발 표준 식별 코드 목록.

### 3단계: 워커 에이전트 기동 및 스트림 캡처 (Orchestrator -> Worker)
* 오케스트레이터는 워커 에이전트(agy subagent 등)를 기동하기 직전, 반드시 `python vulcan.py run-preflight <RUN-file>`을 실행하여 계약(TBD 미보강 등) 및 Scope 차단 요소가 없음을 사전 검증합니다.
* 검증 통과 후 Antigravity 런타임의 서브에이전트 기동 도구인 `invoke_subagent`를 호출하여 가상 격리 워크스페이스(`Workspace: branch` 모드) 상에서 워커를 기동합니다.
* `profile: poc`의 Impl worker에게는 코드, dependency manifest, 빠른 self-check만 맡깁니다. `README.md`, 최종 테스트 결과서, browser smoke/screenshot, release/backlog, 증적 정규화는 Gate 4/5 또는 별도 Evidence/Normalization worker로 분리합니다.
* 워커가 구동되는 동안 출력되는 진행 이력 및 실시간 로그 스트림을 파싱하여, 대화 단절 시 즉시 복구(Resume)할 수 있는 `conversation_id`(또는 `thread_id`) 및 실시간 태스크 대시보드 상태를 동적으로 갱신합니다.

### 4단계: 워커 수행 완료 및 출력 계약 검증 (Worker -> Orchestrator)
* 워커는 작업을 완료하고 [RUN_OUTPUT_CONTRACT.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/core/RUN_OUTPUT_CONTRACT.md) 포맷에 맞춰 완료보고서를 작성 및 반환합니다.
* 오케스트레이터는 구조적 Schema 정합성, 준수 보고서(`standard_compliance_report`), 그리고 위임(subagent, branch agent 등) 발생 시의 `delegation_records` 누락 여부를 검증합니다.
* PoC Impl worker가 비차단 `run-preflight`/`run-check` 경고를 받았더라도 이를 제거하기 위해 장시간 반복하지 않습니다. 구현 테스트와 빠른 self-check가 통과했다면 경고와 후속 판단 필요 항목을 출력 계약에 남기고 반환합니다.
* Agy `Workspace: branch` worker가 격리 workspace 안에서 부모의 untracked Run 문서를 직접 갱신하지 못해도 실패로 보지 않습니다. worker 반환 요약을 기준으로 Orchestrator가 부모 workspace에서 Run 결과와 `delegation_records`를 정규화합니다.

### 5단계: 변경 사항 통합 및 세션 동기화 (Orchestrator)
* 오케스트레이터는 `python vulcan.py run-integrate` 명령을 실행해 워커가 수정한 파일이 `scope.writable`에 부합하는지 최종 git diff를 검증한 후 부모 workspace 또는 통합 브랜치에 반영 후보로 통합합니다.
* 성공 시 `vulcan.py wave-complete` 및 `sync-session`을 통해 session 상태를 갱신하고, Gate 전환 전에는 `python vulcan.py status --check`로 Run 완료와 추적성 정합성을 함께 확인합니다. `prepare-transition`은 상세/호환 진단이 필요할 때 직접 실행하고, 추적성 오류가 남으면 `check-trace`를 별도 상세 진단으로 실행합니다.
