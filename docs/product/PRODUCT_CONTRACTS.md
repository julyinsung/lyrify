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
| API-001 | POST | `/api/director/generate-styles` | `JSON` (`{ keyword: "string", count?: 10 }`) | `JSON` (`{ success: true, styles: [{ id, genre, bpm, instruments, lyricTheme, promptText }] }`) | SCN-001 | AI 디렉터 10종 스타일 레시피 기획 |
| API-002 | GET | `/api/tracks` | None | `JSON` (`{ tracks: [{ id, title, aiScore, aiReview, ranking, draftAudio, sunoAudio, coverImage, releaseKit }] }`) | SCN-002 | 트랙 목록 및 AI 랭킹 조회 |
| API-003 | POST | `/api/tracks/:id/evaluate` | `JSON` (`{ audioPath?: "string", lyrics?: "string" }`) | `JSON` (`{ success: true, aiScore: number, aiReview: string, techCheck: { clipping: boolean, silence: boolean } }`) | SCN-002 | 초안 오디오/가사 AI 품질 1차 채점 |
| API-004 | POST | `/api/tracks/:id/map-suno` | `JSON` (`{ sunoAudioPath: "string", targetFolder?: "string" }`) | `JSON` (`{ success: true, zenionTrackPath: "string", mappedFiles: object }`) | SCN-003 | Suno 음원 매핑 및 `ZENION-MUSIC` 폴더 구조화 |
| API-005 | POST | `/api/tracks/:id/generate-image` | `JSON` (`{ useApi: boolean, customPrompt?: "string" }`) | `JSON` (`{ success: true, imageUrl: "string" }`) | SCN-004 | AI 썸네일 또는 로컬 템플릿 커버 생성 |
| API-006 | POST | `/api/tracks/:id/export-video` | `JSON` (`{ format: "youtube_16x9" \| "shorts_9x16" \| "all", audioType: "suno" \| "ace" }`) | `JSON` (`{ success: true, jobId: "string", videoUrls: object }`) | SCN-004 | 16:9 유튜브 및 9:16 숏폼 비디오 렌더링 |
| API-007 | GET | `/api/tracks/:id/release-kit` | None | `JSON` (`{ youtube: { title, description, tags, timestampLyrics }, instagram: { caption, hashtags }, tiktok: { caption, hashtags } }`) | SCN-005 | SNS 플랫폼별 릴리즈 키트 조회 |
| API-008 | POST | `/api/tracks/:id/sync` | `JSON` (`{ timeline: [{ part: "string", startSecond: number }] }`) | `JSON` (`{ success: true, updatedTimeline: array }`) | SCN-004 | 가사 타임라인 싱크 저장 |

## 3. Data Contracts

| DATA/DB ID | 이름 | 주요 필드 | 보안 분류 | 관련 API/Scenario | 상세 문서 / 설명 |
| --- | --- | --- | --- | --- | --- |
| DATA-001 | database.json | `id`, `title`, `bpm`, `genre`, `lyricsRaw`, `aiScore`, `aiReview`, `audioPathAceStep`, `audioPathSuno`, `coverImageUrl`, `timeline`, `releaseKit` | 일반 | API-001 ~ API-008 | 로컬 트랙 메타데이터 DB |
| DATA-002 | config.json | `zenionRootDirectory` (`/data/ZENION-MUSIC`), `aceWatchDirectory` (`/data/ACE-Step-1.5`), `googleApiKey` | 인증정보 | API-001, API-004, API-005, API-006 | Docker 볼륨 마운트 및 앱 환경설정 파일 (GCP Key 포함) |

## 4. UI Contracts

| UI/SCR ID | 화면/상호작용 | 주요 상태 및 컴포넌트 | 관련 Scenario | 검증 |
| --- | --- | --- | --- | --- |
| UI-001 | 메인 대시보드 (AI Screening & Vault) | Empty / Loading / Success (100점 만점 AI 품질 뱃지, TOP 추천 태그, 파형 미니 플레이어, ACE vs Suno 토글) | SCN-002 | Playwright / 육안 검증 |
| UI-002 | AI 디렉터 기획 스위트 | Empty (키워드 입력) / Generating (10종 생성) / Ready (10종 스타일 레시피 카드 프리뷰 & ACE 원클릭 트리거) | SCN-001 | UI 기능 검증 |
| UI-003 | 트랙 상세 & 비디오 스튜디오 | 듀얼 파형 A/B 청음, 가사 타임라인 싱크([Verse]/[Chorus]), AI 커버 썸네일, 16:9/9:16 비디오 원클릭 인코딩 | SCN-003, SCN-004 | 수동/자동 검증 |
| UI-004 | SNS 원클릭 릴리즈 키트 허브 | YouTube/Instagram/TikTok 탭별 제목, 설명문, 해시태그, 타임스탬프 원클릭 복사 & ZENION 로컬 폴더 열기 | SCN-005 | 클립보드 복사 검증 |

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
