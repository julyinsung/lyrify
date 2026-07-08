# Independent Execution Process

> 상태: v0.1
> 목적: 독립 검수, Build Wave, Evidence Run을 같은 별도 세션/worktree 실행 모델로 다루기 위한 공통 규칙을 정의한다.

## 1. 개념

Independent Execution은 Orchestrator의 현재 대화 세션과 분리된 runner가 Run 계약을 읽고 작업하는 실행 단위다.

독립 검수와 독립 구현은 본질적으로 같은 구조다.
차이는 읽기 중심인지, 쓰기 중심인지, 그리고 어떤 source document와 scope를 받는지다.

| 실행 유형 | 목적 | 권한 | 대표 출력 |
| --- | --- | --- | --- |
| `review` | 산출물, 코드, 테스트, 증적을 독립 검수 또는 교차검증한다 | 읽기 중심, result 파일 작성 | `PASS`, `FIND`, `CR`, `ISSUE` 후보 |
| `pr-cross-validation` | PR diff, CI, 리뷰 코멘트, 관련 Run을 작성 runner와 다른 runner가 교차검증한다 | 읽기 중심, PR comment 또는 result 파일 작성 | merge 가능 후보, `FIND`, `CR`, `ISSUE` 후보 |
| `build` | 승인된 Build Wave 범위 안에서 구현한다 | 쓰기 중심, scope 제한 | 코드, 테스트, Run 결과, traceability delta |
| `evidence` | 테스트 로그와 화면 증적을 수집한다 | 쓰기 중심, evidence 경로 제한 | 테스트 결과, Playwright screenshot, 로그 |
| `qa-fix` | 승인된 FIND를 기존 설계 범위 안에서 수정한다 | 쓰기 중심, FIND 범위 제한 | 수정 코드, 재검증 결과 |

Runner는 Codex인지 Claude인지가 본질이 아니다.
Codex CLI, Claude CLI, GitHub reviewer, 수동 검수자는 모두 Run 계약을 수행하는 실행기다.

## 2. 공통 원칙

- Run은 먼저 파일로 존재해야 한다.
- Runner는 Run의 `source_documents`, `scope`, `completion_criteria`, `output_requirements`를 읽고 수행한다.
- Runner는 현재 Gate보다 앞선 산출물, 구현, 테스트, 증적을 임의로 만들지 않는다.
- 쓰기 작업은 Run의 writable scope 안에서만 수행한다.
- Review runner는 본선 산출물을 직접 수정하지 않고 result 또는 review 파일에 후보 판단을 남긴다.
- Build runner가 만든 결과는 Orchestrator가 다시 검토하고 통합한다.
- Runner 완료 보고만으로 Gate를 완료 처리하지 않는다.
- Runner는 Gate 전환, `session.json`의 Gate 상태 변경, 사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 판단하지 않는다.
- Runner가 위 판단이 필요하다고 보더라도 직접 처리하지 않고 Orchestrator 결정 필요 항목으로 반환한다.
- Worktree를 사용한 경우 결과 수집 후 사람이 확인하고 정리한다.

## 3. Runner 구분

| Runner | 비대화형 실행 기준 | 비고 |
| --- | --- | --- |
| `codex-cli` | `codex exec` | JSONL 로그와 last message 저장 |
| `claude-cli` | `claude -p` | `--output-format json`, `--model`, `--effort`, `--dangerously-skip-permissions` 사용 |
| `antigravity-cli` | `agy.exe --print` | Headless Gemini runner. Antigravity CLI에 설정된 model/effort를 상속한다 |
| `manual` | 사람이 result 파일 작성 | 정책, 승인, 일정 판단에 사용 |

Claude CLI와 Antigravity CLI는 Codex CLI처럼 별도 대화창을 여는 것이 아니라 비대화형 실행을 만들 수 있다.
따라서 `agent-run`, `review-run`, `run-exec`의 runner로 사용할 수 있다.

기본 Claude 설정은 `claude-opus-4-7` + `high` effort를 사용한다.
Claude Code 공식 기준으로 Opus 4.7은 `low`, `medium`, `high`, `xhigh`, `max` effort를 지원한다.
`xhigh`가 Opus 4.7의 권장 기본값에 가깝지만, Ex 기본값은 비용과 안정성을 고려해 `high`로 둔다.
Claude worker는 worktree 격리를 전제로 비대화형 실행에서 `--dangerously-skip-permissions`를 사용한다. Orchestrator는 실행 전후 `git status`와 diff를 확인하고, 결과를 자동 merge하지 않는다.

기본 Antigravity 설정은 `gemini-3.5-flash` + `high` effort를 사용한다.
현재 Ex는 IDE 창을 열지 않는 `agy.exe --print` 실행을 사용하며, model/effort가 CLI 옵션으로 노출되지 않는 환경에서는 사용자가 Antigravity CLI에 설정한 기본 모델/effort를 따른다.
이 경우 Ex는 의도한 model/effort를 프롬프트에 요청값으로 명시하고 실행 요약의 `model_source: agy-config-inherited`에 기록한다.
Antigravity runner가 exit code 0으로 종료됐더라도 stdout/stderr와 결과 파일 변경이 모두 없으면 `failed_empty_output`으로 처리한다.

## 4. Review Execution

Review Execution은 기존 `INDEPENDENT_REVIEW_PROCESS.md`의 독립 검수와 같다.
사용자-facing 용어는 `교차검증`을 우선 사용하고, 기존 `independent review`는 호환 이름으로 유지한다.

```bash
python vulcan.py review-request --gate gate2 --title "Gate 2 설계 독립 검수"
python vulcan.py agent-run --mode review --target-id RV-001 --runner codex-cli
python vulcan.py agent-run --mode review --target-id RV-001 --runner claude-cli
python vulcan.py agent-run --mode review --target-id RV-001 --runner antigravity-cli
```

Review runner는 request를 읽고 result 파일만 갱신한다.
결과는 자동 승인하지 않고 Orchestrator가 `FIND`, `CR`, `ISSUE`, 승인 후보로 다시 분류한다.
기존 `review-run` 명령은 호환 alias로 유지한다.

## 5. PR Cross Validation

PR Cross Validation은 Build runner가 만든 변경을 merge 후보로 보기 전에 작성 runner와 다른 runner가 검증하는 절차다.

PR 교차검증은 일반 Gate 산출물 검수와 다르게 다음 입력을 함께 본다.

- PR diff
- 관련 Build Wave Run
- 관련 요구사항, 설계, 테스트케이스, 개발표준
- CI 결과와 실패 로그
- 테스트 결과서와 Playwright 증적
- 추적표 delta
- PR 리뷰 코멘트와 unresolved thread

권장 분담:

| PR 작성 runner | 교차검증 runner | 중점 |
| --- | --- | --- |
| `codex-cli` Backend PR | `claude-cli` | API 계약, 보안 흐름, 예외/메시지, 테스트 누락 |
| `claude-cli` Frontend PR | `codex-cli` | UI Implementation Contract, 상태별 UI 테스트, 추적성, Playwright 증적 |
| `antigravity-cli` 작성 PR | 작성 runner가 아닌 review runner | 빠른 교차 관점 검토, 누락된 계약/증적/테스트 확인 |
| Evidence/QA PR | 작성 runner가 아닌 review runner | 증적-테스트-추적표 1:1 연결, 미실행 테스트 Pass 여부 |

PR 교차검증 결과는 자동 merge 승인이 아니다.
Orchestrator가 결과를 다시 확인하고 다음 중 하나로 확정한다.

- merge 후보
- 수정 요청 `FIND`
- 기준선 변경 `CR`
- 사용자 판단 `ISSUE`

PR 교차검증 최소 체크:

- PR scope가 Run의 writable scope와 맞는가
- 관련 ID가 변경 파일, 테스트, 증적, 추적표에 연결되어 있는가
- 필수 검증 명령과 CI가 실행되었고 exit code가 기록되어 있는가
- 화면 변경은 Playwright 증적과 UI Implementation Contract 비교가 있는가
- 설계, 보안, 데이터, 개발표준 기준을 낮추는 변경이 숨어 있지 않은가
- 리뷰 코멘트나 CI 실패가 unresolved 상태로 남아 있지 않은가

## 6. Build Execution

Build Execution은 같은 독립 실행 모델을 구현에 적용한 것이다.
프론트엔드와 백엔드는 같은 `build` persona에 속하지만, 실제 실행에서는 서로 다른 Build Wave와 runner로 나누는 것이 권장된다.

권장 기본 분담:

| 영역 | 권장 runner | 이유 |
| --- | --- | --- |
| Frontend Build Wave | `claude-cli` | 화면설계서, UI Implementation Contract, 상태별 UI 테스트를 기준으로 화면/상태 구현에 집중한다 |
| Backend Build Wave | `codex-cli` | 개발표준, 패키지 구조, API/DB/보안/테스트 계약을 기준으로 서버 구현에 집중한다 |
| Evidence / Playwright QA | `codex-cli`, `claude-cli`, `antigravity-cli` 중 안정적인 runner | 프로젝트 환경에서 Playwright 실행이 안정적인 runner를 선택한다 |
| 빠른 독립 검토 후보 | `antigravity-cli` | Gemini 기반의 추가 관점 검토가 필요한 경우 사용한다 |

중요한 점은 runner 선호가 품질 보증을 대체하지 않는다는 것이다.
프론트엔드가 Claude에서 작성되어도 Playwright 증적과 UI Contract 검수는 필요하고, 백엔드가 Codex에서 작성되어도 개발표준/보안/테스트 검수는 필요하다.

권장 흐름:

1. Orchestrator가 `implementation-plan` Run을 만든다.
2. 작업지시서가 달라지는 구현 범위는 Build Wave별 Run으로 분리한다.
3. 각 Build Wave Run에 runner, writable scope, 관련 ID, 검증 명령을 부여한다.
4. runner가 별도 세션/worktree에서 수행한다.
5. Orchestrator가 `run-integrate`로 worker worktree diff를 수집하고 Run scope 위반 여부를 판정한다.
6. scope 위반이나 충돌이 있으면 직접 수정하지 않고 재작업 Run 또는 FIND로 돌려보낸다.
7. 허용 diff만 반영한 뒤 필요한 경우 review/evidence/traceability Run을 만든다.

Worktree와 PR은 같은 것이 아니다.

- Review Execution은 보통 detached/readonly worktree에서 result 파일만 만들며 PR을 만들지 않는다.
- Build Execution은 브랜치 worktree에서 수행하는 것을 권장한다.
- Build runner 완료 후 Orchestrator가 변경 범위와 테스트를 확인한 뒤 draft PR을 만든다.
- PR이 만들어지면 작성 runner와 다른 runner가 교차검토한다.
- 예: `claude-cli`가 Frontend PR을 만들면 `codex-cli`가 설계, 테스트, traceability 관점에서 리뷰한다.
- 예: `codex-cli`가 Backend PR을 만들면 `claude-cli`, `antigravity-cli` 또는 별도 review runner가 API 계약, 보안, 테스트 증적 관점에서 리뷰한다.

초기 운영은 직렬 실행이 기본이다.
Backend Wave를 먼저 끝내고 API 계약을 고정한 뒤 Frontend Wave가 그 계약을 따라가는 방식이 충돌을 줄인다.
현재 Core 모델에서는 한 Wave를 backend/frontend runner에게 나누어 동시에 구현시키지 않는다. 병렬 구현이 필요하면 별도 fan-out 실행 모델을 정의한 뒤 적용한다.

Build Wave 또는 작업자 Run 실행 명령:

```bash
python vulcan.py agent-run --mode work --target-id RUN-010 --runner codex-cli
python vulcan.py agent-run --mode work --target-id RUN-011 --runner claude-cli
python vulcan.py agent-run --mode work --target-id RUN-012 --runner antigravity-cli
python vulcan.py agent-run --mode work --target-id RUN-010 --runner codex-cli --dry-run
python vulcan.py run-integrate --run-id RUN-010 --dry-run
python vulcan.py run-integrate --run-id RUN-010 --apply
```

`agent-run --mode work`는 한 번에 하나의 Run을 실행한다.
초기 운영은 직렬 실행이 기본이며, 현재 Core 모델에서는 Build Wave Run을 순차 실행한다.

기본 동작:

- `execution.default_worktree=true`이면 브랜치 worktree를 생성한다.
- 기본 branch 예: `codex/run-run-010-codex-cli`
- 기본 worktree 예: `.vulcan/worktrees/RUN-010-codex-cli`
- 현재 worktree에 미커밋 변경이 있으면 기본 차단한다. HEAD 기준 worktree 생성을 감수할 때만 `--allow-dirty`를 사용한다.
- runner가 만든 코드와 문서는 자동 merge하지 않는다. Orchestrator가 worktree diff, Run 문서, 검증 결과를 확인한 뒤 반영한다.
- Orchestrator는 worker 결과를 손으로 복사하지 않고 `run-integrate`로 diff를 수집한다.
- `run-integrate`는 Run의 `scope.writable`과 `scope.excluded`를 기준으로 허용/위반 파일을 분류하고, `--apply`가 있을 때만 허용 diff를 현재 worktree에 반영한다.
- `run-integrate`는 코드 수정, 테스트 작성, 추적표 보정, Gate/session 갱신을 수행하지 않는다. 실패나 누락은 재작업 worker, Review/QA worker, Traceability worker로 넘긴다.
- 실행 로그와 요약은 `docs/runs/_exec/`에 남긴다.
- 실행 시작 시 `docs/runs/_exec/<TARGET-ID>_<runner>-activity.json`에 `status: running`을 기록하고, 종료 시 `completed`, `failed`, `timeout`, `completed_no_result_change`로 갱신한다. 로컬 대시보드는 이 파일을 읽어 runner 실행 중 상태를 표시한다.
- 실행 시작 시 `docs/runs/_exec/<TARGET-ID>_<runner>-status.json`도 만든다. worker는 wall-clock 타이머를 정확히 맞추려고 하지 않고, 시작, 컨텍스트 로딩, 편집, 테스트, 결과 작성, 완료, 차단, 실패 같은 단계가 바뀔 때 이 파일의 `phase`와 `current_task`를 갱신한다.
- `current_task`는 대시보드에 한 줄로 보이는 짧은 문장이어야 한다. 너무 긴 설명, 전체 로그, 사고 과정은 기록하지 않는다.
- `activity.json.events`에는 최근 100개의 정규화된 worker 이벤트를 저장한다. 대시보드는 기본 화면에는 마지막 상태만 표시하고, worker를 클릭하면 `events` timeline 레이어를 보여준다.
- `codex-cli`는 `--json` JSONL stdout을 파싱하되, stdout 앞에 섞일 수 있는 non-JSON 경고 줄은 무시한다. `thread.started`, `turn.started`, `item.started/completed` 같은 상태 이벤트는 대시보드 `current_task`와 activity timeline으로 정규화한다.
- `claude-cli`는 `--output-format stream-json --include-partial-messages`를 파싱해 `session_id`와 부분 메시지를 수집한다.
- `antigravity-cli`/`agy.exe`는 현재 stdout 결과를 단독 신뢰하지 않고 `--log-file`을 필수로 지정해 conversation id, 모델 선택, stream 상태를 tail 하여 activity/status에 반영한다. Windows `agy.exe 1.0.3`에서는 stdout이 비어 있어도 transcript에 모델 응답이 남을 수 있으므로, result 파일 변경 여부와 log/transcript fallback을 함께 확인한다. transcript는 `transcript_full.jsonl`을 먼저 읽고, 없으면 `transcript.jsonl`을 읽어 마지막 모델 응답을 last-message로 회수한다. `--add-dir`는 절대경로를 사용한다.

Context attach 기본값:

- Antigravity runner는 `--add-dir <worktree-absolute-path>`로 작업 디렉터리를 workspace에 추가하고, 계약 문서 경로는 프롬프트 안에 명시한다.
- Review 실행은 `request.md`와 `result.md` 경로를 프롬프트 계약으로 전달한다.
- Work/Run 실행은 해당 `RUN-*.md` 경로를 프롬프트 계약으로 전달한다.
- `source_documents.read_first`, `source_documents.working_documents`, `scope.writable`은 Run/Review 문서 안의 계약으로 두고 worker가 필요할 때 읽게 한다.
- 추가 파일 attach는 특정 기준 파일을 반복적으로 놓치는 경우에만 후속 옵션으로 확장한다.

기존 `run-exec` 명령은 호환 alias로 유지한다.

## 7. 설정 방향

새 프로젝트의 `vulcan.config.json`은 독립 실행 기본값을 둘 수 있다.
`vulcan.py init`은 현재 PC에서 `codex`, `claude`, `agy` CLI 설치 여부를 확인하고, 사용 가능한 runner 목록을 설정에 기록한다.
절대 경로는 기록하지 않는다.
교차검증 가능 여부, 동시 worktree 가능 여부, persona별 runner 선택은 이 목록에서 Vulcan이 계산한다.

```json
{
  "runtime": {
    "primary": null,
    "available_runners": [
      {
        "name": "codex-cli",
        "model": "gpt-5.5",
        "effort": "high",
        "sandbox": "workspace-write",
        "version": "codex-cli 0.130.0"
      },
      {
        "name": "claude-cli",
        "model": "claude-opus-4-7",
        "effort": "high",
        "version": "2.1.142 (Claude Code)"
      },
      {
        "name": "antigravity-cli",
        "model": "gemini-3.5-flash",
        "effort": "high",
        "sandbox": "workspace-write",
        "version": "1.0.0"
      }
    ],
    "model_policy": {
      "codex-cli": {
        "enabled": true,
        "fallback": {
          "model": "gpt-5.5",
          "effort": "high"
        },
        "roles": {
          "review": {
            "model": "gpt-5.5",
            "effort": "high"
          },
          "build": {
            "model": "gpt-5.5",
            "effort": "high"
          },
          "qa-execution": {
            "model": "gpt-5.4",
            "effort": "medium"
          },
          "qa-fix-loop": {
            "model": "gpt-5.5",
            "effort": "high"
          },
          "evidence-summary": {
            "model": "gpt-5.4-mini",
            "effort": "low"
          }
        }
      }
    }
  },
  "execution": {
    "independent_enabled": true,
    "default_worktree": true,
    "default_timeout_seconds": 2400,
    "hard_timeout_seconds": 5400,
    "extension_seconds": 600,
    "max_extensions": 3,
    "progress_grace_seconds": 300,
    "progress_probe_seconds": 300,
    "no_progress_timeout_seconds": 900,
    "min_runtime_seconds": 120
  }
}
```

기존 `review.independent_*` 설정은 호환을 위해 유지하되, 장기적으로는 `execution` 아래 공통 설정으로 수렴한다.

Runner 목록 해석:

| 조건 | 운영 방식 |
| --- | --- |
| runner 0개 | 자동 독립 실행 없이 manual 검수 중심으로 운영한다 |
| runner 1개 | 같은 runner의 별도 세션/worktree로 독립검수와 동시 작업을 수행한다 |
| runner 2개 이상 | 작성 runner와 검증 runner를 분리해 Gate, PR, QA 교차검증을 수행한다 |
| `codex-cli` + `claude-cli` | Backend는 Codex, Frontend는 Claude, 검증은 작성 runner와 다른 runner를 우선한다 |
| `antigravity-cli` 포함 | Gemini 기반 추가 관점으로 Gate, PR, QA 검토 후보를 확장한다 |

예를 들어 Codex만 설치되어 있으면 교차검증은 아니지만 Codex CLI를 별도 세션/worktree로 실행해 독립검수와 동시 Build Wave를 수행할 수 있다.
Codex, Claude, Antigravity 중 둘 이상이 설치되어 있으면 Gate 2, PR, Gate 4에서 교차검증을 기본 운영 후보로 둔다.

Codex runner는 `runtime.model_policy.codex-cli`의 role 정책으로 model/effort를 동적으로 선택할 수 있다.
명시 옵션 `--model`, `--reasoning-effort`가 있으면 항상 실행 옵션이 우선한다.
명시 옵션이 없으면 `run-exec`/`agent-run --mode work`는 Run의 `skill`, `persona`, 제목, 내용을 기준으로 `build`, `build-backend`, `build-frontend`, `qa-execution`, `qa-fix-loop`, `review` 같은 role을 추론하고 해당 정책을 적용한다.
`review-run`은 기본적으로 `review` role 정책을 적용한다.

자세한 기준은 `CODEX_MODEL_POLICY.md`를 따른다.

## 8. Timeout과 runner 상태

Runner 실행은 timeout과 종료 상태를 반드시 기록한다.

기본값:

- review 실행: `review.independent_exec_timeout_seconds`, 기본 1800초
- build/evidence/qa-fix 실행: progress watchdog을 기본으로 사용한다.
- `execution.progress_probe_seconds`, 기본 300초마다 진척 snapshot을 확인한다.
- `execution.no_progress_timeout_seconds`, 기본 900초 동안 의미 있는 진척이 없으면 `no_progress_timeout`으로 종료한다.
- `execution.min_runtime_seconds`, 기본 120초 전에는 stall 종료를 적용하지 않는다.
- `execution.hard_timeout_seconds`, 기본 5400초에 도달하면 진척 신호와 무관하게 process tree를 종료한다.
- `execution.default_timeout_seconds`, `extension_seconds`, `max_extensions`는 호환 fallback 필드다. watchdog 설정이 없을 때 기존 soft timeout extension 방식으로 동작할 수 있다.
- heartbeat만으로는 진척으로 보지 않는다. worker status 변화, worktree diff 변화, 변경 파일 수 증가, 의미 있는 runner 출력 변화 중 하나 이상이 있어야 한다.

실행 기록에는 다음 필드를 남긴다.

```yaml
executed_at: "2026-05-20T22:50:00"
deadline_at: "2026-05-20T23:30:00"
completed_at: "2026-05-20T23:12:10"
duration_seconds: 1330
timeout_seconds: 2400
hard_timeout_seconds: 5400
extension_seconds: 600
max_extensions: 3
extensions_used: 1
progress_probe_seconds: 300
no_progress_timeout_seconds: 900
min_runtime_seconds: 120
watchdog_state: active
last_probe_at: "2026-05-20T22:58:10"
last_progress_at: "2026-05-20T22:58:10"
last_progress_age_seconds: 0
quiet_probe_count: 0
timeout_reason: ""
timed_out: false
status: completed
exit_code: 0
result_file_changed: true
activity: docs/runs/_exec/RV-001_codex-activity.json
status_file: docs/runs/_exec/RV-001_codex-status.json
phase: reviewing
current_task: "Gate2 상류 정합성 검토 중"
last_update: "2026-05-20T22:58:10"
resume_supported: true
thread_id: "019e..."
```

상태 해석:

| 상태 | 의미 | Orchestrator 조치 |
| --- | --- | --- |
| `completed` | runner가 정상 종료했고 결과 파일이 변경됐다 | 결과를 검토하고 반영 후보로 분류 |
| `completed_no_result_change` | runner는 정상 종료했지만 결과 파일을 쓰지 않았다 | 출력 로그를 확인하고 재실행 또는 수동 정리 |
| `failed_empty_output` | runner가 exit code 0으로 종료됐지만 stdout/stderr와 결과 변경이 모두 없다 | wrapper, 인증, 세션 문제로 보고 직접 로그 확인 또는 수동 재실행 |
| `failed` | timeout 전 비정상 종료했다 | stderr/stdout에서 인증, 토큰, 권한, 실행 오류 확인 |
| `timeout` | progress watchdog에서 장시간 진척이 없거나 hard timeout에 도달해 프로세스 트리가 종료됐다 | `timeout_reason`, `watchdog_state`, `last_progress_at`, 부분 로그, worktree diff를 확인하고 Run 분리, 재개, 재실행, 정책 조정 중 하나를 선택 |

토큰 소진 여부는 모든 runner가 표준화해서 알려주지 않는다.
따라서 Vulcan은 토큰 소진을 직접 판정하지 않고, exit code, stderr/stdout, 마지막 응답, 결과 파일 변경 여부로 비정상 종료를 판단한다.
runner가 토큰 또는 사용량 한도 때문에 종료하면 보통 `failed`나 `completed_no_result_change`로 남고, Orchestrator가 로그에서 원인을 확인한다.

장시간 build/evidence 실행은 progress watchdog과 hard timeout을 분리해서 판정한다.
watchdog은 `execution.progress_probe_seconds`마다 진척 snapshot을 캡처하고, 마지막 의미 있는 진척 이후 시간이 `execution.no_progress_timeout_seconds`를 넘으면 `stalled`로 종료한다.
진척 신호는 다음 항목을 함께 본다.

- worker status 파일의 `phase`, `status`, `current_task` 같은 비-heartbeat 상태 변화
- worktree의 git status/diff fingerprint 변화
- 변경 파일 수 증가
- runner stdout/stderr/log 증가. 단, 출력 증가만 있고 상태나 diff가 없으면 보조 신호로만 취급한다.

heartbeat 파일 수정시각만으로는 진척으로 보지 않는다.
`execution.hard_timeout_seconds`에 도달하면 진척 신호가 있어도 프로세스 트리를 종료하고 `timeout`으로 기록한다.
worker가 `running` 상태인데 status 파일이 오래 갱신되지 않으면 `stale`로 보고 로그, 마지막 메시지, worktree diff를 확인한다.

watchdog probe가 발생하면 `summary.json`, `activity.json`, Run Execution Record에 다음 정보를 남긴다.

```yaml
timeout_policy:
  watchdog_enabled: true
  progress_probe_seconds: 300
  no_progress_timeout_seconds: 900
  min_runtime_seconds: 120
  hard_timeout_seconds: 5400
  watchdog_state: active
  last_probe_at: "2026-05-30T12:10:00"
  last_progress_at: "2026-05-30T12:10:00"
  last_progress_age_seconds: 0
  quiet_probe_count: 0
  watchdog_events:
    - probe_at: "2026-05-30T12:10:00"
      state: active
      reasons:
        - "worktree diff changed"
        - "runner output/log advanced during active phase"
timeout_reason: ""
```

## 8.1 Worker Heartbeat와 Resume

Worker heartbeat는 작업 로그가 아니라 상태 신호다.

```json
{
  "target_type": "review",
  "target_id": "RV-001",
  "runner": "codex-cli",
  "status": "running",
  "phase": "reviewing",
  "current_task": "Gate2 상류 정합성 검토 중",
  "last_update": "2026-05-20T22:58:10"
}
```

규칙:

- worker는 정확한 분 단위 타이머를 가진 존재로 가정하지 않는다.
- worker는 단계가 바뀔 때 status 파일을 갱신한다.
- Orchestrator는 `last_update`보다 OS 파일 수정시각을 더 신뢰한다.
- 대시보드는 `current_task` 한 줄과 신호등 상태만 보여준다.
- `status: running`인데 status 파일이 오래 갱신되지 않으면 stale로 본다.
- `result_file_changed=false` 또는 `run_file_changed=false`이면 exit code 0이어도 성공으로 보지 않는다.

Resume 가능한 runner는 같은 실행 세션을 1회 회수할 수 있다.

| Runner | Resume 기준 |
| --- | --- |
| `codex-cli` | `codex exec resume <thread_id> "<prompt>"` |
| `claude-cli` | `claude --resume <session_id> -p "<prompt>"` 또는 `claude --continue -p "<prompt>"` |

대시보드 상태를 남기려면 원시 CLI 명령을 직접 실행하지 않고 다음 프레임워크 명령을 사용한다.

```powershell
python vulcan.py agent-resume --target-id RV-001 --runner codex-cli
python vulcan.py agent-resume --target-id RUN-010 --runner claude-cli --prompt "이전 작업을 계속 진행하고 Run 문서를 갱신해줘"
```

`agent-resume`은 기존 `activity.json`에서 `thread_id` 또는 `session_id`를 읽고, resume 실행 전에 activity/status를 `running`으로 갱신한다.
따라서 로컬 대시보드는 resume 중인 worker도 진행 작업으로 표시할 수 있다.

Orchestrator는 다음 조건에서만 resume을 사용한다.

- 이전 실행이 준비 응답, 무변경, 결과 파일 미갱신, 부분 종료로 끝났다.
- `activity.json`에 `thread_id` 또는 `session_id` 같은 resume 식별자가 남아 있다.
- worktree와 Run/Review 파일이 아직 삭제되지 않았다.
- resume은 기존 실행을 회수하기 위한 1회 재지시로 제한한다.

resume 후에도 결과 파일 또는 Run 문서가 갱신되지 않으면 `invalid runner result`로 보고 재실행, 다른 runner 교차검증, 수동 정리 중 하나를 선택한다.

## 9. Orchestrator 책임

Orchestrator는 runner보다 상위에 있다.

- Run 생성
- runner 선택
- worktree 생성 여부 결정
- 결과 회수
- 테스트/증적 재검증
- FIND/CR/ISSUE 분류
- 본선 산출물 반영 판단
- 사용자 승인 질문

Runner가 아무리 강해도 Orchestrator의 Gate 판단과 Human approval을 대체하지 않는다.
