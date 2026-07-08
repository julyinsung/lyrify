# Gemini / Antigravity Adapter (GEMINI Standard)

> 상태: v0.2 (Gemini/Agy Orchestrator 및 Runner 어댑터 명세)
> 목적: Gemini 및 Antigravity/Agy 환경에서 Vulcan-Anvil Ex 프레임워크의 규칙과 제약을 이행하기 위한 바인딩 가이드라인을 정의한다.

---

## 1. 연동 개념

Gemini Adapter는 Core의 공통 규약 및 Run 입력을 Gemini 모델과 Antigravity/Agy 플랫폼 특성에 맞게 중재하고, 출력을 정규화하는 얇은 레이어입니다.

Antigravity/Agy는 단순 worker runner뿐 아니라 메인 Orchestrator가 될 수 있다. Agy가 메인 Orchestrator인 경우 `GEMINI.md`, `docs/core/`, `docs/adapters/gemini/`를 기준으로 Gate 진행, Run 생성, native worker 위임, 결과 검증을 조율한다.

공통 Gate 실행 기준은 `docs/core/GATE_EXECUTION_CHECKLIST.md`를 따른다. Gemini/Antigravity Run 입력은 이 공통 체크리스트와 `docs/adapters/gemini/GATE_PROMPTS_GEMINI.md`를 읽으며, Codex 전용 `docs/adapters/codex-gpt/GATE_PROMPTS.md`를 실행 계약으로 사용하지 않는다.

```text
+-------------------+      +-------------------------+      +---------------------+
|    Core Rule      | ---> |     Gemini Adapter      | ---> |    Gemini Runner    |
| (Run Input YAML)  |      |  (Structured Schema)    |      |    (API Execution)  |
+-------------------+      +-------------------------+      +---------------------+
```

## 2. Gemini 특화 연동 전략

### ⓪ Agy main Orchestrator mode

Agy를 메인 Orchestrator로 사용할 때는 다음 기준을 적용한다.

* Core Gate 규칙은 `docs/core/GATE_EXECUTION_CHECKLIST.md`를 따른다.
* Agy/Gemini 전용 prompt와 persona mapping은 `docs/adapters/gemini/` 문서를 따른다.
* 현재 Gate/Profile/Branch/Run 상태와 다음 행동 후보는 먼저 `python vulcan.py status`로 확인한다.
* Delivery Profile 세부 기준은 `docs/core/DELIVERY_PROFILES.md`를 따른다. `profile: poc`이면 `docs/poc/POC_REQUIREMENTS.md`, `docs/poc/POC_SYSTEM_DESIGN.md`, `docs/poc/POC_TEST_REPORT.md` 3종을 공식 작업 문서로 보고, audit 산출물 파일을 임의 생성하거나 채우지 않는다.
* Phase 0~Gate 3 동안 Agy `Workspace: branch`를 Environment Readiness Track에 사용할 수 있다. 이 경로는 폴더, 의존성, lockfile, lint/build/test 스크립트, hello/health smoke를 준비하는 용도이며 업무 요구사항 구현, 테스트 Pass 확정, 추적표 Implemented/Verified 변경은 금지한다.
* `profile: poc`의 Impl worker는 코드, dependency manifest, 빠른 self-check까지만 담당한다. `README.md`, `POC_TEST_REPORT.md` 최종화, browser smoke/screenshot, release/backlog, 증적 정규화는 Gate 4/5 또는 별도 Evidence/Normalization worker로 넘긴다.
* Gate 전환 가능성은 `python vulcan.py status --check`로 요약 진단하고, `prepare-transition`은 상세/호환 진단이 필요할 때 직접 실행한다.
* Agy native subagent와 `Workspace: branch`는 외부 CLI runner가 아니라 native delegation 경로로 취급한다.
* worker 호출 전 Orchestrator가 직접 `python vulcan.py run-preflight <run-file>`를 실행한다.
* worker 결과는 `delegation_records.mode: agy-branch-agent`로 남기고, 최종 Gate/Wave/QA 판단은 Orchestrator가 부모 workspace에서 다시 검증한다.

### ① Structured Outputs (JSON Schema 강제) 활용
* Gemini API가 지원하는 `responseSchema`를 활용하여 워커의 출력이 `RUN_OUTPUT_CONTRACT_GEMINI.md` 규격에 선언된 정형 JSON/YAML 스키마를 최대한 준수하도록 유도합니다.
* 스키마 제약을 적용하여 워커의 포맷 정합성 오류 및 파싱 실패율을 획기적으로 낮춥니다. (단, 모델의 부분 출력이나 예외적인 API 오류 가능성이 있으므로 예외 대응 처리를 권장합니다.)

### ② 대규모 컨텍스트 윈도우 (Long-context Window) 최적화
* Gemini의 대용량 컨텍스트 윈도우 특성을 유용하게 활용하되, 비효율적인 컨텍스트 낭비를 방지하기 위해 1차적으로는 작업에 핵심적인 trace seed와 관련 소스 문서(source_documents) 위주로 컨텍스트를 주입하고, 필요 시 의존 관계가 있는 파일들로 점진적 확장하는 방식을 지향합니다.
* 이를 통해 파일 간 의존 관계 누락을 방지하면서도 경량화된 부트스트랩 조율 철학을 유지합니다.

### ③ Antigravity Workspace: branch native delegation

Antigravity/Agy가 제공하는 `Workspace: branch` 방식은 Gemini adapter의 native branch agent 경로로 취급한다.

이 경로는 일반 Git worktree 또는 `agy.exe` 외부 CLI runner와 다르다. Agy runtime이 가상 브랜치/오버레이 작업공간을 관리하므로, Run 문서에는 두꺼운 `_exec` 로그 대신 `delegation_records.mode: agy-branch-agent`로 delegate, task, status, changed files, result summary를 얇게 기록한다.

Orchestrator는 Agy worker 결과를 그대로 확정하지 않고 부모 workspace에서 변경 파일과 `scope.writable`을 확인하고 필요한 검증 명령을 재실행한다.

Orchestrator는 Agy native branch worker에게 위임하기 전에 반드시 `python vulcan.py run-preflight <run-file>`를 직접 실행한다. 이 경로는 `run-exec`/`agent-run --mode work`의 자동 preflight를 통과하지 않으므로, `status --check`/`prepare-transition`의 사후 점검은 누락을 발견하는 안전망으로만 취급한다.

Environment Readiness Track에서 생성한 결과도 같은 방식으로 검증한다. 단, 환경 기준선 후보는 기능 구현 Wave가 아니므로 REQ/AC/UI/UT/IT를 `Implemented`, `Verified`, `Pass`로 변경하지 않는다.

PoC Impl worker는 `Workspace: branch`의 속도 이점이 있더라도 browser evidence, README, 최종 테스트 결과서, release/backlog 정리까지 한 번에 수행하지 않는다. 구현 파일과 빠른 self-check를 반환하고, 비차단 `run-preflight`/`run-check` 경고가 남으면 제거 루프를 반복하지 않고 후속 판단 항목으로 보고한다.

Agy `Workspace: branch` worker가 부모 workspace의 untracked Run 문서에 직접 쓰지 못해도 실패로 처리하지 않는다. worker는 변경 파일, self-check, 요약을 반환하고, Orchestrator가 부모 workspace에서 Run 문서와 `delegation_records`를 정규화한다.

`agent-run`/`run-exec`로 `agy.exe`를 호출하는 경로는 transcript, watchdog, 프로세스 로그 같은 외부 CLI 증적이 필요한 경우의 선택 옵션이다.

검토 기록: [Agy Workspace Branch Delegation Review](../../reference/_reviews/AGY-WORKSPACE-BRANCH-DELEGATION-REVIEW.md)

## 3. 하위 최소 산출물 구성

Gemini 어댑터는 다음 문서들로 구성되어 제어 규칙을 이행합니다.

1. **[README_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/adapters/gemini/README_GEMINI.md)**: 본 개요 및 개념 정의서
2. **[LIMITATIONS_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/adapters/gemini/LIMITATIONS_GEMINI.md)**: Gemini 엔진 고유의 한계와 극복 지침
3. **[GATE_PROMPTS_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/adapters/gemini/GATE_PROMPTS_GEMINI.md)**: 런타임 구동 엔진이 기계적으로 파싱 가능한 구조화된 게이트 프롬프트 템플릿
4. **[PERSONA_MAPPING_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/adapters/gemini/PERSONA_MAPPING_GEMINI.md)**: 코어 페르소나와 Gemini 시스템 인스트럭션 매핑 규칙
5. **[RUN_OUTPUT_CONTRACT_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/adapters/gemini/RUN_OUTPUT_CONTRACT_GEMINI.md)**: 워커가 실행 완료 시 반환해야 하는 JSON/YAML 구조화 출력 정의서
