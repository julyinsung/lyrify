# UI 품질 검토 Skill

## 사용할 때

Gate 2에서 Gate 3로 넘어가기 전, 화면이 있는 기능의 UI 기준선이 구현자가 좋은 화면을 만들 수 있을 만큼 충분한지 검토할 때 사용한다.

`screen-review`가 화면 누락, 상태 누락, 증적 가능 여부를 확인한다면, `ui-review`는 화면 품질 기준, 레이아웃 밀도, 상태 표현, 모바일 사용성, 사용자 피드백 흐름을 더 까다롭게 본다.

## 필수 입력

- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/templates/SCREEN_SPEC_TEMPLATE.md`
- 관련 요구사항정의서
- 관련 기능명세서
- 관련 화면설계서
- 관련 테스트케이스 또는 UI 테스트 후보
- 외부 시안, 이미지 시안, HTML/CSS/JS 화면 퍼블리싱 산출물, 텍스트 와이어프레임 중 현재 기준선

## 검토 관점

1. UI 기준선 유형이 명확한지 확인한다.
   - `Text Wireframe`
   - `Image Mockup`
   - `HTML/CSS/JS 화면 퍼블리싱 산출물`
   - `External Design`
   - `Existing Screen`
2. 텍스트 와이어프레임만 있는 경우, 구현자가 화면 밀도, 여백, 계층, 컴포넌트 우선순위를 충분히 판단할 수 있는지 확인한다.
3. 화면별 기본, 오류, 빈 상태, 로딩, 처리 중, 권한 제한 상태가 사용자의 흐름 기준으로 충분한지 확인한다.
4. 버튼, 입력창, 오류 메시지, 링크, 삭제/위험 액션의 위치와 강조가 명확한지 확인한다.
5. Desktop/Mobile viewport에서 줄바꿈, 버튼 배치, 입력 흐름이 자연스러운지 확인한다.
6. 도메인에 맞는 UI 톤을 확인한다. 업무 도구는 과한 장식보다 반복 사용, 스캔, 입력 효율을 우선한다.
7. 구현자가 임의로 디자인을 해석해야 하는 부분을 찾는다.
8. 화면 퍼블리싱 산출물 또는 외부 시안이 있으면 UI Implementation Contract의 필수 유지, 변경 허용, 변경 금지, 비교 방식이 충분한지 확인한다.
9. UI 품질이 중요한 프로젝트인데 기준선이 텍스트 와이어프레임뿐이면 `Minimal`로 판정하고 보강을 권고한다.

## 판정

| 판정 | 의미 | 다음 행동 |
| --- | --- | --- |
| `Ready` | 현재 UI 기준선으로 구현 가능 | Gate 3 진행 가능 |
| `Minimal` | 구현은 가능하지만 품질 편차가 큼 | 사용자 확인 후 진행하거나 mockup 보강 |
| `Needs Mockup` | 텍스트 와이어프레임만으로 구현 품질 보장 어려움 | Image/HTML/외부 시안 보강 필요 |
| `Blocked` | 필수 화면/상태/흐름이 부족함 | Gate 2 보완 후 재검토 |
| `Contract Missing` | 화면 퍼블리싱 산출물 또는 외부 시안은 있으나 구현 계약이 없음 | UI Implementation Contract 작성 후 재검토 |

## 출력

다음을 반환한다.

- 검토한 `SCR-ID`, `UIREF-ID`
- UI 기준선 유형
- UI Implementation Contract 판정
- 판정: `Ready` / `Minimal` / `Needs Mockup` / `Contract Missing` / `Blocked`
- 구현자가 임의 해석해야 하는 부분
- 보강 권고: 레이아웃, 상태, 메시지, 모바일, 접근성, 위험 액션
- Gate 3로 넘길 수 있는 UI 테스트 기준
- `FIND`, `ISSUE`, `CR` 권고
