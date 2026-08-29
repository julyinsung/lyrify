# 🏛️ Lyrify Studio 시스템 아키텍처 및 데이터 흐름 가이드

> **개발자, 시스템 관리자, 아키텍트를 위한 3-Tier 엔드투엔드 API 흐름 및 하이브리드 스토리지 구조 명세서**

---

## 🗺️ 1. 엔드투엔드 아키텍처 및 출발지 / 목적지

시스템은 **[1. 브라우저 클라이언트] ➔ [2. Lyrify 백엔드 허브] ➔ [3. AI / DB / 볼트 파일 / Suno 연동]**의 계층으로 구성됩니다.

```
┌────────────────────────────────┐
│ 1. 출발지 (Client / Web UI)   │  브라우저 (http://localhost:3000)
│   • 스튜디오 콘솔              │  - 파트별 타임라인 에디터, AI 프로듀서 채팅, A/B 청음
└───────────────┬────────────────┘
                │ REST API (/api/...)
                ▼
┌────────────────────────────────┐
│ 2. 중계지 (Backend Hub)       │  Node.js / Express 서버 (Docker 컨테이너)
│   • Director & Vault Service   │  - 오케스트레이션, 트랜잭션, 파일 동기화
└───────────────┬────────────────┘
                │
  ┌─────────────┼──────────────────────────────┬────────────────────────────┐
  ▼             ▼                              ▼                            ▼
[목적지 1]    [목적지 2: SQLite DB]          [목적지 3: 마스터 볼트]      [목적지 4: Suno/FFmpeg]
☁️ Google    🗄️ data/zenion_studio.sqlite   📂 ZENION-MUSIC/             🌐 Suno.com (클립보드)
   Gemini SDK    - tracks (원장)                - master/ (최종 음원/가사)   🎬 Linux FFmpeg (:3000)
                 - track_branches (테이크)       - branches/take-xx/
                 - agent_sessions (채팅 로그)
```

---

## 🔄 2. 핵심 시나리오별 API 출발지 및 목적지

### 시나리오 1: 단일 곡 심층 기획 (`POST /api/director/deep-produce`)
* **출발지**: 브라우저 UI (`#deep-produce-btn`)
* **중계지**: `DirectorController` ➔ `DirectorService.deepProduceTrack()`
* **목적지 1 (AI)**: `GeminiProvider._generateStructuredRecipe()` (Google Gemini 2.0 Flash SDK)
* **목적지 2 (DB)**: `SqliteVaultRepository.insertTrack()` & `insertBranch()`
* **목적지 3 (스토리지)**: `VaultStorageService.createTrackVault()` ➔ `ZENION-MUSIC/곡명_ID/master/recipe.json`
* **반환**: 사운드 아키텍처(Rationale), 파트별 타임라인, Suno 마스터 프롬프트

### 시나리오 2: 음악 테이크 브랜치 분기 (`POST /api/tracks/:id/branches`)
* **출발지**: 브라우저 브랜치 생성 버튼 / AI Co-Producer 지시창
* **중계지**: `TracksController` ➔ `VaultStorageService.createTrackBranch()`
* **목적지 1 (DB)**: SQLite `track_branches` 테이블에 부모 테이크 ID를 연결하여 저장
* **목적지 2 (스토리지)**: `ZENION-MUSIC/곡명_ID/branches/take-02/` 물리 폴더 생성
* **반환**: 신규 생성된 브랜치 ID 및 스냅샷 데이터

### 시나리오 3: Master 원장 승격 / 병합 (`POST /api/tracks/:id/branches/:id/merge`)
* **출발지**: 브라우저 `[🌟 Master로 승격]` 버튼
* **중계지**: `TracksController` ➔ `VaultStorageService.mergeBranchToMaster()`
* **목적지 1 (DB)**: SQLite 트랜잭션 내에서 `tracks.active_version`을 갱신하고 `branch_history`에 승격 로그 기록
* **목적지 2 (스토리지)**: `ZENION-MUSIC/곡명_ID/master/` 디렉토리의 `recipe.json`, `master_audio.mp3`를 해당 테이크 파일로 원자적 교체
* **반환**: 확정된 Master v2.0 메타데이터

---

## 🗄️ 3. 하이브리드 듀얼 레이어 스토리지 모델

```
[Layer 1: SQLite 임베디드 데이터베이스] (data/zenion_studio.sqlite)
  ├── tracks (id, title, genre, bpm, active_version, rationale_json, created_at)
  ├── track_branches (id, track_id, parent_take_id, branch_name, lyrics_raw, style_prompt, audio_path)
  ├── branch_history (id, track_id, from_branch_id, to_branch_id, action_type, commit_msg)
  └── agent_sessions (id, track_id, user_prompt, agent_response, created_at)

[Layer 2: 마스터 볼트 물리 디렉토리] (C:\Users\julyi\Documents\ZENION-MUSIC\곡명_ID\)
  ├── master/                         <-- 최종 확정 원장
  │   ├── recipe.json                 (마스터 사운드 설계도 & 가사)
  │   ├── master_audio.mp3            (최종 승격된 고품질 음원)
  │   └── release_kit.md              (SNS 릴리즈 키트)
  └── branches/                       <-- 실험 테이크들
      ├── take-01_initial_sketch/     (초안 스케치)
      └── take-02_brass_build/        (브라스 보강 버전)
```
