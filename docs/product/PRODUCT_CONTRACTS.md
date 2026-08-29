# Product Contracts

---
document_id: PROD-CONTRACT
title: Product Contracts
title_ko: 제품 구현 계약 인덱스
project: lyrify
profile: product
gate_scope: gate2-impl
status: Draft
version: v0.3
owner_role: Technical Architect
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-08-27
related_documents:
  - docs/product/PRODUCT_BRIEF.md
  - docs/product/PRODUCT_ARCHITECTURE.md
---

## 1. Contract Policy

이 문서는 상세 설계서 복사본이 아니라 Product profile의 구현 계약 진입점이다.
상세 API/DB/UI/보안 설계가 필요한 경우 `docs/artifacts/02-design/` 산출물로 분리하고, 이 문서에서는 링크와 핵심 계약만 유지한다.

## 2. API Contracts

| API ID | Method | Path / Entry | Request | Response | 관련 Scenario | 상세 문서 / 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| API-001 | POST | `/api/director/generate-styles` | `JSON` (`{ keyword: "string", count?: number, mode?: "explore" \| "single" \| "album", provider?: "gemini" \| "openai" \| "ollama" }`) | `JSON` (`{ success: true, styles: [{ id, title, genre, bpm, instruments, lyricTheme, lyrics: { verse1, chorus, verse2 }, promptText }] }`) | SCN-001 | AI 디렉터 가변 스타일(1~20곡) 및 가사 레시피 기획 |
| API-002 | GET | `/api/tracks` | None | `JSON` (`{ tracks: [{ id, title, aiScore, aiReview, ranking, draftAudio, sunoAudio, coverImage, releaseKit }] }`) | SCN-002 | 트랙 목록 및 AI 랭킹 조회 |
| API-003 | POST | `/api/tracks/:id/evaluate` | `JSON` (`{ audioPath?: "string", lyrics?: "string" }`) | `JSON` (`{ success: true, aiScore: number, aiReview: string, techCheck: { clipping: boolean, silence: boolean } }`) | SCN-002 | 초안 오디오/가사 AI 품질 1차 채점 |
| API-004 | POST | `/api/tracks/:id/map-suno` | `JSON` (`{ sunoAudioPath: "string", targetFolder?: "string" }`) | `JSON` (`{ success: true, zenionTrackPath: "string", mappedFiles: object }`) | SCN-003 | Suno 음원 매핑 및 `ZENION-MUSIC` 폴더 구조화 |
| API-005 | POST | `/api/tracks/:id/generate-image` | `JSON` (`{ useApi: boolean, customPrompt?: "string" }`) | `JSON` (`{ success: true, imageUrl: "string" }`) | SCN-004 | AI 썸네일 또는 로컬 템플릿 커버 생성 |
| API-006 | POST | `/api/tracks/:id/export-video` | `JSON` (`{ format: "youtube_16x9" \| "shorts_9x16" \| "all", audioType: "suno" \| "ace" }`) | `JSON` (`{ success: true, jobId: "string", videoUrls: object }`) | SCN-004 | 16:9 유튜브 및 9:16 숏폼 비디오 렌더링 |
| API-007 | GET | `/api/tracks/:id/release-kit` | None | `JSON` (`{ youtube: { title, description, tags, timestampLyrics }, instagram: { caption, hashtags }, tiktok: { caption, hashtags } }`) | SCN-005 | SNS 플랫폼별 릴리즈 키트 조회 |
| API-008 | POST | `/api/tracks/:id/sync` | `timeline` JSON | `{success: true, track: Object}` | 가사 타임라인 싱크 정보 저장 및 마스터 볼트 동기화 |
| API-009 | POST | `/api/director/deep-produce` | `{story, mood, reference, targetGenre, bpm}` | `{success: true, track: Object, blueprint: Object, rationale: Object}` | [v0.2.0] 단일 곡 심층 사운드 아키텍처 및 파트별 편곡 의도 기획 |
| API-010 | POST | `/api/tracks/:id/branches` | `{parentTakeId, branchName, description}` | `{success: true, branchId: string, branch: Object}` | [v0.2.0] 신규 음악 테이크 브랜치 분기 생성 |
| API-011 | POST | `/api/tracks/:id/branches/:branchId/merge` | `{commitMessage: string}` | `{success: true, masterVersion: string, track: Object}` | [v0.2.0] 특정 브랜치 테이크를 Master 원장으로 승격 및 확정 |
| API-012 | GET | `/api/tracks/:id/compare` | Query: `?a=master&b=take-02` | `{success: true, diff: {lyricsDiff, styleDiff, audioDiff}}` | [v0.2.0] 두 테이크 간의 가사, 스타일 태그, 오디오 A/B 비교 데이터 반환 |
| API-013 | POST | `/api/agent/co-produce` | `{trackId, branchId, userInstruction}` | `{success: true, suggestion: Object, tunedBranch: Object}` | [v0.2.0] AI Co-Producer Agent 대화형 편곡/작사 튜닝 및 지시 |

## 2. Program Contracts (Facade/Domain)

| Interface/Class | Method | Signature | 설명 |
| --- | --- | --- | --- |
| `DirectorService` | `generateStyles` | `(params: {keyword, count, mode}) => Promise<Object>` | AI 디렉터 가변 곡수 및 3대 모드 레시피 기획 |
| `DirectorService` | `deepProduceTrack` | `(params: {story, mood, reference}) => Promise<Object>` | [v0.2.0] 1곡 집중 사운드 아키텍처 & Rationale 설계 |
| `VaultStorageService`| `createTrackBranch`| `(trackId, branchData) => Promise<Object>` | [v0.2.0] 신규 테이크 브랜치 생성 및 물리 볼트 미러링 |
| `VaultStorageService`| `mergeBranchToMaster`| `(trackId, branchId) => Promise<Object>` | [v0.2.0] 브랜치 테이크의 Master 승격 및 동기화 |
| `QualityJudgeService`| `evaluateTrack` | `(trackId: string, options: Object) => Promise<Object>` | ACE/Suno 오디오 기술 결함 및 가사 1차 채점 |
| `VideoRenderService` | `renderTrackVideo` | `(trackId: string, options: {format}) => Promise<Object>` | 16:9/9:16 비디오 렌더링 파이프라인 |
| `ReleaseKitService` | `generateReleaseKit`| `(trackId: string) => Promise<Object>` | SNS 릴리즈 키트 생성 및 release_kit.md 저장 |

## 3. Data Contracts

| DATA ID | 엔티티/스키마 | 저장 위치 / 포맷 | 설명 |
| --- | --- | --- | --- |
| DATA-001 | Track Master Schema | `ZENION-MUSIC/[곡명]_[ID]/recipe.json` | 개별 트랙 메타데이터, BPM, 가사, 자산 상태, AI 채점 결과 |
| DATA-002 | Master Database Index | `data/database.json` | 전체 트랙 색인 및 메타데이터 동기화 캐시 |
| DATA-003 | SQLite Hybrid Engine | `data/zenion_studio.sqlite` | [v0.2.0] 트랙 원장(`tracks`), 테이크 브랜치(`track_branches`), 이력(`branch_history`), 에이전트 세션(`agent_sessions`) 관계형 스토리지 |

## 4. UI Contracts

| UI/SCR ID | 화면/상호작용 | 주요 상태 및 컴포넌트 | 관련 Scenario | 검증 |
| --- | --- | --- | --- | --- |
| UI-001 | 메인 대시보드 (AI Screening & Vault) | Empty / Loading / Success (100점 만점 AI 품질 뱃지, TOP 추천 태그, 파형 미니 플레이어, ACE vs Suno 토글) | SCN-002 | Playwright / 육안 검증 |
| UI-002 | AI 디렉터 기획 스위트 | Empty (키워드 입력) / Generating (10종 생성) / Ready (10종 스타일 레시피 카드 프리뷰 & ACE 원클릭 트리거) | SCN-001 | UI 기능 검증 |
| UI-003 | 트랙 상세 & 비디오 스튜디오 | 듀얼 파형 A/B 청음, 가사 타임라인 싱크([Verse]/[Chorus]), AI 커버 썸네일, 16:9/9:16 비디오 원클릭 인코딩 | SCN-003, SCN-004 | 수동/자동 검증 |
| UI-004 | SNS 원클릭 릴리즈 키트 허브 | YouTube/Instagram/TikTok 탭별 제목, 설명문, 해시태그, 타임스탬프 원클릭 복사 & ZENION 로컬 폴더 열기 | SCN-005 | 클립보드 복사 검증 |
| UI-005 | 스튜디오 콘솔 & 타임라인 에디터 | [v0.2.0] 사운드 아키텍처 Rationale 뷰, [Intro~Outro] 파트별 시각적 타임라인 카드, Suno Style/Lyrics/Negative 일체형 마스터 패키지 | SCN-006 | UI 기능 검증 |
| UI-006 | 버전 트리 & A/B 비교 스튜디오 | [v0.2.0] Master vs Branch 트리 그래프, A/B 파형 및 가사 Diff 뷰어, 원장 승격(Merge) 버튼, AI Co-Producer 대화창 | SCN-007, SCN-008 | UI 기능 검증 |

## 5. Security Contracts

Product profile의 보안 계약은 `docs/core/PRODUCT_PROFILE_BASELINE.md`, `docs/core/SECURITY_BASELINE.md`, `docs/core/REFERENCE_STANDARDS.md`를 기준으로 작성한다.
KISA/SR 매핑은 선택 참고이지만, OWASP/CWE 기반의 제품 보안 판단은 비워두지 않는다.

| SEC ID | 보안 계약 | 적용 대상 | 기준/참조 | 관련 Scenario | 검증 |
| --- | --- | --- | --- | --- | --- |
| SEC-001 | Google API Key 노출 방지 (소스코드 및 원격 저장소 하드코딩 영구 배제) | DATA-002, API-005 | OWASP Top 10 A02:2021, CWE-798 | SCN-004 | SEC-REG-001 |
| SEC-002 | 경로 트래버설 취약점 방지 (`ZENION-MUSIC` 및 작업 디렉토리 외부 탈출 금지) | API-004, API-006 | OWASP ASVS V5, CWE-22 | SCN-001 ~ SCN-005 | SEC-REG-001 |

## 6. Security And Data Baseline

| 항목 | 기준 | 적용 위치 | 검증 |
| --- | --- | --- | --- |
| Security | docs/core/PRODUCT_PROFILE_BASELINE.md, docs/core/SECURITY_BASELINE.md | GCP API Key 로컬 세팅 격리 (`.env`), 로컬 경로 검증 모듈 | REG-001 |
| Data | docs/core/DATA_STANDARD_RULES.md | database.json 스키마 표준 정의 | REG-001 |

## 7. Contract Gaps

| Gap ID | 내용 | 영향 | 후속 판단 |
| --- | --- | --- | --- |
| GAP-001 | 비디오 인코딩 백엔드 진행 상태 실시간 통신 방식 필요 | HTTP POST의 1회성 응답만으로는 FFmpeg 렌더링 진행률(%)을 대시보드에 실시간 표시하기 어려움 | SSE(Server-Sent Events) 프로토콜 또는 프론트엔드의 1초 주기 주기적 폴링(Polling) API 추가 도입 |
