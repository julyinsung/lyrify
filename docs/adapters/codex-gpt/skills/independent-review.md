# Independent Review Skill

## 사용할 때

Gate 종료 전, 작성 세션과 분리된 독립 검수가 필요할 때 사용한다.

특히 다음 상황에서 사용한다.

- Gate 2 설계 산출물이 충분히 구체적인지 독립 검토할 때
- Gate 4 테스트 결과와 화면 증적이 실제 기대 결과와 맞는지 확인할 때
- 메인 에이전트가 작성한 산출물을 같은 Codex라도 별도 세션에서 다시 볼 때
- Claude 또는 다른 런타임의 결과를 Codex 관점에서 재검토할 때

## 필수 입력

- `docs/core/INDEPENDENT_REVIEW_PROCESS.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/RUN_INPUT_CONTRACT.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`
- 리뷰 요청 파일: `docs/reviews/RV-*_request.md`
- 리뷰 대상 Gate 산출물과 관련 Run

## 절차

1. request 파일의 `review_id`, `gate`, `source_run`, `related_ids`, `result_file`을 확인한다.
2. `session.json.current_gate`와 request의 `gate`가 충돌하지 않는지 확인한다.
3. request의 `upstream_review_required` 또는 `상류 정합성` 지시가 있으면 Phase 0부터 현재 Gate까지 순서대로 읽는다.
4. 리뷰 대상 산출물과 Run 결과를 읽는다.
5. Gate별 중점 검토 항목을 적용한다.
6. 산출물을 직접 수정하지 않고 result 파일에만 결과를 작성한다.
7. 발견사항을 `PASS`, `FIND`, `CR`, `ISSUE`로 분류한다.
8. 검증 명령을 실행했다면 cwd, 명령, exit code, 성공 기준, 로그/증적 경로를 남긴다.

### Gate 2 상류 정합성 검토

Gate 2 독립 검수는 Gate 2 산출물만 보는 검수가 아니다.

반드시 다음 순서로 확인한다.

1. Phase 0 산출물에서 프로젝트 목표, 사용자, 제약, 가정, 질문, 리스크, 의사결정을 확인한다.
2. Gate 1 요구사항정의서와 추적표에서 REQ/NREQ/AC, 포함/제외 범위, DEC/ISSUE를 확인한다.
3. Gate 2 설계 산출물이 Gate 1 범위를 누락, 축소, 임의 확장하지 않았는지 확인한다.
4. Gate 2 내부에서 아키텍처, 화면, 기능, API, 프로그램, DB, 보안, 개발표준이 서로 모순되지 않는지 확인한다.
5. 미해결 DEC/ISSUE/RISK/ASM이 닫혔거나 Gate 3 입력 또는 Orchestrator 판단 항목으로 분리됐는지 확인한다.

Gate 2 result에는 `Phase0 -> Gate1`, `Gate1 -> Gate2`, `Scope Drift`, `Open Decisions`, `Design Internal Consistency` 판정을 남긴다.

## 독립 runner 실행

Orchestrator가 `python vulcan.py agent-run --mode review --target-id RV-NNN`로 실행한 경우 이 skill은 선택된 CLI runner의 새 비대화형 세션에서 적용된다.

- `codex-cli` runner는 `codex exec`를 사용한다.
- `claude-cli` runner는 `claude -p`와 `--dangerously-skip-permissions`를 사용한다.
- `antigravity-cli` runner는 `agy.exe --print`를 사용한다.
- Desktop 대화창을 새로 여는 것이 아니라 별도 CLI 실행 세션이다.
- 모델, reasoning/effort, sandbox는 기본적으로 `vulcan.config.json.review` 값을 따른다.
- Gate 2 설계 검수와 Gate 4 QA 검수는 높은 추론 강도를 권장한다.
- Codex 기준 기본값은 `gpt-5.5` + `high` reasoning effort다.
- Claude 기준 기본값은 `claude-opus-4-7` + `high` effort다.
- Antigravity 기준 기본값은 `gemini-3.5-flash` + `high` effort다.
- 실행 단위로 바꿔야 하면 Orchestrator는 `agent-run --mode review --runner ... --model ... --reasoning-effort ...`를 사용한다.
- 리뷰어는 result 파일만 갱신하고, 최종 응답에는 판정과 작성한 내용을 요약한다.
- 리뷰어는 Gate 전환, `session.json` Gate 상태 변경, 최종 승인 판단을 하지 않는다.

## 판정 기준

| 판정 | 기준 |
| --- | --- |
| PASS | 다음 Gate 또는 승인 판단에 충분한 산출물과 증적이 있다 |
| FIND | 승인된 범위 안의 결함이며 Gate 안에서 수정 가능하다 |
| CR | 요구사항, 설계, 보안, 데이터, 릴리즈 범위 변경이 필요하다 |
| ISSUE | 추가 질문, 사용자 판단, 외부 확인이 필요하다 |

## 출력

다음을 result 파일에 남긴다.

- 리뷰 요약
- 검토한 문서와 Run
- 실행하거나 확인한 검증 결과
- `FIND` 후보
- `CR` 후보
- `ISSUE` 후보
- Orchestrator 결정 필요 항목

## 금지

- 본선 산출물을 직접 수정하지 않는다.
- 작성자의 의도를 추측해 누락을 통과시키지 않는다.
- 실행하지 않은 테스트를 Pass로 기록하지 않는다.
- 사용자 승인 없이 `User Approved`로 기록하지 않는다.
- Gate 전환, session 변경, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다.

