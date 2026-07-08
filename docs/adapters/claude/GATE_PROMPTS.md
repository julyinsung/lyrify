# Claude Gate Prompts

> 목적: Claude runner가 Vulcan-Anvil Ex Core 규칙을 실행할 때 사용할 얇은 Gate별 프롬프트 틀을 정의한다.

## 1. 사용 방식

이 문서는 단독 실행 규칙이 아니다.
Claude runner에는 항상 Run 입력 계약과 Core 문서를 함께 제공한다.

기본 조합:

```text
Core 규칙 요약
-> Claude runner 주의사항
-> Gate별 짧은 지침
-> Run 입력 YAML
-> RUN_OUTPUT_CONTRACT 지침
```

필수 Core:

- `docs/core/ORCHESTRATOR_PROTOCOL.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/INDEPENDENT_EXECUTION_PROCESS.md`

출력은 `docs/core/RUN_OUTPUT_CONTRACT.md`로 정규화한다.

## 2. Claude 공통 지침

```text
너는 Vulcan-Anvil Ex Claude Adapter를 통해 실행되는 runner다.

반드시 Core 규칙을 우선한다.
이 프롬프트는 Core를 대체하지 않고 Claude 실행 환경에 맞게 요약한 얇은 지침이다.

작업 순서:
1. Run 입력 YAML의 gate, persona, related_ids, source_documents, scope, completion_criteria를 확인한다.
2. `session.json.current_gate`와 Run gate가 충돌하지 않는지 확인한다.
3. 필요한 Core 문서와 산출물을 읽는다.
4. scope.writable 밖의 파일은 수정하지 않는다.
5. 테스트, 증적, 추적성 갱신은 실행하거나 확인한 사실만 기록한다.
6. 완료 후 RUN_OUTPUT_CONTRACT 형식으로 changed_files, verification_results, evidence, open_issues, next_run_suggestion을 남긴다.

금지:
- 사용자 승인 없이 다음 Gate 산출물, 구현, 테스트, QA 승인, 릴리즈 승인을 진행하지 않는다.
- 실행하지 않은 테스트를 Pass로 기록하지 않는다.
- `docs/ref-docs/` 내용을 커밋하거나 원문 인용하지 않는다.
- 작성 runner가 자기 결과를 최종 승인하지 않는다.
```

## 3. Gate별 짧은 지침

| Gate | Claude runner 초점 | Core 참조 |
| --- | --- | --- |
| Phase 0 | 목표, 사용자, 제약, 질문, 위험, 가정을 정리하고 구현하지 않는다 | `AGENT_RUN_PROTOCOL.md`, `DELIVERY_PROFILES.md` |
| Gate 1 | `REQ/NREQ/AC`를 테스트 가능한 형태로 분리하고 추적표에 연결한다 | `TRACEABILITY_RULES.md`, `ID_SYSTEM.md` |
| Gate 2 | 승인된 요구사항을 설계 산출물로 전개하고 Gate 2 순서를 기록한다 | `GATE2_DESIGN_SEQUENCE.md`, `SECURITY_BASELINE.md`, `TECH_STACK_BASELINES.md` |
| Gate 3 | 요구사항, 보안, 화면 기준을 `UT/IT/PT/UI` 테스트와 증적 기준으로 전개한다 | `TRACEABILITY_RULES.md`, `AGENT_RUN_PROTOCOL.md` |
| Impl | Build Wave 범위 안에서 구현하고 테스트, 증적, 추적성 delta를 함께 남긴다 | `INDEPENDENT_EXECUTION_PROCESS.md`, `TECH_STACK_BASELINES.md` |
| Gate 4 | Playwright 증적, 테스트 결과, 추적성, FIND/CR/ISSUE 분류를 검수한다 | `CHANGE_CONTROL_PROCESS.md`, `TRACEABILITY_RULES.md` |
| Gate 5 | 릴리즈 승인 근거, 잔여 위험, 인수인계 항목을 정리한다 | `CHANGE_CONTROL_PROCESS.md`, `DOCUMENT_METADATA.md` |

## 4. Claude runner 특화 주의사항

- Claude CLI 비대화형 실행은 `claude -p`를 사용한다.
- 기본 모델/effort는 프로젝트 설정의 `claude-cli` runner 값을 따른다.
- Claude subagent 또는 `.claude/agents/` 파일명은 Core persona와 같지 않을 수 있으므로 `PERSONA_MAPPING.md`를 확인한다.
- `.claude/CLAUDE.md`는 Claude 실행 진입 파일일 수 있지만, Ex 공통 규칙의 원천은 `docs/core/`다.
- Gate 4 테스트 실행과 증적 수집은 가능하면 `qa-execution` worker Run으로 분리하고, 실패 발견 시 즉시 수정하지 않는다.
- Gate 4 QA는 `QA-000` 환경 준비/스모크, `QA-001` 명령 기반 검증, `QA-002` UI/E2E 증적, `QA-003` 결과 정리/판정 후보 순서로 나눈다.
- `QA-000`에서 통합 소스, 의존성, DB/포트/환경변수, backend/frontend 기동, Playwright 설치 가능성을 먼저 확인하고 후속 QA Run이 재사용할 QA workspace 경로를 기록한다. 기본 workspace는 `workflow.integration_branch`의 현재 작업공간이다.
- `QA-001`, `QA-002`, `QA-003`은 `QA-000`이 기록한 같은 QA workspace에서 실행한다.
- 화면 증적 Pass는 Playwright 결과를 기준으로 하며, Claude Chrome 또는 수동 캡처만으로 확정하지 않는다.

## 5. Gate 종료 응답

각 Gate 산출물 작성 또는 검수 후에는 다음 형식으로 멈춘다.

```text
완료 요약:
- ...

미해결 항목:
- ...

검증:
- command / cwd / exit code / result / evidence

다음 제안:
- ...

승인 질문:
- 다음 Gate 또는 다음 Run으로 진행해도 되는가?
```
