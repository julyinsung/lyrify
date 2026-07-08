# Codex/GPT Adapter

> 상태: v0.4.7
> 목적: Vulcan-Anvil Ex Core 산출물과 Agent Run Protocol을 Codex/GPT 기반 개발 실행 흐름에 연결한다.

## 1. 범위

Codex/GPT Adapter는 공통 Run Input Contract를 Codex/GPT 계열 runner 호출, 실행 지침, 출력 정규화 방식으로 변환한다.

이 Adapter는 다음 작업을 우선 지원한다.

- 요구사항/설계 문서 읽기
- Gate별 작업 범위 선정
- 구현 및 테스트 실행
- 화면 캡처와 결과 증적 생성
- 요구사항추적표 갱신
- 다음 Run 제안

## 2. 현재 적용 범위

`0.4.7` 기준 Codex/GPT Adapter는 새 프로젝트에 주입되는 `AGENTS.md`, `.agents/skills/`, `.codex/agents/`, `docs/core/`, `docs/adapters/codex-gpt/skills/`를 통해 다음 흐름을 지원한다.

- 새 프로젝트 컨시어지 응답
- Phase 0부터 Gate 5까지의 단계 판단
- 요구사항, 설계, 보안, 데이터, 테스트, 변경관리 문서 작성
- Build Wave 기반 구현 계획과 Wave별 작업지시
- `workflow.integration_branch` 기준 구현 통합 브랜치와 worker 실행
- Gate 4 `qa-execution`과 `QA-000` workspace 재사용
- Run 문서 작성과 `vulcan.py` 기반 검증
- Dashboard가 읽는 `session.json`, Run, 문서 상태 갱신

## 3. Codex/GPT 실행 특징

Codex/GPT Adapter는 다음 특징을 고려한다.

- Codex/GPT 런타임의 기본 진입 문서는 루트 `AGENTS.md`다.
- Codex repo-local skill은 `.agents/skills/*/SKILL.md`에 두며, 작업이 skill description과 맞을 때 Codex가 읽는 절차 카드다.
- Codex custom agent는 `.codex/agents/*.toml`에 두며, 메인 Orchestrator가 명시적으로 호출하는 읽기 중심 보조 에이전트 정의다.
- Codex custom agent는 `.codex/agents/*.toml`의 `name`으로 식별된다. Orchestrator는 프롬프트에서 custom agent 이름을 명시해 사용을 요청한다.
- 현재 surface의 내부 tool schema가 `agent_type` 같은 필드를 노출한다고 가정하지 않는다. Codex가 custom agent를 선택하지 못하면, Orchestrator는 built-in/default subagent에 custom agent TOML 내용을 prompt 계약으로 주입할 수 있다. 이때 model/effort는 자동 적용으로 보고하지 않는다.
- `AGENTS.md`는 세부 규칙을 중복하지 않고 `docs/core/`와 `docs/adapters/codex-gpt/`를 참조한다.
- 공통 Gate 실행 기준은 `docs/core/GATE_EXECUTION_CHECKLIST.md`를 따른다. Codex/GPT runner만 추가로 `docs/adapters/codex-gpt/GATE_PROMPTS.md`를 읽는다.
- Claude, Gemini, Antigravity Run 입력에는 Codex 전용 `GATE_PROMPTS.md`를 주입하지 않는다.
- Claude 전용 `.claude/CLAUDE.md`, `.claude/agents/`, `.claude/skills/`는 같은 저장소에 공존할 수 있으나 Codex/GPT의 기본 실행 계약은 아니다.
- 파일 읽기와 수정, 테스트 실행을 한 흐름에서 처리할 수 있다.
- 산출물과 코드가 같은 워크스페이스에 있을 때 추적표 갱신까지 이어가기 좋다.
- 컨텍스트가 길어지면 Run Scope를 좁혀야 한다.
- 프로젝트 주입 표준(`docs/seed-docs/reference-standards/`)은 읽기 전용 기준 문서로 사용할 수 있다.
- 민감 참고문서(`docs/ref-docs/`)는 기본적으로 제외해야 한다.
- 테스트와 캡처는 결과 문서 및 증적 경로로 남겨야 한다.

## 4. 기본 실행 순서

```text
1. `docs/core/RUN_INPUT_CONTRACT.md` 형식의 Run 입력 확인
2. Codex/GPT runner에 맞는 프롬프트와 실행 옵션 구성
3. 관련 문서와 scope를 runner에게 전달
4. runner 실행 로그, 상태, 마지막 메시지 수집
5. Run 출력 정리
```

## 5. 다음 작성 대상

본 Adapter는 다음 문서를 기준으로 구체화한다.

- `docs/core/RUN_INPUT_CONTRACT.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`
- `GATE_PROMPTS.md`
- `LIMITATIONS.md`

## 6. 현재 사용 가능한 문서

| 문서 | 용도 |
| --- | --- |
| `PERSONA_DELEGATION.md` | Codex/GPT subagent 위임과 persona 적용 규칙 |
| `GATE_PROMPTS.md` | Gate별 기본 프롬프트 |
| `LIMITATIONS.md` | Codex/GPT Adapter 한계와 승인 필요 상황 |
| `.agents/skills/` | Codex 런타임이 발견할 수 있는 repo-local skill |
| `.codex/agents/` | 메인 Orchestrator가 호출할 수 있는 Codex custom agent 정의 |
| `skills/` | Run 문서와 adapter가 참조하는 내부 작업 절차 카드 |

Run 입력/출력 형식은 adapter별로 정의하지 않는다.
Codex, Claude, Gemini worker는 모두 `docs/core/RUN_INPUT_CONTRACT.md`, `docs/core/RUN_OUTPUT_CONTRACT.md`를 동일하게 사용한다.
단, Run 입력의 `source_documents.read_first`는 adapter별로 다르다.

| Runner | 공통 문서 | 추가 adapter 문서 |
| --- | --- | --- |
| Codex/GPT | `docs/core/GATE_EXECUTION_CHECKLIST.md` | `docs/adapters/codex-gpt/GATE_PROMPTS.md` |
| Claude | `docs/core/GATE_EXECUTION_CHECKLIST.md` | `docs/adapters/claude/GATE_PROMPTS.md` |
| Gemini/Antigravity | `docs/core/GATE_EXECUTION_CHECKLIST.md` | `docs/adapters/gemini/GATE_PROMPTS_GEMINI.md` |

## 7. Skill 카드

Codex/GPT Adapter에는 두 종류의 skill 카드가 있다.

Repo-local Codex skill:

| 상황 | Repo-local Skill |
| --- | --- |
| Gate/Run/worker/승인 라우팅 | `.agents/skills/vulcan-orchestrator/SKILL.md` |
| Gate 2 설계 | `.agents/skills/vulcan-design/SKILL.md` |
| Impl Build Wave | `.agents/skills/vulcan-impl-wave/SKILL.md` |
| Gate 4 QA | `.agents/skills/vulcan-qa/SKILL.md` |
| Gate 5 릴리즈 | `.agents/skills/vulcan-release/SKILL.md` |

Codex custom agent:

| 상황 | Agent |
| --- | --- |
| 관련 ID/source document 후보 탐색 | `.codex/agents/trace-scout.toml` |
| Run 입력 계약 검토 | `.codex/agents/run-drafter.toml` |
| Program/API/DB/UI 계약 정합성 검토 | `.codex/agents/contract-reviewer.toml` |
| QA 로그/증적 해석 | `.codex/agents/qa-reader.toml` |

Adapter 내부 작업 카드:

| 상황 | Skill |
| --- | --- |
| 표준 persona Run | `persona-run` (`docs/core/AGENT_RUN_PROTOCOL.md`) |
| 추적성 검토 | `skills/traceability-review.md` |
| 보안 검토 | `skills/security-review.md` |
| 표준용어/DB명세 검토 | `skills/data-standard-review.md` |
| Gate 4 QA 실행/증적 수집 | `skills/qa-execution.md` |
| QA 결함 수정 루프 | `skills/qa-fix-loop.md` |
| 변경요청 영향도 분석 | `skills/change-impact-analysis.md` |

## 8. 0.4.7 이후 검증 작업

다음 단계에서는 실제 생성 프로젝트를 기준으로 Codex와 Claude의 Run 결과를 비교한다.

- 같은 요구사항을 Codex와 Claude에서 각각 Gate 1~5로 진행
- 생성 문서, Run, 추적표, 테스트 증적의 차이 확인
- 과도한 문서화와 누락 검출 기준 조정
- Dashboard A2에서 Gate별 상태와 검수 결과가 충분히 읽히는지 확인
- staged QA와 `qa-fix-loop` 분리가 실제 프로젝트에서 과도하게 느려지지 않는지 확인
