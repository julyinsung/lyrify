# Codex/GPT Skill

> 목적: Codex/GPT skill은 `AGENTS.md`가 참조하는 가벼운 작업 절차 카드다.

이 파일들은 Claude Code의 `.claude/skills`가 아니며 런타임 플러그인으로 취급하지 않는다.
Vulcan-Anvil Ex Run을 수행하기 전에 어떤 절차를 읽어야 하는지 정의한다.

## Skill 목록

| Skill | 사용할 때 |
| --- | --- |
| `persona-run` | 요구사항 작성, 설계, 테스트 설계, 구현, 증적 정리처럼 표준 persona 자체가 작업 절차일 때 |
| `traceability-review.md` | 산출물, 코드, 테스트, 증적이 ID로 연결되어 있는지 검토할 때 |
| `screen-design.md` | 화면 구조, 외부/생성 시안, 와이어프레임, UI 기준 증적을 설계할 때 |
| `security-review.md` | 보안 설계, 보안 구현, 보안 테스트 커버리지를 검토할 때 |
| `screen-review.md` | 화면 목록, 화면 상태, 와이어프레임/시안, UI 테스트/증적 기준을 검토할 때 |
| `ui-review.md` | 구현자가 좋은 화면을 만들 수 있을 만큼 UI 기준선이 충분한지 검토할 때 |
| `development-standard-review.md` | 개발표준정의서, 패키지 구조, 코딩/주석/테스트 컨벤션 확정 여부를 검토할 때 |
| `implementation-plan.md` | 구현 전에 Build Wave, 의존성, 위임, 검증, 커밋 단위를 계획할 때 |
| `implementation-scaffold.md` | feature 구현 전에 빌드 가능한 계약 skeleton과 public signature를 만들 때 |
| `build-wave.md` | Implementation Plan에 정의된 하나의 Build Wave를 구현할 때 |
| `data-standard-review.md` | 프로젝트 용어집, DB 명세, 데이터 명명, 공공데이터 표준 준수 여부를 검토할 때 |
| `qa-execution.md` | Gate 4 테스트 실행, 로그, Playwright 증적, 후보 FIND/CR/ISSUE를 수집할 때 |
| `qa-fix-loop.md` | 승인된 설계 범위 안에서 QA 발견사항을 수정할 때 |
| `change-impact-analysis.md` | 변경요청을 분석하거나 이슈를 CR로 승격해야 하는지 판단할 때 |
| `independent-review.md` | 작성 세션과 분리된 독립 검수로 Gate 산출물과 증적을 다시 검토할 때 |

## 규칙

- skill 수행 결과는 `REQ`, `AC`, `FUNC`, `SCR`, `PGM`, `DB`, `SEC`, `UT`, `IT`, `UI`, `FIND`, `CR` 중 관련 ID와 연결한다.
- skill 수행 중 범위 누락이나 결함을 발견하면 `docs/core/CHANGE_CONTROL_PROCESS.md`에 따라 `ISSUE`, `FIND`, `CR`로 분류한다.
- 핵심 규칙을 이 디렉터리에 중복하지 않는다. 세부 기준은 `docs/core/`와 adapter 계약 문서를 참조한다.
