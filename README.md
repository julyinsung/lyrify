# {PROJECT_NAME}

이 저장소는 애플리케이션 소스와 Vulcan-Anvil Ex 산출물/운영 파일을 함께 보관합니다.

Vulcan-Anvil Ex는 요구사항, 설계, 구현, 테스트, 증적, 승인 기록을 Gate 단위로 남기기 위한 AI 협업 개발 프레임워크입니다. 따라서 일반 애플리케이션 저장소보다 문서와 운영 파일이 많습니다.

## 폴더 구조

```text
{PROJECT_NAME}/
  backend/                 # 백엔드 애플리케이션 소스가 생성되는 영역
  frontend/                # 프론트엔드 애플리케이션 소스가 생성되는 영역
  docs/                    # Vulcan-Anvil Ex 산출물, 템플릿, Run 기록
  AGENTS.md                # Codex/GPT 에이전트 진입 지침
  .agents/                 # Codex repo-local skill 카드
  .codex/agents/           # Codex custom agent 정의
  .claude/                 # Claude 런타임용 adapter 파일
  session.json             # 현재 Gate, 진행 상태, 대시보드용 상태 캐시
  vulcan.config.json       # 독립 검수 등 프로젝트별 운영 설정
  vulcan.py                # Gate/Run/추적성 검증 보조 CLI
  ENVIRONMENT.md           # 프로젝트 실행 환경 메모
  GATE_GUIDE.md            # Gate 진행 가이드
```

프로젝트에 따라 `backend/`, `frontend/`, `build.gradle`, `settings.gradle`, `gradlew`, `package.json` 같은 실제 애플리케이션 파일은 구현 단계에서 생성됩니다.

## 주요 영역

| 경로 | 성격 | 설명 |
| --- | --- | --- |
| `backend/`, `frontend/` | 애플리케이션 소스 | 실제 개발 대상 코드입니다. |
| `docs/artifacts/` | 프로젝트 산출물 | 요구사항, 설계, 테스트, QA, 릴리즈 승인 문서가 작성됩니다. |
| `docs/runs/` | 에이전트 작업 기록 | 각 Gate/작업 단위의 입력 계약, 수행 결과, 검증 결과를 남깁니다. |
| `docs/reviews/` | 독립 검수 기록 | 독립 검수 요청과 결과 후보를 남깁니다. |
| `docs/core/` | Ex Core 규칙 | Gate, ID, 추적성, Orchestrator, persona 규칙입니다. |
| `docs/adapters/` | 런타임 adapter | Codex/GPT, Claude 같은 실행 환경별 연결 규칙입니다. |
| `docs/templates/` | 산출물 템플릿 | 프로젝트 산출물의 기본 양식입니다. |
| `docs/ref-docs/` | 비공개 참고자료 | 민감 문서를 둘 수 있는 영역이며 기본적으로 커밋 대상이 아닙니다. |

## 왜 프레임워크 파일이 같이 있나요?

이 프로젝트는 단순 코드 생성 결과가 아니라, Gate별 의사결정과 증적을 함께 남기는 방식으로 진행됩니다.

- `AGENTS.md`는 Codex/GPT가 프로젝트 규칙을 읽는 진입점입니다.
- `.agents/skills/`는 Codex가 Gate/Run/Impl/QA/Release 작업에서 필요할 때 읽는 repo-local skill 카드입니다.
- `.codex/agents/`는 메인 Orchestrator가 명시적으로 호출할 수 있는 Codex custom agent 정의입니다.
- `.claude/`는 Claude 사용 시 같은 Core 규칙을 적용하기 위한 adapter입니다.
- `session.json`은 현재 Gate와 대시보드 상태를 기록합니다.
- `vulcan.py`는 Run 생성, Gate 상태 갱신, 추적성 검증을 수행하는 보조 도구입니다.
- `docs/`는 감리 대응 산출물과 에이전트 작업 기록의 원본입니다.

처음 보는 사람은 `backend/`와 `frontend/`를 애플리케이션 코드로 보고, `docs/`, `AGENTS.md`, `.agents/`, `.codex/agents/`, `.claude/`, `session.json`, `vulcan.py`를 Vulcan-Anvil Ex 운영 파일로 보면 됩니다.

## 기본 명령

```bash
python vulcan.py gate-start gate1 --feature "기능명"
python vulcan.py run-new --gate gate1 --skill traceability-review --title "요구사항 검토" --related-ids REQ-001
python vulcan.py review-request --gate gate2 --title "Gate 2 설계 독립 검수" --related-ids REQ-001
python vulcan.py review-run --review-id RV-001
python vulcan.py check-trace
python vulcan.py session --gate gate1 --status done --feature "기능명"
```

독립 검수는 기본적으로 `vulcan.config.json`의 `independent_model`과 `independent_reasoning_effort` 값을 사용합니다. Gate 2 설계 검수와 Gate 4 QA 검수는 `gpt-5.5` + `high`를 권장합니다.

새 프로젝트에서는 `independent_enabled`가 기본적으로 `true`입니다. 이는 Gate 2/Gate 4 종료 전 독립 검수를 기본 권장 절차로 둔다는 뜻이며, 검수 실행은 `review-request`, `review-run` 명령으로 명시적으로 수행합니다.

```bash
python vulcan.py review-run --review-id RV-001 --model gpt-5.5 --reasoning-effort high
```

Gate 진행 중에는 사용자의 명시 승인 없이 다음 Gate로 넘어가지 않습니다.
