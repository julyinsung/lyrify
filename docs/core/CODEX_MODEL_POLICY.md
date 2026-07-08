# Codex Model Policy

> Status: draft v0.1
> Scope: `codex-cli` runner only

## 1. 목적

Vulcan-Anvil Ex는 초기 audit workflow에서 Codex runner를 보수적으로 `gpt-5.5` + `high` reasoning effort로 사용했다.
이 기본값은 설계 정합성, QA 판단, 릴리즈 전 검수에는 안전하지만 모든 worker 작업에 쓰기에는 시간이 오래 걸리고 비용도 커질 수 있다.

이 문서는 Codex runner의 작업 성격별 model/effort 선택 기준을 정의한다.
목표는 별도 벤치마크 프로젝트를 만들지 않고, 실제 Run 실행 기록을 누적해 점진적으로 정책을 조정하는 것이다.

Claude CLI와 Antigravity/Gemini runner는 이 문서의 적용 대상이 아니다.

## 2. 기본 원칙

- 명시 옵션이 항상 우선한다.
  - `--model`
  - `--reasoning-effort`
- 명시 옵션이 없으면 `vulcan.config.json.runtime.model_policy.codex-cli.roles`를 따른다.
- 역할별 정책이 없으면 `runtime.model_policy.codex-cli.fallback`을 따른다.
- fallback도 없으면 runner 기본값 `gpt-5.5` + `high`를 사용한다.
- 지원되지 않는 Codex model alias는 worker 실행 전에 compatibility fallback으로 정규화한다.
- 최종 실행 기록에는 실제 model, reasoning effort, model source, effort source, model policy role, model fallback reason을 남긴다.
- 품질 판단이 필요한 작업은 계속 강한 모델/높은 effort를 사용한다.
- 로그 요약, 증적 index, Run 초안 같은 정리 작업은 낮은 모델/effort를 우선 사용한다.

## 3. 권장 역할 정책

| Role | Model | Effort | 용도 |
| --- | --- | --- | --- |
| `review` | `gpt-5.5` | `high` | 독립 검수, 설계/QA 정합성 검토 |
| `critical_judgment` | `gpt-5.5` | `high` | Gate 승인 후보, FIND/CR 분류, 릴리즈 판단 후보 |
| `build` | `gpt-5.5` | `high` | 일반 구현 worker |
| `build-backend` | `gpt-5.5` | `high` | Backend/API/DB 구현 worker |
| `build-frontend` | `gpt-5.5` | `high` | Frontend/UI 구현 worker |
| `qa-execution` | `gpt-5.4` | `medium` | QA 명령 실행, 로그 수집, 결과 정리 |
| `qa-fix-loop` | `gpt-5.5` | `high` | 승인된 FIND 범위 안의 QA 수정 worker |
| `run-draft` | `gpt-5.4-mini` | `medium` | Run 초안, trace-context 후보, 문서 정리 |
| `evidence-summary` | `gpt-5.4-mini` | `low` | 로그/증적 index, 단순 요약 |

이 표는 성능 개선을 위한 시작점이다.
정답으로 고정하지 않고 실제 sample Run에서 duration, 실패율, Orchestrator 보정량을 보고 조정한다.

## 3.1 Codex Custom Agent 권장값

`.codex/agents/*.toml`에 정의하는 custom agent는 역할별로 model/effort를 직접 명시한다.
이 값은 `agent-run/run-exec`의 runner 정책이 아니라 Codex subagent 정의에 적용되는 값이다.

| Custom Agent | Model | Effort | 이유 |
| --- | --- | --- | --- |
| `trace-scout` | `gpt-5.5` | `medium` | 빠른 관련 ID/source document 탐색 |
| `run-drafter` | `gpt-5.5` | `medium` | Run 작업지시서 누락/과다 범위 검토 |
| `contract-reviewer` | `gpt-5.5` | `high` | 설계/구현 계약 누락과 CR 후보 판단 |
| `qa-reader` | `gpt-5.5` | `medium` | QA 로그 원인 분류와 FIND/CR/ISSUE 후보 판단 |

custom agent도 정답으로 고정하지 않는다.
실제 샘플 프로젝트에서 소요 시간, 유효 지적 수, 잘못 짚은 지적 수, Orchestrator 보정량을 보고 조정한다.

## 4. 설정 예시

```json
{
  "runtime": {
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
          "evidence-summary": {
            "model": "gpt-5.4-mini",
            "effort": "low"
          }
        }
      }
    }
  }
}
```

## 5. 실행 기록

`agent-run --mode work`, `run-exec`, `review-run`은 Codex runner 실행 기록에 다음 값을 남긴다.

```yaml
model: gpt-5.5
reasoning_effort: high
model_source: codex-model-policy:build-backend
effort_source: codex-model-policy:build-backend
model_policy_role: build-backend
model_fallback_reason: ""
```

명시 옵션을 사용하면 source는 `cli-argument`가 된다.

```powershell
python vulcan.py agent-run --mode work --run-id RUN-012 --runner codex-cli --model gpt-5.5 --reasoning-effort high
```

## 5.1 Compatibility fallback

역할 정책이나 CLI 명시 옵션이 현재 Codex CLI 계정에서 지원되지 않는 model alias를 가리키면, Ex는 실행 전에 지원되는 fallback model로 바꾼다.

현재 compatibility fallback:

| Requested model | Actual model | 사유 |
| --- | --- | --- |
| `gpt-5.3-codex` | `gpt-5.5` | 현재 Codex CLI 계정에서 지원되지 않는 경우가 있어 실행 전 호환 모델로 정규화 |

fallback이 발생하면 실행 기록의 `model_source`에는 `compat-fallback:<requested-model>`이 붙고, `model_fallback_reason`에 사람이 읽을 수 있는 이유가 남는다.

예:

```yaml
model: gpt-5.5
reasoning_effort: high
model_source: codex-model-policy:build|compat-fallback:gpt-5.3-codex
effort_source: codex-model-policy:build
model_policy_role: build
model_fallback_reason: gpt-5.3-codex is not supported by the current Codex CLI account; using gpt-5.5
```

이 fallback은 품질 downgrade 정책이 아니라 실행 호환성 회복 장치다.
모델 정책 자체를 조정하려면 `vulcan.config.json.runtime.model_policy` 또는 이 문서의 권장 역할 정책을 변경한다.

## 6. 성능 측정 방향

모델별 성능을 별도 실험으로 크게 돌리지 않는다.
실제 Run 실행 기록을 누적해 다음 항목을 비교한다.

- role
- model
- reasoning_effort
- duration_seconds
- exit_code
- timed_out
- run_file_changed 또는 result_file_changed
- changed_files
- run-check/check-trace/check-contract 결과
- Orchestrator 보정 필요 여부

향후 `perf-report`가 안정되면 role/model/effort별 평균 실행 시간과 실패 경향을 집계한다.

## 7. 주의사항

- `qa-execution`은 실패를 수정하지 않는다. 낮춘 effort로 실행하더라도 FIND/CR 최종 분류는 Orchestrator 또는 강한 review가 확인한다.
- `build`와 `qa-fix-loop`는 코드 변경을 만들 수 있으므로 `mini` 계열을 기본값으로 두지 않는다.
- `critical_judgment`는 자동 실행 role이라기보다 Orchestrator가 중요한 판단을 별도 runner에게 맡길 때 사용하는 정책 이름이다.
- 프로젝트가 감리 또는 보안 민감도가 높으면 모든 role을 일시적으로 `gpt-5.5` + `high`로 되돌릴 수 있다.
