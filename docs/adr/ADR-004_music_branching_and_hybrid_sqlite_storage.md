# ADR-004: Music Git-Flow Branching, Hybrid SQLite Storage, and AI Co-Producer Agent Architecture

- **Status**: Accepted (v0.2.0)
- **Date**: 2026-08-29
- **Deciders**: Lead Architect, Lead AI Music Producer, Engineering Team
- **Related Requirements**: SCN-006, SCN-007, SCN-008, REQ-004, REQ-005

---

## 1. Context & Problem Statement (배경 및 문제 정의)

Lyrify Studio v0.1.0(MVP)은 마스터 볼트(`ZENION-MUSIC`), Linux FFmpeg 비디오 렌더링, 기본 AI 기획 파이프라인을 성공적으로 구축했습니다.
그러나 실제 상업 음원 및 고품질 음악 제작 과정에서 다음과 같은 핵심 한계가 드러났습니다:

1. **기획 의도(Rationale)의 부재**:
   - 단순히 장르, BPM, 가사를 기계적으로 10개씩 양산하는 방식은 왜 이 조성(Key)과 악기를 선택했는지, 왜 이 파트에서 이 가사와 지시어가 나왔는지에 대한 음악적 근거를 제공하지 못함.
2. **단일 원장(Master)과 점진적 변형(Takes/Branches) 관리의 부재**:
   - 실제 작곡 과정은 [초안 스케치 -> 파트별 수정/변형 -> A/B 비교 청취 -> 최종 마스터 확정]의 반복 루프를 거치나, 기존 시스템은 단일 트랙 덮어쓰기 구조로 되어 있어 과거 실험 테이크의 이력 관리가 불가능함.
3. **단순 JSON 파일 저장소의 한계**:
   - 버전이 늘어나고 브랜치(Take 1, Take 2...)가 많아질수록 단일 `database.json`은 동시성 락 충돌, 부분 업데이트 비효율, 관계형 쿼리(부모-자식 트리 탐색, A/B Diff)의 한계에 직면함.
   - 반면 외부 대형 RDBMS(PostgreSQL/MySQL)는 파일 접근성을 해치고 운영 복잡도를 증가시킴.

---

## 2. Decision Drivers (결정 고려 요인)

1. **인간 중심의 파일 접근성**: 사용자가 윈도우 탐색기(`ZENION-MUSIC/`)에서 폴더를 열고 마스터 음원 및 테이크별 음원을 DAW/영상툴에 직접 끌어다 쓸 수 있어야 함.
2. **초고속 관계형 쿼리 & 트랜잭션 안전성**: 버전 트리 탐색, A/B 비교, 원장 승격(Merge) 시 데이터 무결성과 트랜잭션이 보장되어야 함.
3. **무설치 임베디드 경량성**: 별도의 외부 DB 서버를 띄우지 않고 Node.js 프로세스 내에서 zero-config로 동작해야 함.
4. **AI Co-Producer 인터랙션**: 자연어로 AI 프로듀서와 대화하며 특정 파트를 튜닝하고 새 브랜치를 분기할 수 있어야 함.

---

## 3. Considered Options (검토 대안)

* **Option 1: 100% 파일 기반 (JSON 파일 트리)**
  - 장점: 단순함.
  - 단점: 브랜치 간 Diff 검색, A/B 비교, 트랜잭션 롤백 시 파일 I/O 병목 및 동시성 락 충돌 위험.
* **Option 2: 외부 RDBMS 전용 (PostgreSQL / MySQL)**
  - 장점: 완벽한 SQL 쿼리.
  - 단점: 미디어 바이너리 저장 비효율, 윈도우 탐색기 직접 접근 불가, 별도 DB 서버 구동 부담.
* **Option 3 (선택됨): 하이브리드 듀얼 레이어 (SQLite + 로컬 마스터 볼트 실시간 미러링)**
  - **Layer 1 (인덱스 & 트랜잭션)**: 경량 임베디드 SQLite (`better-sqlite3`, `data/zenion_studio.sqlite`)
  - **Layer 2 (물리 패키지 & 미디어)**: 마스터 볼트 파일 시스템 (`ZENION-MUSIC/트랙명/master/`, `branches/take-xx/`)

---

## 4. Decision (아키텍처 결정)

우리는 **Option 3: 하이브리드 듀얼 레이어 (SQLite + Vault Storage Mirroring)** 및 **Music Git-Flow 브랜칭 모델**을 v0.2.0의 표준 아키텍처로 채택한다.

### 4.1. 스토리지 계층 구조 (Hybrid Dual-Layer)
1. **SQLite 임베디드 데이터베이스 (`data/zenion_studio.sqlite`)**:
   - `tracks` : Master 곡 메타데이터 및 활성 버전 정보
   - `track_branches` : Take별 ID, 부모 ID, 편곡 지시어, 가사, Rationale, 음원 경로
   - `branch_history` : Git 커밋과 유사한 버전 변경 및 승격(Merge) 이력
   - `agent_sessions` : AI Co-Producer와의 대화형 튜닝 세션 로그
2. **로컬 마스터 볼트 물리 디렉토리 (`ZENION-MUSIC/곡명_ID/`)**:
   - `master/` : 최종 승격된 마스터 음원(`master_audio.mp3`), 설계도(`recipe.json`), 릴리즈 키트(`release_kit.md`)
   - `branches/take-01_initial/`, `take-02_brass/` : 실험 테이크별 바이너리 음원 및 스냅샷

### 4.2. 음악 프로덕션 워크플로우 (Music Git-Flow)
* **Branching**: 사용자가 AI Co-Producer에게 'Verse 2 가사 수정 및 색소폰 솔로 추가'를 지시하면 기존 Master(또는 특정 Take)로부터 새 브랜치(`take-02`) 분기.
* **A/B Comparison**: Master와 Branch 간의 가사 Diff, 스타일 프롬프트 Diff, 오디오 파형을 나란히 놓고 비교 청취.
* **Merge to Master**: 마음에 드는 Branch를 버튼 하나로 `Master v2.0`으로 승격(Promote)하고 물리 `master/` 디렉토리에 동기화.

---

## 5. Consequences (영향 및 효과)

* **Positive (긍정적 효과)**:
  - 1곡을 완벽하게 다듬어가는 프로페셔널한 음악 창작 경험(DAW급 워크스테이션) 제공.
  - 실험적인 편곡/가사 시도가 원본을 훼손하지 않고 안전하게 브랜치로 보존됨.
  - 윈도우 탐색기 직접 접근성과 SQLite의 초고속 쿼리/트랜잭션 안전성을 동시에 확보.
* **Negative / Mitigation (고려사항 및 대응)**:
  - SQLite와 파일 시스템 간의 양방향 동기화 오버헤드 -> `VaultSyncService`를 통한 원자적(Atomic) 트랜잭션 래퍼로 불일치 방지.
