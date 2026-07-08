# Codex/GPT Persona Delegation

> 상태: 초안 v0.1
> 목적: Codex/GPT 런타임에서 메인 에이전트가 persona 기반 subagent 작업을 위임하는 방식을 정의한다.

## 1. 개념

Codex/GPT Adapter에서 persona는 subagent 이름이 아니라 작업 계약이다.

Codex 런타임이 subagent를 지원하면 메인 에이전트는 `docs/core/AGENT_PERSONAS.md`의 persona를 기준으로 작업을 나누어 위임한다. subagent 기능이 없거나 사용할 수 없는 환경에서는 메인 에이전트가 같은 persona 계약을 직접 수행한다.

## 2. 위임 우선순위

메인 에이전트는 다음 순서로 판단한다.

1. Run 입력의 `persona`를 확인한다.
2. `docs/core/AGENT_PERSONAS.md`에서 persona의 책임과 금지사항을 확인한다.
3. `docs/adapters/codex-gpt/skills/`에서 필요한 skill 카드를 추가로 확인한다.
4. 수정 범위가 겹치지 않는 경우에만 subagent 병렬 실행을 고려한다.
5. subagent 결과는 반드시 Run 출력 계약으로 정규화한다.
6. Codex thread/subagent를 사용했으면 외부 CLI runner의 `Run Execution Record`가 없더라도 현재 Run에 `delegation_records`를 남긴다.

## 3. 권장 위임 패턴

| 상황 | 권장 persona | 위임 방식 |
| --- | --- | --- |
| 요구사항 초안 작성 | `requirements` | 단일 subagent 또는 메인 에이전트 직접 수행 |
| 기능/프로그램/DB/화면 설계 | `design` | 기능 단위로 나누어 순차 실행 |
| 구현 | `build` | 파일 소유권이 분리될 때만 병렬 실행 |
| 화면 캡처/테스트 증적 | `evidence` | 구현 완료 후 별도 Run으로 실행 |
| 보안/추적성/품질 검토 | `review` | 구현과 분리된 읽기 중심 Run으로 실행 |
| QA 결함 수정 | `build` + `review` | build가 수정하고 review가 재검증 |
| 변경요청 영향도 분석 | `change-control` | 먼저 분석 후 필요한 Gate persona로 진행 |

## 4. Codex subagent 전달문 기본형

```text
너는 Vulcan-Anvil Ex의 `{persona}` persona로 동작한다.

반드시 먼저 읽을 문서:
- AGENTS.md
- docs/core/AGENT_PERSONAS.md
- docs/core/AGENT_RUN_PROTOCOL.md
- docs/core/TRACEABILITY_RULES.md
- docs/core/RUN_INPUT_CONTRACT.md
- docs/core/RUN_OUTPUT_CONTRACT.md

이번 Run:
<RUN_INPUT_YAML>

규칙:
- scope.writable 안의 파일만 수정한다.
- related_ids와 무관한 변경은 하지 않는다.
- 검증하지 않은 결과를 통과로 보고하지 않는다.
- 완료 시 변경 파일, 검증 결과, 증적, 미해결 이슈, Orchestrator가 `delegation_records`에 기록할 위임 결과 요약을 반환한다.
```

## 5. 병렬 위임 제한

다음 경우에는 병렬 subagent 실행을 피한다.

- 같은 파일을 둘 이상의 persona가 수정해야 한다.
- 요구사항 또는 설계가 아직 승인되지 않았다.
- 보안 기준을 낮추는 판단이 필요하다.
- DB 스키마와 프로그램 구현이 동시에 바뀌어 순서 의존성이 크다.
- 테스트 실패 원인이 요구사항 변경인지 구현 결함인지 불명확하다.

## 6. 결과 수집

메인 에이전트는 subagent 결과를 그대로 최종 답변으로 사용하지 않는다.

반드시 다음을 수행한다.

1. 변경 파일과 관련 ID를 대조한다.
2. 검증 command와 결과가 있는지 확인한다.
3. 증적 경로가 실제로 존재하는지 확인한다.
4. 필요한 경우 `vulcan.py run-check`로 Run 문서를 검사한다.
5. 미해결 이슈가 있으면 `FIND`, `CR`, `ISSUE` 중 하나로 분류한다.
6. subagent/thread의 작업 범위, 변경 파일, 결과 요약, Orchestrator 재검증 명령을 현재 Run의 `delegation_records`로 기록한다.

외부 CLI runner를 사용한 경우에는 `docs/runs/_exec/` 로그, stdout/stderr, timeout/watchdog, worktree/branch 같은 상세 실행 기록을 함께 남길 수 있다. Codex native subagent나 thread 위임은 같은 프로세스 수준 메타가 없을 수 있으므로, `delegation_records`를 최소 책임 추적 단위로 사용한다.

