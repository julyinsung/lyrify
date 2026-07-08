# Independent Review Process

> 상태: v0.1
> 목적: 작성 세션과 분리된 독립 검수를 Gate 종료 검수의 기본 권장 절차로 정의한다.

## 1. 개념

독립 검수는 `INDEPENDENT_EXECUTION_PROCESS.md`의 `review` 유형에 해당한다.
즉 독립 검수와 독립 구현은 별도 세션/worktree 실행이라는 같은 실행 모델을 공유하되, 이 문서는 읽기 중심 검수 절차만 상세히 정의한다.

Vulcan-Anvil Ex의 리뷰는 두 가지로만 구분한다.

| 구분 | 의미 | 예 |
| --- | --- | --- |
| 자체 점검 | 같은 세션에서 Orchestrator가 스스로 산출물과 증적을 점검한다 | 작성 직후 체크리스트 확인, `run-check`, `check-trace` |
| 독립 검수 | 작성 세션과 분리된 세션, worktree, 또는 다른 runner가 산출물과 증적을 다시 검토한다 | 새 Codex CLI 세션, Claude CLI, GitHub reviewer, 수동 검수 |

독립 검수에서 Codex가 검토하는지 Claude가 검토하는지는 단계명이 아니라 `runner` 속성이다. 결과는 `PASS`, `FIND`, `CR`, `ISSUE` 후보로 남기고, Orchestrator가 본선 산출물 반영 여부를 다시 판단한다.

## 2. 기본 원칙

- 독립 검수는 Gate 2와 Gate 4에서 기본 권장 절차다.
- 독립 검수는 자동 승인 또는 자동 Gate 전환 조건이 아니다.
- 우선 적용 Gate는 `gate2`, `gate4`다.
- 리뷰 요청과 결과는 `docs/reviews/`에 파일로 남긴다.
- 리뷰 Run은 `docs/runs/`에 별도로 남긴다.
- 가능하면 별도 worktree를 사용해 작성 맥락과 파일 변경을 분리한다.
- 독립 검수 결과는 자동 승인하지 않는다. Orchestrator가 재검토한 뒤 `FIND`, `CR`, `ISSUE`, 승인 후보로 분류한다.

## 3. 설정

프로젝트 루트의 `vulcan.config.json`에서 독립 검수 기본값을 둔다.

```json
{
  "runtime": {
    "available_runners": [
      {
        "name": "codex-cli",
        "model": "gpt-5.5",
        "effort": "high"
      },
      {
        "name": "claude-cli",
        "model": "claude-opus-4-7",
        "effort": "high"
      },
      {
        "name": "antigravity-cli",
        "model": "gemini-3.5-flash",
        "effort": "high"
      }
    ]
  },
  "review": {
    "independent_enabled": true,
    "independent_sandbox": "workspace-write",
    "independent_exec_timeout_seconds": 1800,
    "independent_triggers": ["gate2", "gate4"],
    "independent_worktree": true,
    "independent_readonly": true
  }
}
```

`independent_enabled`가 `true`이면 Orchestrator는 `independent_triggers`에 포함된 Gate 종료 전 독립 검수를 기본 권장 절차로 제안한다. 다만 자동 실행은 하지 않는다. 사용자의 명시 지시 또는 Orchestrator의 별도 실행 판단이 있을 때 `vulcan.py agent-run --mode review`를 실행한다.

## 4. 모델과 추론 강도

독립 검수는 작성자가 놓친 누락, 모순, 미실행 검증을 잡아내는 역할이므로 Codex `review` role 기본값은 `gpt-5.5`와 `high` reasoning effort를 권장한다.
Codex runner의 역할별 model/effort 정책은 `CODEX_MODEL_POLICY.md`와 `vulcan.config.json.runtime.model_policy.codex-cli`를 따른다.
Claude runner 기본값은 `claude-opus-4-7`과 `high` effort를 사용한다.
Antigravity runner 기본값은 `gemini-3.5-flash`와 `high` effort를 사용한다.
Claude runner는 worktree 또는 독립 실행 디렉터리 격리를 전제로 `--dangerously-skip-permissions`를 사용해 권한 확인 대기 없이 검수 명령을 끝까지 수행한다. Orchestrator는 결과 파일과 diff를 다시 확인한 뒤 반영 여부를 판단한다.

프로젝트 기본 모델과 effort는 `runtime.available_runners`에서 정하고, Codex는 `runtime.model_policy.codex-cli`로 역할별 override를 둘 수 있다.

```json
{
  "runtime": {
    "available_runners": [
      {
        "name": "codex-cli",
        "model": "gpt-5.5",
        "effort": "high"
      },
      {
        "name": "claude-cli",
        "model": "claude-opus-4-7",
        "effort": "high"
      },
      {
        "name": "antigravity-cli",
        "model": "gemini-3.5-flash",
        "effort": "high"
      }
    ]
  }
}
```

특정 리뷰 실행에서만 바꾸려면 `agent-run --mode review` 옵션으로 override한다.

```bash
python vulcan.py agent-run --mode review \
  --review-id RV-001 \
  --model gpt-5.5 \
  --reasoning-effort high
```

Claude CLI로 실행할 때는 runner만 바꾼다.

```bash
python vulcan.py agent-run --mode review \
  --review-id RV-001 \
  --runner claude-cli \
  --model claude-opus-4-7 \
  --reasoning-effort high
```

Antigravity CLI로 실행할 때도 runner만 바꾼다. 현재 Ex는 IDE 창을 열지 않는 `agy.exe --print`를 사용하며, model/effort 전용 플래그가 없을 수 있으므로 Antigravity CLI에 설정된 기본 모델/effort를 따른다.
Ex는 요청 모델과 effort를 프롬프트 및 실행 기록에 남기고, 실행 기록에는 `model_source: agy-config-inherited`를 함께 남긴다.
Antigravity runner가 exit code 0으로 종료됐더라도 stdout/stderr와 result 변경이 모두 없으면 `failed_empty_output`으로 처리한다.

```bash
python vulcan.py agent-run --mode review \
  --review-id RV-001 \
  --runner antigravity-cli \
  --model gemini-3.5-flash \
  --reasoning-effort high
```

`agent-run --mode review`는 실제 실행 증적을 Independent Review Run에 남긴다.
기존 `review-run`은 호환 명령으로 유지한다.

```yaml
runner: codex-cli
model: gpt-5.5
reasoning_effort: high
deadline_at: "2026-05-20T23:30:00"
duration_seconds: 420
timeout_seconds: 1800
timed_out: false
status: completed
exit_code: 0
json_log: docs/reviews/RV-001_codex-exec.jsonl
last_message: docs/reviews/RV-001_codex-last-message.md
result_file_changed: true
```

운영 기준:

- Gate 2 설계 검수와 Gate 4 QA 검수는 Codex runner 기준 `gpt-5.5` + `high`를 기본으로 사용한다.
- Claude runner 기준 기본값은 `claude-opus-4-7` + `high`다.
- Antigravity runner 기준 기본값은 `gemini-3.5-flash` + `high`다.
- 빠른 예비 검토나 로컬 스모크 확인만 필요하면 일회성으로 `--reasoning-effort low`를 사용할 수 있다.
- 독립 검수 실행은 result 파일 작성을 계약으로 하므로 `--sandbox read-only`를 사용하지 않는다. `agent-run --mode review`와 `review-run`은 read-only sandbox를 차단하고 `workspace-write` 사용을 요구한다.
- 검수 완료 보고에는 실제 사용된 `model`과 `reasoning_effort`를 남긴다.
- timeout은 `review.independent_exec_timeout_seconds`를 따르며 기본값은 1800초다.
- timeout이면 `status: timeout`, `timed_out: true`, `exit_code: 124`로 기록한다.
- token/사용량 한도 종료는 runner마다 표현이 달라서 직접 판정하지 않는다. stderr/stdout, last_message, `result_file_changed`를 근거로 Orchestrator가 실패 원인을 확인한다.

## 5. 생성 명령

```bash
python vulcan.py review-request \
  --gate gate2 \
  --title "Gate 2 설계 독립 검수" \
  --from-run RUN-003 \
  --related-ids REQ-001,FUNC-001,SCR-001
```

기본 동작:

- `docs/reviews/RV-NNN_*_request.md` 생성
- `docs/reviews/RV-NNN_*_result.md` 생성
- `docs/runs/RUN-NNN_independent-review-*_v0.1.md` 생성
- `vulcan.config.json.review.independent_worktree`가 `true`이면 detached worktree 생성

## 6. 실행 명령

`codex-cli` runner를 사용할 수 있으면 Orchestrator가 독립 검수 세션을 비대화형으로 실행할 수 있다.

```bash
python vulcan.py agent-run --mode review --review-id RV-001
```

기본 동작:

- `codex-cli`는 `codex exec`를 새 비대화형 세션으로 실행한다.
- `claude-cli`는 `claude -p`를 새 비대화형 실행으로 사용한다.
- `antigravity-cli`는 `agy.exe --print`를 새 headless 실행으로 사용한다.
- worktree가 있으면 해당 worktree를 `--cd`로 사용한다.
- 모델과 reasoning effort는 기본적으로 `vulcan.config.json.review` 또는 Codex role policy 값을 사용하며, `--model`, `--reasoning-effort`로 실행 단위 override가 가능하다.
- Antigravity runner는 `--add-dir <worktree>`와 프롬프트에 포함된 review request/result 경로를 기본 입력으로 사용한다. 나머지 상류/작업 문서는 request 안의 계약을 따라 worker가 직접 읽는다.
- 실행 로그를 `docs/reviews/RV-NNN_{runner}-exec.*`에 남긴다.
- 마지막 응답을 `docs/reviews/RV-NNN_{runner}-last-message.md`에 남긴다. Antigravity runner는 stdout이 비어 있을 수 있으므로 `transcript_full.jsonl` 우선, `transcript.jsonl` fallback 순서로 마지막 모델 응답을 회수한다.
- 실행 시작과 종료 상태를 `docs/runs/_exec/RV-NNN_{runner}-activity.json`에 남긴다. 로컬 대시보드는 이 파일로 `running`, `completed`, `failed`, `timeout` 상태를 표시한다.
- result 파일 변경 여부와 exit code를 Independent Review Run에 기록한다.

주의:

- `agent-run --mode review`는 Desktop 대화창을 새로 여는 기능이 아니다.
- `codex exec` 기반의 독립 실행 세션을 만든다.
- result 파일이 변경되었더라도 Orchestrator가 다시 검토한 뒤 본선 산출물 반영 여부를 결정한다.

## 7. 리뷰어의 작업

리뷰어는 request 파일을 읽고 result 파일만 작성한다.

### 금지

- 본선 산출물을 직접 수정하지 않는다.
- 작성자의 의도를 추측해 누락을 통과시키지 않는다.
- 실행하지 않은 테스트를 Pass로 기록하지 않는다.
- 대화상 승인 없이 `User Approved`로 기록하지 않는다.

### 필수

- `PASS`, `FIND`, `CR`, `ISSUE` 중 하나로 판정한다.
- `FIND`는 승인된 범위 안의 결함으로 남긴다.
- 기준선 변경이 필요하면 `CR`로 남긴다.
- 추가 판단이 필요하면 `ISSUE`로 남긴다.
- 검증 명령을 실행했으면 cwd, 명령, exit code, 성공 기준, 로그/증적 경로를 기록한다.

## 8. Gate별 중점

### Gate 2

- Gate 2 독립 검수는 Gate 2 산출물만 보지 않는다. 반드시 Phase 0, Gate 1, Gate 2 순서로 상류 정합성을 먼저 확인한다.
- Phase 0의 목표, 제약, 가정, 질문, DEC/RISK/ASM이 Gate 1 요구사항과 범위에 반영되었는지 확인한다.
- Gate 1의 REQ/NREQ/AC, 포함/제외 범위, DEC/ISSUE가 Gate 2 설계의 전제와 모순되지 않는지 확인한다.
- Gate 2 설계가 Gate 1 범위를 임의로 축소하거나 확장하지 않았는지 확인한다. 범위 변경이 필요하면 `CR` 또는 `ISSUE` 후보로 남긴다.
- Gate 2 설계 순서가 지켜졌는지 확인한다.
- SW Architecture가 상세 설계와 함께 Baseline 후보로 보강되었는지 확인한다.
- REQ/AC가 FUNC, SCR, PGM, API, DB, SEC, DEV 기준으로 전개되었는지 확인한다.
- UIREF/ui-baseline이 있으면 UI Implementation Contract와 상태별 UI 증적 기준이 있는지 확인한다.
- Gate 3 테스트 설계로 넘길 검증 후보와 미해결 질문이 분리되었는지 확인한다.

Gate 2 result 파일에는 다음 판정을 별도로 남긴다.

| 판정 항목 | 확인 기준 |
| --- | --- |
| `Phase0 -> Gate1` | Phase 0 목표, 제약, 가정, 질문이 Gate 1 요구사항/범위/DEC로 내려왔는가 |
| `Gate1 -> Gate2` | REQ/NREQ/AC와 포함/제외 범위가 설계 산출물에 빠짐없이 전개됐는가 |
| `Scope Drift` | Gate 2가 승인된 Gate 1 범위를 임의 확장/축소하지 않았는가 |
| `Open Decisions` | 미해결 DEC/ISSUE/RISK/ASM이 닫혔거나 다음 Gate 입력으로 분리됐는가 |
| `Design Internal Consistency` | 아키텍처, 화면, 기능, API, 프로그램, DB, 보안, 개발표준이 서로 모순되지 않는가 |

### Gate 4

- 테스트 결과서가 개발표준과 테스트케이스의 필수 명령을 모두 기록했는지 확인한다.
- 각 검증 결과에 cwd, 명령, exit code, 성공 기준, 로그/증적 경로가 있는지 확인한다.
- UI 증적이 상태/시나리오별 UI-ID와 1:1로 연결되었는지 확인한다.
- 기준 UIREF와 구현 screenshot 차이가 `Pass`, `FIND`, `CR`로 판정되었는지 확인한다.
- 미실행 검증이나 기대 화면과 다른 캡처가 Pass로 기록되지 않았는지 확인한다.

## 9. Worktree 정리

독립 검수 worktree는 결과 수집 후 사람이 확인하고 삭제한다.

```bash
git worktree remove <worktree-path>
```

삭제 전 result 파일이 본선 `docs/reviews/`에도 반영되어 있는지 확인한다.
