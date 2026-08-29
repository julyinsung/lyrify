# Product Brief

---
document_id: PROD-BRIEF
title: Product Brief
title_ko: 제품/업무 앱 개요
project: lyrify
profile: product
gate_scope: phase0-gate1
status: Draft
version: v0.2
owner_role: Product Owner
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-08-27
---

## 1. Product Goal

| 항목 | 내용 |
| --- | --- |
| 목표 | AI 음악 크리에이터(@zenion.studio 등)를 위해, 감성 키워드 입력만으로 다양한 세부 스타일 레시피(기본 10종 및 단일/앨범 모드 가변)를 다각도로 기획(AI 디렉터)하고, ACE-Step 초안 생성 및 AI 1차 퀄리티 스크리닝(오디오/가사 100점 만점 채점), 상업용 Suno AI 유료 완성 음원 매핑, `C:\Users\julyi\Documents\ZENION-MUSIC` 로컬 저장소 자산 구조화, 캡컷을 대체하는 멀티 플랫폼 비디오(16:9 유튜브 롱폼 & 9:16 인스타/틱톡 숏폼) 렌더링 및 SNS 릴리즈 키트를 원스톱으로 관리/생성하는 올인원 크리에이터 스튜디오 구축 |
| 주요 사용자 | AI 음악을 기획/제작하고 이를 유튜브, 인스타그램 릴스, 틱톡 등의 소셜 채널에 체계적으로 배포하려는 전문 크리에이터 |
| 해결하려는 문제 | 1. 음악 이론/스타일 지식 부족으로 반복적인 프롬프트 작성 및 초안 청음 선별에 막대한 시간이 소요됨.<br>2. ACE-Step 초안, Suno AI 유료 완성 음원, 커버 이미지, 메타데이터가 파편화되어 로컬 관리(`ZENION-MUSIC`)가 어려움.<br>3. 매번 캡컷 등 무거운 영상 편집기를 켜서 16:9 및 9:16 비디오를 수동 편집하고 SNS 설명문/해시태그를 일일이 작성하는 수작업 피로도 극심. |
| 성공 기준 | 1. 감성 키워드로 가변 스타일 레시피(기본 10종, 단일/앨범 모드) 자동 기획 및 ACE-Step 초안 연계.<br>2. ACE 초안 생성 시 오디오 결함 및 가사 완결성을 AI가 1차 채점하여 상위 TOP 3 후보를 대시보드에 랭킹 추천.<br>3. 선별된 곡의 Suno AI 완성 음원 매핑 및 `ZENION-MUSIC` 폴더 내 곡별 자산(음원, 커버, 영상, 메타데이터) 자동 구조화 정리.<br>4. 로컬 FFmpeg 기반 유튜브 롱폼(16:9) 및 숏폼(9:16) 가사 비디오 원클릭 렌더링 및 SNS 릴리즈 키트(제목/설명/해시태그) 원클릭 복사 제공. |
| 비목표 | 1. 클라우드 멀티유저 계정 시스템 (로컬 싱글 크리에이터 PC 환경에 최적화).<br>2. 유튜브/인스타/틱톡 직접 API 자동 업로드 (1단계 MVP는 완성 비디오 파일 및 업로드용 릴리즈 키트 로컬 생성/복사에 집중).<br>3. Suno AI 웹 자동 크롤러/다운로더 (Suno AI 웹에서 생성된 음원은 사용자가 로컬 폴더에 다운로드하여 매핑하는 방식). |

## 2. Core Scenarios

| Scenario ID | 시나리오 | 사용자 가치 | 우선순위 | 관련 REQ |
| --- | --- | --- | --- | --- |
| SCN-001 | AI 음악 디렉터 & 가변 스타일 기획 | 복잡한 음악 이론 없이 감성 키워드 하나로 1~20곡의 가변 음악 스타일 레시피(탐색/단일/앨범 모드)를 즉시 자동 생성함 | Must | REQ-001 |
| SCN-002 | ACE 초안 감지 및 AI 1차 퀄리티 스크리닝 | 대량 생성된 ACE 초안 음원들을 AI가 오디오 파형과 가사 완성도로 채점하여 랭킹 및 TOP 3 추천을 제공, 청음 선별 시간을 90% 단축함 | Must | REQ-001 |
| SCN-003 | Suno AI 음원 매핑 및 ZENION-MUSIC 자산 구조화 | 선별된 곡의 Suno AI 음원을 1:1 매핑하고 `ZENION-MUSIC` 로컬 폴더에 곡별 전용 폴더로 음원/가사/메타데이터를 자동 구조화 저장함 | Must | REQ-002 |
| SCN-004 | AI 비주얼 합성 및 멀티 플랫폼 비디오 렌더링 | 캡컷 없이 유튜브 롱폼(16:9) 및 인스타/틱톡 숏폼(9:16) 가사 비디오를 로컬 FFmpeg로 원클릭 렌더링함 | Must | REQ-003 |
| SCN-005 | SNS 멀티 플랫폼 릴리즈 키트 생성 | 유튜브/인스타/틱톡 업로드에 필요한 최적의 제목, 설명문, 추천 해시태그, 타임스탬프 가사를 원클릭 복사할 수 있음 | Must | REQ-003 |

## 3. Release Scope

| 구분 | 내용 |
| --- | --- |
| 이번 릴리즈 포함 (MVP) | 1. 감성 키워드 기반 10종 스타일 레시피 자동 기획(AI 디렉터) 기능.<br>2. ACE 초안 파일 감지 및 AI 1차 품질 채점(100점 만점)/랭킹 추천 대시보드.<br>3. Suno AI 음원 매핑, 듀얼 비교 청음 및 `ZENION-MUSIC` 폴더 자산 자동 구조화 정리.<br>4. AI 커버 썸네일 생성 및 유튜브(16:9), 숏폼(9:16) 멀티 포맷 비디오 렌더링.<br>5. SNS 멀티 플랫폼(유튜브/인스타/틱톡) 배포용 릴리즈 키트 원클릭 복사 기능. |
| 이번 릴리즈 제외 | 1. 유튜브/인스타/틱톡 API 자동 업로드 연동.<br>2. Suno AI 웹 브라우저 자동화 크롤러. |
| 다음 릴리즈 후보 | 1. 유튜브/틱톡 API 직접 업로드 및 예약 발행 기능.<br>2. Suno AI 웹 자동 다운로더 확장. |

## 4. Product Risks And Assumptions

| ID | 유형 | 내용 | 대응 |
| --- | --- | --- | --- |
| RISK-001 | Risk | ACE-Step 결과물 파일 명명 규칙이나 폴더 구조가 달라질 경우 파싱 오류 발생 가능성 | 애플리케이션 설정(`config.json`)을 통해 ACE 감시 경로 및 ZENION-MUSIC 루트 경로를 유연하게 변경 가능하도록 설계 |
| RISK-002 | Assumption | 로컬 동영상(MP4) 16:9 및 9:16 렌더링을 위해 로컬 시스템에 FFmpeg 설치가 필수적임 | 서버 기동 시 로컬 FFmpeg 설치 여부를 유효성 검사하고, 대시보드 내 설치 상태 확인 및 알림 제공 |
| RISK-003 | Risk | 이미지 생성 API 연동 실패 시 비주얼 제작 차단 가능성 | Google Imagen API 실패 또는 미설정 시에도 로컬 그라데이션 텍스트 오버레이 템플릿으로 썸네일/배경을 자동 폴백 생성 |

## 5. Requirements

### 5.1 기능 요구사항 (Functional Requirements)

| REQ ID | 요구사항명 | 상세 설명 | 우선순위 | 상태 | 관련 Scenario |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | AI 스타일 기획 및 초안 품질 스크리닝 | 감성 키워드 기반 10종 세부 스타일 레시피 자동 생성(AI 디렉터) 및 ACE 초안 음원/가사 AI 1차 채점(100점)과 랭킹 뷰 제공 | Must | Draft | SCN-001, SCN-002 |
| REQ-002 | Suno 음원 매핑 및 ZENION-MUSIC 자산 관리 | Suno AI 완성 음원 1:1 매핑, 듀얼 비교 청음, `ZENION-MUSIC` 로컬 폴더 내 곡별 자산(음원, 가사, 커버, 메타데이터) 자동 구조화 저장 | Must | Draft | SCN-003 |
| REQ-003 | 멀티 플랫폼 비디오 렌더링 및 SNS 배포 키트 | 유튜브 롱폼(16:9) 및 숏폼(9:16) 가사 비디오 원클릭 인코딩(FFmpeg) 및 SNS 업로드용 제목/설명/해시태그 릴리즈 키트 생성 | Must | Draft | SCN-004, SCN-005 |

### 5.2 인수 기준 (Acceptance Criteria)

| AC ID | 관련 REQ | 인수 기준 설명 | 검증 방법 | 상태 |
| --- | --- | --- | --- | --- |
| AC-001-01 | REQ-001 | 사용자가 감성 키워드 입력 시 장르, BPM, 악기 구성, 가사 테마가 포함된 10종의 세부 스타일 레시피를 생성하고 이를 `music_recipes.md` 또는 프롬프트 카드로 출력해야 한다. | 스타일 레시피 생성 및 다양성 검증 | Draft |
| AC-001-02 | REQ-001 | ACE 초안 파일 감지 시 오디오 파형(볼륨/클리핑/무음) 및 가사 구조를 분석하여 100점 만점 점수와 AI 리뷰를 부여하고 점수 순으로 랭킹 정렬해야 한다. | AI 퀄리티 스코어링 알고리즘 및 랭킹 정렬 검증 | Draft |
| AC-002-01 | REQ-002 | `ZENION-MUSIC` 폴더 내에 곡별 전용 디렉토리를 생성하고 초안 음원, Suno 완성 음원, 커버 이미지, 메타데이터(`metadata.json`)를 자동 정리하여 영구 저장해야 한다. | 로컬 파일 시스템 구조화 저장 검증 | Draft |
| AC-002-02 | REQ-002 | 대시보드 내장 플레이어를 통해 각 곡의 초안(ACE)과 최종 완성 음원(Suno)을 선택 전환하여 비교 청음할 수 있어야 한다. | 오디오 플레이어 전환 청음 테스트 | Draft |
| AC-003-01 | REQ-003 | 생성형 이미지 API(Google Imagen 등) 또는 로컬 그라데이션 템플릿을 통해 썸네일 커버 이미지를 자동 생성해야 한다. | 썸네일 생성 및 폴백 템플릿 렌더링 검사 | Draft |
| AC-003-02 | REQ-003 | 로컬 FFmpeg를 제어하여 유튜브용 롱폼(16:9)과 인스타/틱톡용 숏폼(9:16) 가사 비디오(MP4)를 선택 또는 일괄 렌더링할 수 있어야 한다. | 16:9 및 9:16 MP4 비디오 렌더링 및 해상도/재생 검증 | Draft |
| AC-003-03 | REQ-003 | 각 곡 상세 화면에서 유튜브, 인스타그램, 틱톡 맞춤 최적 제목, 설명문, 추천 해시태그, 타임스탬프 가사를 원클릭 복사할 수 있는 릴리즈 키트를 제공해야 한다. | SNS 릴리즈 키트 생성 및 클립보드 복사 검증 | Draft |

### 5.3 비기능 요구사항 (Non-Functional Requirements)

| NREQ ID | 요구사항명 | 상세 설명 | 우선순위 | 상태 |
| --- | --- | --- | --- | --- |
| NREQ-001 | 사용성 및 성능 기준 | 파일 변경 실시간 감시 반응(2초 이내), 동영상 인코딩 진행률 표시, 로컬 FFmpeg 부재 시 환경 경고 가이드 노출 | Should | Draft |

| AC ID | 관련 NREQ | 인수 기준 설명 | 검증 방법 | 상태 |
| --- | --- | --- | --- | --- |
| AC-N001-01 | NREQ-001 | `music_recipes.md` 수정 또는 신규 초안 생성 후 대시보드에 업데이트된 카드가 반영되는 시간은 2초 이내여야 한다. | 파일 변경 이벤트 반응 속도 측정 테스트 | Completed |
| AC-N001-02 | NREQ-001 | 로컬 동영상 인코딩 수행 시, 실시간 진행 상태(Progress %)를 사용자에게 직관적으로 제공해야 한다. | UI 상태 트래킹 검증 | Completed |
| AC-N001-03 | NREQ-001 | 로컬 시스템에 FFmpeg가 미설치되어 있을 경우, 대시보드에 설치 필요 알림 및 가이드를 화면에 노출해야 한다. | FFmpeg 의존성 유효성 검사 및 UI 알림 검증 | Completed |

---

## 5. [v0.2.0] 신규 시나리오 및 요구사항 정의 (Deep Production & Music Git-Flow)

### 5.1. v0.2.0 핵심 시나리오 (Use Cases)
| 시나리오 ID | 시나리오명 | 액터 | 사전 조건 | 주 흐름 (Main Flow) | 사후 결과 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SCN-006** | 단일 곡 심층 기획 및 사운드 아키텍처(Rationale) 설계 | 음악 크리에이터 / 디렉터 | Lyrify 스튜디오 실행 | 1. 스토리/감정선/레퍼런스를 입력하여 1곡 집중 기획 요청<br>2. AI가 BPM, 조성(Key), 악기 편성, 보컬 캐릭터 선정 "이유(Rationale)"와 [Intro~Outro] 파트별 편곡 의도를 도출 | 1곡 전용 종합 음악 기획서(Sound Blueprint) 생성 |
| **SCN-007** | 음악 버전 관리(Take Branching) 및 A/B 비교 청취 | 음악 크리에이터 | 트랙 스케치(Master v1.0) 존재 | 1. 특정 테이크에서 브랜치 생성(`take-02_brass`)<br>2. 브랜치에서 가사/편곡 지시어 수정 후 Suno 생성<br>3. Master와 Branch의 가사/스타일 Diff 및 오디오 A/B 비교<br>4. 마음에 드는 테이크를 Master로 승격(Merge) | 트랙 원장(Master)이 v2.0으로 갱신되고 물리 볼트에 보존 |
| **SCN-008** | AI Co-Producer Agent와의 대화형 점진적 튜닝 | 음악 크리에이터 | 특정 브랜치 활성화 | 1. 지시창에 "Chorus에 브라스 추가하고 Verse 2 가사 수정해줘" 자연어 입력<br>2. AI Agent가 지시사항을 반영한 신규 브랜치 및 튜닝된 Suno 프롬프트 제안 | 인간과 AI의 대화형 점진적 편곡 완성 |

### 5.2. v0.2.0 기능 요구사항 (Functional Requirements)
| 요구사항 ID | 요구사항명 | 상세 설명 | 우선순위 | 상태 |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-004** | Rationale 기반 파트별 편곡 타임라인 및 Suno 마스터 패키징 | • 곡의 음악이론적 선택 이유(Rationale) 명시<br>• [Intro~Outro] 각 파트별 [편곡 의도 + 연주 지시어 + 한글 가사 + 보컬 큐] 시각적 타임라인 편집<br>• Suno v3.5~v5.x Style Box, Lyrics Box, Negative Prompt, Extend/Inpaint 팁 일체형 패키징 | Must | Proposed (v0.2) |
| **REQ-005** | Music Git-Flow 브랜칭 및 하이브리드 SQLite 스토리지 엔진 | • 마스터 원장(Master)과 실험 브랜치(Takes) 버전 관리<br>• SQLite(`better-sqlite3`) 임베디드 DB를 통한 초고속 트리 쿼리 및 트랜잭션 관리<br>• 로컬 마스터 볼트(`ZENION-MUSIC/트랙명/master/`, `branches/take-xx/`) 물리 폴더 실시간 미러링 | Must | Proposed (v0.2) |

### 5.3. v0.2.0 인수 기준 (Acceptance Criteria)
| AC ID | 관련 REQ | 인수 기준 설명 | 검증 방법 | 상태 |
| :--- | :--- | :--- | :--- | :--- |
| **AC-004-01** | REQ-004 | 1곡 심층 기획 시 BPM, 조성, 악기 편성의 음악적 이유(Rationale)와 파트별 편곡 의도가 포함된 JSON 객체가 생성되어야 한다. | `POST /api/director/deep-produce` 단위 테스트 | Proposed |
| **AC-004-02** | REQ-004 | 타임라인 상에서 파트별 가사 및 편곡 지시어를 개별 수정하고 마스터 볼트에 저장할 수 있어야 한다. | 타임라인 에디터 API 테스트 | Proposed |
| **AC-004-03** | REQ-004 | Suno Style of Music, Lyrics, Negative Prompt를 원클릭으로 분리 복사할 수 있어야 한다. | UI 클립보드 복사 검증 | Proposed |
| **AC-005-01** | REQ-005 | 특정 트랙에서 신규 테이크 브랜치를 생성하면 SQLite와 로컬 볼트 `branches/take-xx/` 폴더가 동시 생성되어야 한다. | `POST /api/tracks/:id/branches` 테스트 | Proposed |
| **AC-005-02** | REQ-005 | 두 테이크(또는 Master와 Take) 간의 가사 및 스타일 프롬프트 Diff를 비교 조회할 수 있어야 한다. | `GET /api/tracks/:id/compare` 테스트 | Proposed |
| **AC-005-03** | REQ-005 | 브랜치 승격(Merge) 실행 시 해당 테이크가 원장(Master)으로 승격되고 `master/` 디렉토리 파일이 갱신되어야 한다. | `POST /api/tracks/:id/branches/:id/merge` 테스트 | Proposed |

