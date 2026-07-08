# 백로그 운영 프로세스

> 본 문서는 Vulcan-Anvil Ex 프로젝트에서 Phase 0, FIND, CR, ISSUE, 기술부채를 다음 Run 또는 필요한 Gate 진행으로 연결하는 백로그 관리 규칙을 정의한다.

## 1. 백로그란

Backlog는 Gate 밖에 따로 있는 단순 TODO 목록이 아니다.

Backlog는 다음 항목을 임시로 보관하고, 우선순위와 영향 범위를 정한 뒤, 적절한 Run 또는 필요한 Gate 진행으로 연결하는 작업 대기열이다.

- Phase 0에서 나온 미확정 아이디어와 질문
- QA/리뷰에서 발견됐지만 즉시 처리하지 않을 FIND
- 요구사항, 설계, 보안, 데이터, 릴리즈 범위를 바꾸는 CR
- 결론 내기 어려운 ISSUE
- 기술부채, 리팩터링, 운영 개선 항목

모든 변경요청이 Backlog를 먼저 거치는 것은 아니다. 요구사항, 설계, 보안 기준, DB, 화면, 테스트 기준선 변경이 명확하면 먼저 `DOC-PM-CR-NNN_*_v0.1.md` 상세 변경요청서를 작성하고 `DOC-PM-G0-001_Change-Request_v0.1.md` 관리대장에 등록한다. 이후 승인됐지만 즉시 처리하지 않는 경우에만 Backlog `CR` 항목으로 연결한다.

## 2. 위치와 책임

- 위치: [`docs/backlog/DOC-PM-OPS-001_Backlog_v0.1.md`](DOC-PM-OPS-001_Backlog_v0.1.md)
- 운영 주체: Orchestrator
- 판단 보조: `change-control`, `review`, `requirements`, `design`, `build` persona
- 도구: `python vulcan.py backlog list/add/done/reject`

Orchestrator는 Backlog 항목을 단순히 쌓아두지 않는다. 항목마다 유형, 관련 ID, 다시 진행할 Gate, 관련 Run, 우선순위를 확인하고 다음 행동을 제안해야 한다.

## 3. 항목 유형

| 유형 | 의미 | 대표 처리 |
| --- | --- | --- |
| `IDEA` | 아직 요구사항으로 확정되지 않은 아이디어, 질문, 방향 후보 | Phase 0 정리 후 Gate 1 후보 |
| `FIND` | 승인된 요구사항/설계 범위 안의 결함이나 누락 | QA Fix Run 또는 다음 배치 |
| `CR` | 요구사항, 설계, 보안, 데이터, 릴리즈 범위를 바꾸는 변경 | 영향도 분석 후 필요한 Gate 진행 |
| `ISSUE` | 원인, 처리 방향, 승인 여부가 아직 불명확한 항목 | 의사결정 후 IDEA/FIND/CR/DEBT로 전환 |
| `DEBT` | 기술부채, 리팩터링, 운영 개선, 의존성 정리 | 우선순위에 따라 Run 생성 |

## 4. 레벨

레벨은 작업의 크기가 아니라 Gate 영향도를 기준으로 정한다.

| 레벨 | 기준 | 처리 방식 |
| --- | --- | --- |
| `Trivial` | 문서, 추적표, 테스트 기준 변경 없이 처리 가능 | 바로 Run 생성 가능 |
| `Small` | 단일 또는 소수 ID 범위의 설계/테스트 보완 필요 | 영향받는 Gate를 다시 진행 |
| `Major` | 신규 요구사항, 기준선 변경, 아키텍처/보안/데이터 영향 | Gate 1 또는 Gate 2부터 다시 진행 |

다음 중 하나라도 해당하면 `Trivial`로 보지 않는다.

- 입력 검증, 거부 정책, 권한 정책이 바뀐다.
- API 요청/응답 계약이 바뀐다.
- 화면 흐름, DB 구조, 보안 기준, 테스트 기준이 바뀐다.
- 새 외부 의존성이나 운영 정책이 필요하다.
- 기존 요구사항의 의미가 바뀐다.

## 5. 우선순위

| 우선순위 | 기준 |
| --- | --- |
| `P0` | 보안 취약점, 데이터 손실, 운영 장애, 감사 대응 차단 |
| `P1` | Must 요구사항 미충족, 주요 기능 결함, Gate 통과 차단 |
| `P2` | Should 요구사항, 일반 개선, 기술부채 |
| `P3` | 아이디어, Parking Lot, 장기 검토 |

## 6. 상태

```text
Proposed -> Triaged -> Scheduled -> In Progress -> Done
                                      -> Rejected
                                      -> Deferred
```

| 상태 | 의미 |
| --- | --- |
| `Proposed` | 항목이 접수됐지만 아직 분류되지 않음 |
| `Triaged` | 유형, 레벨, 우선순위, 관련 ID, 다시 진행할 Gate 후보가 정리됨 |
| `Scheduled` | 처리할 배치나 Run 후보가 정해짐 |
| `In Progress` | Run 또는 필요한 Gate 진행이 시작됨 |
| `Done` | 처리와 검증이 완료됨 |
| `Rejected` | 반려되거나 다른 항목에 흡수됨 |
| `Deferred` | 의사결정 또는 일정상 보류됨 |

## 7. Gate와의 관계

Backlog 항목은 필요한 최소 Gate만 다시 진행한다.

| 영향 범위 | 다시 진행할 Gate |
| --- | --- |
| 아이디어 정리, 요구사항 후보 | Phase 0 또는 Gate 1 |
| `REQ`, `NREQ`, `AC` 변경 | Gate 1 |
| `FUNC`, `SCR`, `PGM`, `DB`, `IF`, `SEC` 변경 | Gate 2 |
| `UT`, `IT`, `PT`, `UI` 변경 | Gate 3 |
| 코드 결함, 증적 누락, 테스트 실패 수정 | 구현 또는 Gate 4 |
| 릴리즈 범위, 인수인계, 잔여 리스크 | Gate 5 |

다시 진행할 때는 가능한 한 scope를 좁힌다. 이 scope는 별도 되돌림 명령이 아니라 CR 상세서와 Run 문서에 기록한다.

```text
scope: REQ-005, AC-008, FUNC-005, PGM-005, SEC-002, UT-008
```

## 8. FIND, CR, ISSUE 처리

| 발견 항목 | Backlog 등록 가능 여부 | 기준 |
| --- | --- | --- |
| Blocker FIND | 원칙적으로 불가 | 현재 Gate 안에서 해결하거나 CR로 승격 |
| Major FIND | 원칙적으로 불가 | Gate 통과를 막으면 즉시 처리 |
| Minor FIND | 가능 | 다음 배치로 미뤄도 Gate 통과 근거가 훼손되지 않을 때 |
| CR | 가능 | 승인 후 즉시 처리하지 않거나 배치 조정이 필요할 때 |
| ISSUE | 가능 | 판단, 승인, 외부 확인이 필요할 때 |
| IDEA | 가능 | Phase 0에서 요구사항 후보로 정리 중일 때 |

Backlog가 Gate 4 타협의 핑계가 되어서는 안 된다. Gate 통과를 막는 결함은 Backlog로 넘기지 않는다.

## 9. 세션 중 사용 흐름

### 9.1 조회

```text
사용자: "백로그 확인해줘"
Orchestrator:
  1. `python vulcan.py backlog list` 실행
  2. P0/P1, CR, ISSUE, 다시 진행할 Gate 후보를 우선 요약
  3. 다음에 처리할 후보를 제안
```

### 9.2 추가

```text
사용자: "첨부파일 기능은 나중에 백로그로 남겨줘"
Orchestrator:
  1. 유형을 IDEA 또는 CR 후보로 판단
  2. 관련 ID와 출처를 기록
  3. `python vulcan.py backlog add --title "게시글 첨부파일 기능" --type CR --priority P2 --req REQ-후보 --source "사용자 요청"` 실행
  4. 필요하면 change-impact-analysis Run을 제안
```

### 9.3 착수

```text
사용자: "BL-003 시작하자"
Orchestrator:
  1. 유형, 레벨, 관련 ID, 다시 진행할 Gate를 확인
  2. 필요한 경우 `python vulcan.py gate-start <gate> --feature "BL-003"` 실행
  3. Orchestrator Plan 또는 Run 생성
  4. Run에 scope, 실행할 테스트, 추적표 갱신 기준을 기록
  5. 완료 후 테스트, 증적, 추적표, `DOC-PM-OPS-001_Backlog_v0.1.md` 갱신
```

### 9.4 완료

```text
처리 완료 후:
  1. 관련 Run과 검증 결과 확인
  2. 추적표와 산출물 갱신 확인
  3. `python vulcan.py backlog done --id BL-003 --commit <hash>` 실행
```

## 10. 중복과 흡수

- 같은 관련 ID와 같은 Gate 진행 범위를 가진 항목은 병합한다.
- 어떤 항목이 다른 항목의 선행 조건이면 상위 항목에 흡수하고 하위 항목은 Rejected 처리한다.
- CR과 ISSUE가 같은 변경을 가리키면 CR을 기준으로 통합한다.
- 단순 구현 작업과 그 구현을 가능하게 하는 설계 변경은 하나의 CR 흐름으로 묶는다.

## 11. 완료 조건

Backlog 항목을 Done으로 옮기려면 다음을 확인한다.

- 관련 Run 또는 커밋이 있다.
- 관련 ID와 변경 파일이 기록됐다.
- 필요한 테스트나 검증 결과가 있다.
- CR/FIND/ISSUE에서 파생된 항목이면 원 항목의 상태도 갱신됐다.
- 다음 Gate로 넘길 잔여 위험이 있으면 별도 ISSUE 또는 Backlog 항목으로 남겼다.

## 12. Orchestrator 체크리스트

- [ ] 이 항목이 IDEA, FIND, CR, ISSUE, DEBT 중 무엇인지 분류했다.
- [ ] 관련 ID와 출처를 기록했다.
- [ ] 지금 처리할지, 다음 배치로 넘길지 판단했다.
- [ ] 다시 진행할 Gate와 scope를 정했다.
- [ ] Gate 통과를 막는 FIND를 Backlog로 넘기지 않았다.
- [ ] 처리 후 Run, 검증, 추적표, Backlog 상태를 갱신했다.
