# lyrify — Vulcan-Anvil Ex (Claude Adapter)

Codex의 `AGENTS.md`에 대응되는 Claude 진입 문서. Ex Core 규칙과 Claude adapter를 연결한다.

## 1. 역할

Orchestrator로 동작 (별도 persona 아님, 계획·위임·검증·보고 조율).

**지침 우선순위**: ① 사용자 요청·대화 → ② 이 파일 → ③ `docs/core/` (Ex 규칙) → ④ `docs/adapters/claude/` (Claude 계약) → ⑤ `docs/artifacts/`/`docs/templates/` → ⑥ 기존 코드

## 2. Persona 매핑

`.claude/agents/{persona}.md` 파일명 = persona명 (1:1). 사용자 요청을 받으면 persona를 판단하고 같은 이름의 agent를 invoke한다.

| Persona | Claude agent |
| --- | --- |
| `discovery` · `requirements` · `design` · `screen-design` · `test-design` · `build-planning` · `evidence` · `review` | 같은 이름 |
| `security-review` · `screen-review` · `ui-review` · `development-review` | 같은 이름 |
| `build` | `build-frontend`, `build-backend` |
| `release` · `change-control` · `documentation` | Orchestrator 직접 |

위임 시 `persona`, `run_id`, `gate`, `related_ids`, `scope`, `completion_criteria` 함께 전달 (`docs/adapters/claude/RUN_INPUT_CONTRACT.md`).

## 3. 필수 참조 (간단하지 않은 Run 시작 전)

- **Ex Core (항시)**: `docs/core/{ID_SYSTEM, TRACEABILITY_RULES, ORCHESTRATOR_PROTOCOL, AGENT_RUN_PROTOCOL, AGENT_PERSONAS, CHANGE_CONTROL_PROCESS, SECURITY_BASELINE, KISA_SECURITY_RULES, DATA_STANDARD_RULES, REFERENCE_STANDARDS, DOCUMENT_METADATA}.md`
- **Ex Core (상황별)**: `docs/core/{TECH_STACK_BASELINES (기술스택 결정 시), REFACTORING_PROCESS (리팩토링 시)}.md`
- **Claude 계약**: `docs/adapters/claude/{PERSONA_MAPPING, RUN_INPUT_CONTRACT, RUN_OUTPUT_CONTRACT, GATE_PROMPTS, LIMITATIONS}.md`

## 4. Phase 0 + 5-Gate 흐름

| 단계 | 산출물 위치 | 주요 ID |
| --- | --- | --- |
| Phase 0 (탐색) | `00-discovery/` | DEC, RISK, IDEA |
| Gate 1 (요구) | `01-requirements/` | REQ, NREQ, AC |
| Gate 2 (설계) | `02-design/{architecture,function,program,api,screen,data,security,development-standard}/` | CNT/CMP/FLOW/ADR, FUNC, PGM, API, DB, IF, SEC, SCR |
| Gate 2 추적 | `02-traceability/` | (전체 연결) |
| Gate 3 (테스트) | `03-test/` | UT, IT, PT, UI |
| 구현 | `src/`, `docs/runs/` | BW, RUN |
| Gate 4 (QA) | `04-review/` | FIND, ISSUE |
| Gate 5 (승인/릴리즈) | `07-release/`, `05-change/` | CR(register/detail), Release Approval |
| Backlog | `docs/backlog/` | — |

상세는 `GATE_GUIDE.md`, `docs/core/AGENT_RUN_PROTOCOL.md` §5.

## 5. Orchestrator 룰

- 첫 인사·방향 질문은 **탐색 응답**만. 코드/문서 즉시 작성 금지. `discovery` 투입 또는 직접 응답.
- 항상 `session.json.current_gate` 먼저 확인. **현재 Gate보다 앞선 산출물·Run·코드·테스트 생성 금지.**
- end-to-end 목표 요청이라도 현재 Gate가 `phase0`/`gate1`이면 요구사항·질문·승인 지점까지만 정리 후 멈춘다.
- Subagent/타 환경 결과는 Orchestrator가 재검증. 구현자 자기 구현 단독 승인 금지 → `review` persona.

### 5.1 Gate 전환 순서 (절대 위반 금지)

```
run-new (RUN 기록) → 산출물 작성 → 사용자 승인 → check-trace 통과 → session --status done
```

위반 사례: RUN 없이 작업 시작, check-trace 미통과 상태에서 `session --status done`, 빈 표준 템플릿 상태로 Gate 완료.

### 5.2 산출물 생성 룰

`vulcan.py init`이 모든 Gate 표준 빈 템플릿을 미리 생성한다(아래 표). **임의 ID(`DIS-`, `OVERVIEW-` 등) 새 파일 금지.** 작업 시작 전 `Glob`/`LS`로 디렉터리 확인 → 기존 빈 템플릿 `Read` → 메타/표 구조 유지하며 `Edit`. 추가 파일은 표준 ID(`DOC-{AREA}-{GATE}-{NNN}`)로만.

| Gate | 빈 템플릿 (`docs/artifacts/` 하위) |
| --- | --- |
| **P0** | `00-discovery/DOC-CORE-P0-001_Project-Brief`, `-002_Stakeholder-And-Scope`, `-003_As-Is-To-Be`, `-004_Risk-And-Assumption` |
| **G1** | `01-requirements/DOC-CORE-G1-001_Requirements-Spec` |
| **G2 Architecture (먼저)** | `02-design/architecture/DOC-ARCH-G2-001_SW-Architecture` |
| **G2 Detail** | `02-design/function/DOC-CORE-G2-001_Function-Spec`, `program/DOC-CORE-G2-002_Program-Spec`, `api/DOC-API-G2-001_API-Spec`, `screen/DOC-CORE-G2-003_Screen-Spec`, `data/DOC-DATA-G2-{001_Project-Glossary, 002_Database-Spec}`, `security/DOC-SEC-G2-001_Security-Guide`, `development-standard/DOC-DEV-G2-001_Development-Standard` |
| **G2 ERD (DBML)** | `02-design/data/erd/logical/logical-erd.dbml`, `physical/physical-erd.dbml` (PNG/SVG/PDF는 `erd/exports/`) |
| **G2 Screen 자료** | `02-design/screen/images/` (시안), `screen/prototypes/` (HTML/CSS/JS 모크업) |
| **G2 추적** | `02-traceability/DOC-CORE-G4-001_Traceability-Matrix` |
| **G3** | `03-test/DOC-QA-G3-001_Test-Cases` |
| **G4** | `04-review/DOC-QA-G4-001_QA-Finding`, `-002_Test-Result` |
| **CR Register** | `05-change/DOC-PM-G0-001_Change-Request` (개별 CR detail = `DOC-PM-CR-NNN`을 별도 생성) |
| **G5 Release** | `07-release/DOC-PM-G5-001_Release-Approval` |

(모든 파일은 `_v0.1.md` 확장)

### 5.3 Build Wave / 변경 분류

- 구현 규모가 중간 이상 또는 multi-module/multi-commit 필요 시 `implementation-plan` Run을 만들고 `BW-NNN`으로 분할.
- **FIND**: 승인 범위 내 결함 (G4 QA Fix Loop). **CR**: 베이스라인 변경 (`gate-start` + Run + scope). **ISSUE**: 결론 미정 (Backlog).

## 6. Run 단위

모든 의미있는 작업은 Run으로 기록 (`docs/runs/RUN-NNN_*.md`). 변경은 ID 연결. 미실행 테스트를 통과로 보고 금지 (`not_run`/`failed`/`partial` 명시). 상세는 `docs/core/AGENT_RUN_PROTOCOL.md`.

## 7. CLI (Orchestrator 직접 실행)

- `vulcan.py orchestrator-plan --goal "..." --gate <gateN>` — 계획 Run
- `vulcan.py run-new --gate <gateN> --persona <persona> --skill <skill> --title "..." --related-ids ...`
- `vulcan.py run-check <run-file>`
- `vulcan.py check-trace` (Gate 완료 시 SW 아키텍처 baseline 검증 자동 포함)
- `vulcan.py check-architecture --level {draft|baseline}` (G2 초반=draft, G3 진입 전=baseline)
- `vulcan.py session --gate <gateN> --status done --feature "..."`
- `vulcan.py gate-start <gateN>` — 해당 Gate를 진행 상태로 전환 + **orchestrator-plan Run 초안 자동 생성** (같은 Gate에 Draft/InProgress Run 없을 때만). 자동 생성된 Run을 읽고 세부 persona Run은 `run-new`로 추가. (이전 `rollback` 명령은 제거됨)
- `vulcan.py backlog ...` / `handoff ...`

## 8. 트리거 → 투입 매핑

| 사용자 요청 | 투입 |
| --- | --- |
| "프로젝트 시작", 자연어 | `discovery` (Phase 0 탐색) |
| "요구사항 정의" / "Gate 1" | `requirements` |
| "설계 시작" / "Gate 2" | `design`(아키텍처→상세) → `screen-design`, 검수: `security-review`+`ui-review`+`development-review` 병렬 |
| "테스트 계획" / "Gate 3" | `test-design` |
| "구현 계획" / "구현 시작" | `build-planning` → `build-frontend`+`build-backend` Wave별 |
| "UI 증적" / "화면 캡처" | `evidence` |
| "QA 리뷰" / "Gate 4" | `review` |
| "CR 처리" / "Gate 재진행" | Orchestrator 직접 (`gate-start` + 필수 Run) |

상세 워크플로우는 `.claude/skills/vulcan/skill.md`.

## 9. 출력 규칙

Run 종료 시 `docs/adapters/claude/RUN_OUTPUT_CONTRACT.md` 형식으로 보고 (run_id, status, summary, changed_files, related_ids, verification_results, evidence, traceability_updates, findings/CR/issues, next_run_suggestion). **실패·미실행 검증을 숨기지 않는다.**

## 10. 참고문서 경계

- `docs/seed-docs/`: 공개 표준, 읽기 전용 참고
- `docs/ref-docs/`: 민감, 커밋 금지. 필요 시 규칙·결정만 프로젝트 산출물에 요약
