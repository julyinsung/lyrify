---
name: vulcan
description: "Phase 0(Discovery)와 Gate 1~5 개발 프로세스를 오케스트레이션하는 스킬. discovery/requirements/design/screen-design/security-review/screen-review/ui-review/development-review/test-design/build-planning/build-frontend/build-backend/evidence/review 에이전트 팀의 협업을 조율한다. Use when 사용자가 새 프로젝트를 시작하거나 'Discovery 시작', '프로젝트 시작', '요구사항 정의', 'Gate N 시작', '설계 시작', '테스트 계획', '구현 시작', 'UI 증적', 'QA 리뷰', '최종 승인', 'CR 처리', 'Gate 상태 확인' 등 Phase 0/Gate 진입·전환·재진행을 요청할 때. NOT for 프로젝트 초기화(vulcan.py init), session.json 직접 편집, 단순 코드 수정·리팩토링, 단일 파일 디버깅."
---

# Vulcan — Phase 0 + 5-Gate 오케스트레이터

에이전트 팀을 조율하여 Phase 0 + 5-Gate 프로세스로 프로젝트를 진행한다. 표준 페르소나·매핑·CLI는 `CLAUDE.md`를 본다. 이 스킬은 **Gate별 워크플로우와 트리거**에 집중한다.

## 1. Phase 0 (Discovery)

> **Gate 규약/rules/check-trace 적용 안 됨. 자유 반복.**

트리거: "상위설계 시작", "Discovery 시작", "법령 분석", "인프라 설계", "FP 산정", "프로젝트 시작", 자연어 요청.

1. `docs/artifacts/00-discovery/` 확인 (`vulcan.py init`이 P0 산출물 4개를 미리 생성)
2. `discovery` agent 투입 — 사용자와 대화로 배경/현행/위험/공수 정리
3. P0 표준 4개 산출물(`Project-Brief`, `Stakeholder-And-Scope`, `As-Is-To-Be`, `Risk-And-Assumption`) 채우기
4. 임의 ID 새 파일 생성 금지 (`DIS-`, `OVERVIEW-` 등)
5. 사용자 반복 요청 시 자유롭게 반복

**Phase 0 → Gate 1 전환**: P0 산출물 충족 확인 → 사용자 승인 → `requirements` 투입 → REQ/AC로 변환.

## 2. Phase 1: 준비 (Orchestrator 직접)

1. `session.json.current_gate` 확인
2. 요청 분류:
   - "프로젝트 시작" / 자연어 + gate1 pending → `discovery` 투입 후 `requirements`로 연계
   - 명시적 Gate 지정 또는 진행 중인 프로젝트 → discovery 스킵, 해당 Gate agent 직접 투입
   - "상태 확인" → 현재 Gate 상태 보고

## 3. Phase 2: Gate별 팀 구성

Gate 2 설계는 `docs/core/GATE2_DESIGN_SEQUENCE.md` §2의 **10단계(G2-01~G2-10)** 순서를 따른다. 한 Run에서 G2를 한 번에 끝내려 하지 말고, 각 Run에 `design_sequence.current_step`과 `next_run_candidates`를 명시한다.

| Gate / 단계 | 담당 agent | 비고 |
|------|----------|------|
| Gate 1 | `requirements` | |
| G2-01 Kickoff/범위 | `design` | Gate 1 산출물 확인 + 범위 고정 |
| G2-02 SW Architecture Draft | `design` | C1/C2 + 주요 CNT/ADR 후보. `check-architecture --level draft` |
| G2-03 Screen/User Flow | `screen-design` | SCR/UIREF/상태/메시지. **prototype/UIREF는 UI Implementation Contract 작성** |
| G2-04 Function Spec | `design` | FUNC, 기능/예외 흐름 |
| G2-05 Program/API Spec | `design` | PGM, API, DTO, 오류코드 |
| G2-06 Data/DB Spec | `design` | DB, 단어사전, ERD/DBML, 제약 |
| G2-07 Security Guide | `design` | SEC별 정책값, 적용 위치, 오류 메시지 |
| G2-08 Development Standard | `design` | 패키지 구조, 빌드/테스트 명령(cwd/성공기준 포함) |
| G2-09 SW Architecture Baseline 보강 | `design` | CMP/FLOW/품질/추적 마무리. `check-architecture --level baseline` |
| G2-10 Design Review | `security-review`+`screen-review`+`ui-review`+`development-review` 병렬 |
| Gate 3 | `test-design` | UT/IT/PT/UI ID + **검증 명령 메타(cwd/성공/exit/로그) 정의** |
| 구현 계획 | `build-planning` | |
| 구현 | `build-frontend`+`build-backend` | Wave별 |
| UI 증적 | `evidence` | **상태별 캡처** (기본/로딩/오류/성공/전환), 명령 실행 메타 기록 |
| Gate 4 | `review` | UI Contract 차이 판정, 검증 명령 누락 시 FIND |
| Gate 5 | (Orchestrator 직접) | `07-release/DOC-PM-G5-001_Release-Approval`. CR은 `05-change/` |

## 4. 작업 분할 전략 (컨텍스트 보호)

> **⚠️ 서브에이전트에 한 번에 모든 REQ를 주지 않는다.**

| REQ 그룹 복잡도 | 기준 | 청크 크기 |
|-----|------|-----|
| 경량 | 상세 REQ 1~3, API 1~2 | 3~4 그룹 묶음 |
| 보통 | 상세 REQ 4~6, API 3~5 | 2 그룹 묶음 |
| 복잡 | 상세 REQ 7+, API 6+ | 1 그룹 단독 |

REQ 그룹 1~2개면 분할 없이 한 번에. 서브에이전트 프롬프트에는 청크 REQ 범위 + 참조 문서 경로만 (설계 내용 본문 옮기기 금지).

## 5. Phase 3: 산출물 검증 및 Gate 전환

> **⛔ 6단계 모두 완료해야 Gate 전환. 명시 승인 없이 "User Approved" 기록 금지.**

```
1. 산출물 검증 (누락/빈 파일 → 재투입)
2. 사용자에게 보고: 산출물 요약 + 미해결 항목 + 다음 Gate 제안 + "Gate N으로 진행할까요?" 승인 질문
3. 사용자 명시적 승인 대기 (대화상 승인 없이 Run/Release Approval에 'User Approved' 기록 금지)
4. python vulcan.py check-trace 실행
5. 이슈 0건 확인 시 python vulcan.py session --gate gateN --status done --feature "..." 실행
6. session 완료 후 다음 Gate 진행
```

## 6. Gate 전환 조건

| Gate | 완료 조건 |
|------|----------|
| Phase 0 | 배경/제약/참조 파악, 질문·가정·위험 기록 |
| Gate 1 | 모든 `REQ`/`NREQ`에 `AC` 매핑, 추적표 반영 |
| Gate 2 | SW 아키텍처 Baseline (`check-architecture --level baseline` 통과) + `FUNC/SCR/PGM/API/DB/IF/SEC`/개발표준 정의, 보안/화면/UI/개발표준 검수 통과 |
| Gate 3 | 모든 `AC`·보안항목이 `UT/IT/PT/UI` 중 하나 이상에 연결 |
| 구현 | Build Wave별 코드+테스트+추적표+증적 갱신, 단위 테스트 Pass |
| Gate 4 | Blocker(A~D) 전원 Pass, FIND/CR/ISSUE 명시적으로 처리 |
| Gate 5 | `Release-Approval` 작성, 미해결 CR/ISSUE 처리, 사용자 최종 승인 |

## 7. CR 처리 / Gate 재진행

트리거: "요구사항 추가", "Gate N부터 다시", "변경요청 처리", "CR 처리".

```
1. CR 상세서 작성 (05-change/DOC-PM-CR-NNN) — 변경 내용/영향 ID/재진행 Gate 명시
2. CR Register(DOC-PM-G0-001_Change-Request)에 등록
3. 사용자 승인
4. python vulcan.py gate-start <gate> 실행
   → orchestrator-plan Run 초안이 자동 생성됨 (같은 Gate에 Draft/InProgress Run 없을 때).
     자동 생성된 Run을 읽고 CR-ID, 영향 범위, 갱신 산출물, 테스트 기준을 채운다.
5. 필요한 세부 persona Run은 `run-new`로 추가 생성
6. 해당 Gate agent 투입, scope 안에서 산출물 갱신
7. 추적표/CR 상세서/CR Register 갱신
```

별도 `rollback` 명령은 제거됨. 영향 범위는 CR 상세서와 Run 문서 scope로 관리.

## 8. 트리거 → 투입 매핑

| 사용자 요청 | 투입 |
|-----------|------|
| "Discovery 시작", "프로젝트 시작" | `discovery` |
| "Gate 1 시작", "요구사항 정의" | `requirements` |
| "Gate 2 시작", "설계 시작" | `design`(아키텍처→상세) → `screen-design`, 검수 병렬 |
| "Gate 3 시작", "테스트 계획" | `test-design` |
| "구현 계획" / "구현 시작" | `build-planning` → `build-frontend`+`build-backend` |
| "UI 증적", "화면 캡처" | `evidence` |
| "Gate 4 시작", "리뷰 시작" | `review` |
| "상태 확인" | (Orchestrator 직접) |
| "CR 처리", "Gate N부터 다시" | (Orchestrator 직접: CR 상세서 → gate-start → Run) |

## 9. 긴급 절차 (Hotfix)

1. REQUIREMENTS.md에 최소 요구사항 작성
2. 설계 문서 생략 가능 (사용자 명시적 허용)
3. **Gate 4 QA 리뷰는 절대 생략 불가**

## 10. 에스컬레이션 / 에러 핸들링

다음 시 즉시 사용자에게 보고: 요구사항 범위 변경, QA 2회 연속 Fail, 설계 외 외부 서비스 필요, 보안 취약점, 병렬 인스턴스 파일 충돌. 형식: `"에스컬레이션: [트리거] — [상황] — [선택지]"`.

| 에러 | 전략 |
|------|------|
| session.json 없음 | "vulcan.py init 먼저" 안내 |
| Gate 순서 이탈 | 현재 Gate 안내, 순서 진행 유도 |
| 에이전트 실패 | 1회 재시도 → 사용자 보고 |
| 산출물 누락 | check-trace 실행 → 누락 식별 |
| 산출물 품질 저하 | 청크 더 작게 쪼개서 재투입 |

## 11. 확장 스킬

| 스킬 | 대상 | 역할 |
|------|------|------|
| `security-baseline` | design, security-review, review | OWASP Top 10 체크리스트 |
