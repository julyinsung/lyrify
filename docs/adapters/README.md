# Vulcan-Anvil Ex Adapters

이 디렉터리는 Vulcan-Anvil Ex Core 규칙을 Codex, Claude 같은 실제 실행 환경에 연결하는 얇은 변환층이다.

## 1. 원칙

Core는 두껍게 유지하고 Adapter는 얇게 유지한다.

- Core는 Gate, Run, traceability, approval, security, data, development standard, independent execution 같은 모델 독립 규칙을 가진다.
- Adapter는 특정 runner가 Core 입력 계약을 읽고 실행할 수 있도록 프롬프트, 명령 옵션, 로그, 상태파일, 출력 정규화만 변환한다.
- Adapter는 Core 규칙을 길게 복사하지 않는다.
- Core와 Adapter의 내용이 충돌하면 Core가 우선이다.
- 공통 Gate 실행 기준은 `docs/core/GATE_EXECUTION_CHECKLIST.md`에 둔다. Adapter별 `GATE_PROMPTS`는 이 기준을 runner에 맞게 얇게 환기하는 문서다.

## 2. Adapter가 해야 하는 일

Adapter는 다음 질문에만 답한다.

- 이 runner에게 공통 Run 입력 계약과 Core 문서를 어떤 순서로 제공할 것인가?
- runner별 프롬프트 또는 CLI 옵션은 무엇인가?
- runner 결과를 Core Run 출력 계약으로 어떻게 정규화할 것인가?
- runner 한계, 권한, 컨텍스트 제한은 무엇인가?
- 실패, 질문, 승인요청을 어떤 파일과 필드에 남길 것인가?

## 3. Adapter가 피해야 하는 일

다음 내용은 Adapter가 아니라 Core에 둔다.

- Gate 전환과 사용자 승인 정책
- Run lifecycle과 Build Wave 운영 원칙
- FIND, CR, ISSUE, Backlog 분류 규칙
- UI Implementation Contract 원칙
- Playwright 증적 필수 기준
- 보안, 데이터, 개발표준의 공통 기준선
- 독립 실행, worktree, PR, 교차검토의 공통 절차

Adapter에 이런 내용이 필요하면 요약만 두고 Core 문서를 링크한다.

## 4. 현재 Adapter

| Adapter | 목적 |
| --- | --- |
| `codex-gpt/` | Codex/GPT 실행 환경에서 사용할 runner 호출 지침, Gate prompt, skill 카드 |
| `claude/` | Claude CLI, Claude subagent, Claude 프로젝트 파일과 Ex persona의 매핑 |
| `gemini/` | Gemini/Antigravity 계열 runner 호출 지침. 필요 시 추가 |

## 5. 최소 산출물

각 Adapter는 다음 문서를 가진다. Run 입력/출력 형식은 adapter별로 두지 않고 `docs/core/RUN_INPUT_CONTRACT.md`, `docs/core/RUN_OUTPUT_CONTRACT.md`를 사용한다.

| 문서 | 목적 |
| --- | --- |
| `README.md` | Adapter의 범위와 사용 방식 |
| `GATE_PROMPTS.md` | Core 규칙을 짧게 환기하는 runner별 실행 프롬프트 |
| `PERSONA_MAPPING.md` 또는 `PERSONA_DELEGATION.md` | Core persona와 runner별 agent/subagent 이름의 매핑 |
| `LIMITATIONS.md` | runner 한계, 보안 주의사항, 보조 도구 기준 |

Run 입력의 `source_documents.read_first`는 공통 체크리스트와 해당 runner adapter 문서만 포함한다.

| Runner | 추가 adapter prompt |
| --- | --- |
| Codex/GPT | `docs/adapters/codex-gpt/GATE_PROMPTS.md` |
| Claude | `docs/adapters/claude/GATE_PROMPTS.md` |
| Gemini/Antigravity | `docs/adapters/gemini/GATE_PROMPTS_GEMINI.md` |

## 6. 관련 Core 문서

- `docs/core/ORCHESTRATOR_PROTOCOL.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/GATE_EXECUTION_CHECKLIST.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/RUN_INPUT_CONTRACT.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/INDEPENDENT_EXECUTION_PROCESS.md`
- `docs/core/CHANGE_CONTROL_PROCESS.md`
