# Claude Persona Mapping

> 상태: v0.2
> 목적: `.claude/agents/` 파일명과 Ex 표준 persona의 관계를 정의한다.

## 1. 기본 방향

새 파일명 = persona명 (1:1 대응). 오케스트레이터는 persona를 결정하면 같은 이름의 agent 파일을 직접 투입한다. 별도 매핑 테이블이 불필요하다.

## 2. 현행 agent 파일 목록

| Claude agent 파일 | Ex persona | Gate | 비고 |
| --- | --- | --- | --- |
| `discovery.md` | `discovery` | P0 | 온보딩, 현행 분석, 위험/가정 정리 |
| `requirements.md` | `requirements` | G1 | 요구사항, AC, 기술스택 |
| `design.md` | `design` | G2 | SW 아키텍처, 기능/프로그램/API/DB/보안 설계 |
| `screen-design.md` | `screen-design` | G2 | 화면 구조, 와이어프레임, 디자인 토큰 |
| `security-review.md` | `security-review` | G1/G2/G3/G4 | 보안 요구사항·설계·구현 검토 |
| `screen-review.md` | `screen-review` | G2/G3/G4 | 화면 누락·상태·증적 기준 검토 |
| `ui-review.md` | `ui-review` | G2/G4 | UI 기준선 충분성 검토 |
| `development-review.md` | `development-review` | G2/G4 | 개발표준·코딩컨벤션 검토 |
| `test-design.md` | `test-design` | G3 | 테스트 케이스, UT/IT/PT/UI 설계 |
| `build-planning.md` | `build-planning` | Impl | Build Wave 분할, 위임 계획 |
| `build-frontend.md` | `build` | G4 | 프론트엔드 구현 |
| `build-backend.md` | `build` | G4 | 백엔드 구현 |
| `evidence.md` | `evidence` | G4 | 스크린샷, 테스트 결과, 증적 수집 |
| `review.md` | `review` | G4/G5 | 추적성·보안·품질 검수, FIND/CR 판정 |

`release`, `change-control`, `documentation` persona는 Orchestrator가 직접 수행한다 (별도 agent 파일 없음).

## 3. Orchestrator 규칙

```text
요청: "로그인 요구사항 정리해줘"
persona: requirements
Claude agent: requirements
```

```text
요청: "게시글 작성 API 구현해줘"
persona: build
Claude agent: build-backend
```

```text
요청: "화면 캡처 증적 만들어줘"
persona: evidence
Claude agent: evidence
```

## 4. Subagent 위임 규칙

```yaml
persona: build
claude_agent: build-backend
run_id: RUN-003
gate: gate4
related_ids: [REQ-005, PGM-005, UT-007]
```

subagent는 다음 문서를 먼저 확인한다.

- `docs/core/AGENT_PERSONAS.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/adapters/claude/PERSONA_MAPPING.md`
- 해당 `.claude/agents/{agent}.md`
