# Run 001: Build Wave BW-000 Scaffold & Docker Environment Setup

---
document_id: RUN-001
title: Build Wave BW-000 Scaffold & Docker Environment Setup
title_ko: BW-000 스캐폴드 및 Docker 실행 환경 구축
project: lyrify
profile: product
gate_scope: impl
status: Completed
version: v0.1
owner_role: Build Worker
author: Build Worker (Scaffold - Environment Builder)
reviewer: Orchestrator
approver: User
created_at: 2026-08-27
updated_at: 2026-08-27
related_documents:
  - docs/product/PRODUCT_BRIEF.md
  - docs/product/PRODUCT_CONTRACTS.md
  - docs/product/PRODUCT_ARCHITECTURE.md
  - docs/product/PRODUCT_TRACEABILITY.md
  - docs/product/REGRESSION_AND_RELEASE_REPORT.md
---

## 1. Run Input Contract

```yaml
run_id: RUN-001
persona: build
skill: implementation-scaffold
run_type: ImplementationScaffold
gate: impl
goal: "Node 20 LTS 기반 Express 헥사고날 프로젝트 스캐폴드, Dockerfile/Compose 환경, 코어 도메인/서비스/어댑터 스켈레톤 및 헬스체크 검증 완료"

related_ids:
  req: [REQ-001, REQ-002, REQ-003]
  ac: [AC-001-01, AC-001-02, AC-002-01, AC-002-02, AC-003-01, AC-003-02, AC-003-03, AC-N001-01, AC-N001-02, AC-N001-03]
  func: [FUNC-001, FUNC-002, FUNC-003, FUNC-004, FUNC-005]
  api: [API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008]
  db: [DATA-001, DATA-002]
  sec: [SEC-001, SEC-002]
  test: [REG-001, REG-002, REG-003, REG-004, REG-005, SEC-REG-001, SEC-REG-002]

target_contracts:
  func: [FUNC-001, FUNC-002, FUNC-003, FUNC-004, FUNC-005]
  api: [API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008]
  db: [DATA-001, DATA-002]
  sec: [SEC-001, SEC-002]
  test: [REG-001, REG-002, REG-003, REG-004, REG-005, SEC-REG-001, SEC-REG-002]
  interface_contract:
    language: "javascript (ES Modules, Node.js 20 LTS)"
    signatures:
      - "class Track { constructor(params); updateEvaluation(score, review, techCheck); mapSunoAudio(path); setTimeline(timeline); setReleaseKit(kit); toJSON(); }"
      - "class VaultStorageService { constructor({ vaultRepository }); listTracks(); getTrack(id); saveTrack(track); mapSunoTrack(trackId, options); }"
      - "class DirectorService { constructor({ geminiProvider }); generateStyles({ keyword, count, mode, provider }); triggerAceDraft(recipeId, recipeData); }"
      - "class QualityJudgeService { constructor({ ffmpegEncoder, geminiProvider, vaultService }); evaluateTrack(trackId, options); rankTracks(tracks); }"
      - "class VideoRenderService { constructor({ ffmpegEncoder, vaultService }); generateCoverImage(trackId, options); exportVideo(trackId, options); getEncodingStatus(jobId); }"
      - "class ReleaseKitService { constructor({ vaultService }); generateReleaseKit(trackId); getReleaseKit(trackId); }"
      - "class GeminiProvider { constructor(config); isConfigured(); generateStyleRecipes(options); evaluateQuality(options); }"
      - "class FFmpegVideoEncoder { constructor(); checkAvailability(); analyzeAudioTech(path); renderVideo(options); getJobStatus(jobId); }"
      - "class ZenionVaultRepository { constructor(config); loadAll(); findById(id); save(track); delete(id); isSafePath(targetPath); createTrackFolder(folderName); }"
      - "createApp() -> { app, services, adapters }"
    schemas:
      - "DATA-001 (database.json): { tracks: [{ id, title, bpm, genre, lyricsRaw, aiScore, aiReview, techCheck, audioPathAceStep, audioPathSuno, coverImageUrl, timeline, releaseKit, status, createdAt, updatedAt }] }"
      - "DATA-002 (config/.env): { PORT, NODE_ENV, ZENION_ROOT_DIR, ACE_WATCH_DIR, DATA_DIR, GEMINI_API_KEY, OPENAI_API_KEY, LLM_PROVIDER, ACE_API_URL }"
    error_contracts:
      - "400 Bad Request: Missing required parameters"
      - "404 Not Found: Track or Job not found"
      - "500 Internal Server Error: Handled by Express global error handler"
      - "Security Error: Path Traversal attempt detected"
  contract_skeleton:
    mode: new
    files:
      - package.json
      - Dockerfile
      - docker-compose.yml
      - .env.example
      - .gitignore
      - src/server.js
      - src/core/domain/Track.js
      - src/core/services/VaultStorageService.js
      - src/core/services/DirectorService.js
      - src/core/services/QualityJudgeService.js
      - src/core/services/VideoRenderService.js
      - src/core/services/ReleaseKitService.js
      - src/adapters/GeminiProvider.js
      - src/adapters/FFmpegVideoEncoder.js
      - src/adapters/ZenionVaultRepository.js
      - src/api/routes/director.routes.js
      - src/api/routes/tracks.routes.js
      - src/api/routes/video.routes.js
      - src/api/routes/release.routes.js
      - src/client/index.html
      - src/client/src/main.jsx
      - src/client/src/App.jsx
      - src/client/vite.config.js
      - tests/smoke.test.js
    smoke_commands:
      - "node tests/smoke.test.js"

development_standards_applied:
  - standard_id: DEV-DIR-001
    source: docs/product/PRODUCT_ARCHITECTURE.md
    rule: "헥사고날 아키텍처(Driving Adapters -> Core Services -> Driven Adapters) 원칙 준수"
  - standard_id: DEV-SEC-001
    source: docs/product/PRODUCT_CONTRACTS.md
    rule: "SEC-001(API 키 비공개 격리) 및 SEC-002(경로 트래버설 차단 검증) 필수 적용"
  - standard_id: DEV-ERR-001
    source: docs/core/TECH_STACK_BASELINES.md
    rule: "Express 글로벌 예외 핸들러 및 표준 JSON 응답 포맷 준수"

scope:
  writable:
    - package.json
    - Dockerfile
    - docker-compose.yml
    - .env.example
    - .gitignore
    - data/
    - src/
    - tests/
    - docs/runs/RUN-001_build-wave-BW-000_scaffold-docker-environment-setup_v0.1.md
  readonly:
    - docs/core/
    - docs/templates/
  excluded:
    - session.json
    - docs/ref-docs/

completion_criteria:
  - "루트 package.json에 명시된 Node 20 LTS 의존성 및 start/dev/test 스크립트가 구성된다."
  - "Dockerfile 및 docker-compose.yml에 Linux Debian 12 Bookworm, FFmpeg, Noto Sans CJK, 볼륨 마운트가 명시된다."
  - "헥사고날 디렉토리 구조 및 각 코어 도메인/서비스/어댑터/라우트 스켈레톤 코드가 작성된다."
  - "tests/smoke.test.js가 작성되고 self-check(node tests/smoke.test.js)가 100% 통과한다."

verification:
  owner: orchestrator-rerun
  commands:
    - "npm test"
    - "node tests/smoke.test.js"
```

---

## 2. Run Output Contract

```yaml
run_id: RUN-001
status: Completed
adapter: gemini
completed_at: "2026-08-27T23:14:00+09:00"
evidence:
  - id: EV-000-01
    type: test_log
    path: "tests/smoke.test.js"
    description: "7대 헥사고날 컴포넌트 및 보안 스모크 테스트 100% 통과 증적"
traceability_updates:
  - scenario_id: SCN-003
    status: InProgress
  - scenario_id: SCN-004
    status: InProgress

summary:
  ko: "BW-000 스캐폴드 및 Docker 실행 환경 구축을 완료하고 7대 헥사고날 코어/어댑터 스모크 테스트를 100% 통과시켰습니다."
  changed_behavior:
    - "Node 20 LTS 기반 Express 서버가 구동되고 /health, /api/health 및 4대 API 라우터가 정상 마운트됩니다."
    - "도메인 엔티티(Track)와 5대 코어 서비스 및 3대 어댑터가 헥사고날 의존성 주입 패턴으로 연결됩니다."
    - "경로 트래버설 공격 방어(SEC-002) 및 API 키 유출 방어(SEC-001) 검증이 완료되었습니다."
    - "Linux Debian 12 기반 FFmpeg + fonts-noto-cjk 탑재 Dockerfile 및 ZENION/ACE 볼륨 마운트 docker-compose.yml이 준비되었습니다."

changed_files:
  - file_path: package.json
    status: Created
  - file_path: Dockerfile
    status: Created
  - file_path: docker-compose.yml
    status: Created
  - file_path: .env.example
    status: Created
  - file_path: .gitignore
    status: Created
  - file_path: src/server.js
    status: Created
  - file_path: src/core/domain/Track.js
    status: Created
  - file_path: src/core/services/VaultStorageService.js
    status: Created
  - file_path: src/core/services/DirectorService.js
    status: Created
  - file_path: src/core/services/QualityJudgeService.js
    status: Created
  - file_path: src/core/services/VideoRenderService.js
    status: Created
  - file_path: src/core/services/ReleaseKitService.js
    status: Created
  - file_path: src/adapters/GeminiProvider.js
    status: Created
  - file_path: src/adapters/FFmpegVideoEncoder.js
    status: Created
  - file_path: src/adapters/ZenionVaultRepository.js
    status: Created
  - file_path: src/api/routes/director.routes.js
    status: Created
  - file_path: src/api/routes/tracks.routes.js
    status: Created
  - file_path: src/api/routes/video.routes.js
    status: Created
  - file_path: src/api/routes/release.routes.js
    status: Created
  - file_path: src/client/index.html
    status: Created
  - file_path: src/client/src/main.jsx
    status: Created
  - file_path: src/client/src/App.jsx
    status: Created
  - file_path: src/client/vite.config.js
    status: Created
  - file_path: tests/smoke.test.js
    status: Created
  - file_path: docs/runs/RUN-001_build-wave-BW-000_scaffold-docker-environment-setup_v0.1.md
    status: Created

related_ids:
  req: [REQ-001, REQ-002, REQ-003]
  ac: [AC-001-01, AC-001-02, AC-002-01, AC-002-02, AC-003-01, AC-003-02, AC-003-03, AC-N001-01, AC-N001-02, AC-N001-03]
  func: [FUNC-001, FUNC-002, FUNC-003, FUNC-004, FUNC-005]
  api: [API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008]
  db: [DATA-001, DATA-002]
  sec: [SEC-001, SEC-002]
  test: [REG-001, REG-002, REG-003, REG-004, REG-005, SEC-REG-001, SEC-REG-002]

verification_results:
  - command: "npm test"
    result: passed
    summary: "7/7 Tests Passed (Track Domain, Repository & Traversal Defense, Director, Quality Judge, Video & Release Kit, Security Secret Isolation, Express App Wiring)"
  - command: "node tests/smoke.test.js"
    result: passed
    summary: "Exit Code 0 - 100% Smoke Pass"

delegation_records:
  - mode: antigravity-subagent
    delegate: build-worker (Scaffold - Environment Builder)
    native_agent: true
    task: "BW-000 스캐폴드 및 Docker 실행 환경 구축"
    scope:
      writable:
        - package.json
        - Dockerfile
        - docker-compose.yml
        - .env.example
        - .gitignore
        - src/
        - tests/
        - docs/runs/RUN-001_build-wave-BW-000_scaffold-docker-environment-setup_v0.1.md
    started_at: "2026-08-27T23:08:31+09:00"
    completed_at: "2026-08-27T23:14:00+09:00"
    duration_seconds: 329
    heartbeat_count: 1
    status: worker_completed
    changed_files:
      - package.json
      - Dockerfile
      - docker-compose.yml
      - .env.example
      - .gitignore
      - src/server.js
      - src/core/domain/Track.js
      - src/core/services/VaultStorageService.js
      - src/core/services/DirectorService.js
      - src/core/services/QualityJudgeService.js
      - src/core/services/VideoRenderService.js
      - src/core/services/ReleaseKitService.js
      - src/adapters/GeminiProvider.js
      - src/adapters/FFmpegVideoEncoder.js
      - src/adapters/ZenionVaultRepository.js
      - src/api/routes/director.routes.js
      - src/api/routes/tracks.routes.js
      - src/api/routes/video.routes.js
      - src/api/routes/release.routes.js
      - src/client/index.html
      - src/client/src/main.jsx
      - src/client/src/App.jsx
      - src/client/vite.config.js
      - tests/smoke.test.js
      - docs/runs/RUN-001_build-wave-BW-000_scaffold-docker-environment-setup_v0.1.md
    result_summary: "Node 20 / Express 헥사고날 스캐폴드 및 Docker 배포 구성, 스모크 테스트 100% 통과"
    orchestrator_verification:
      - command: "npm test"
        result: passed

standard_compliance_report:
  - standard_id: DEV-DIR-001
    status: Pass
    details: "Driving Adapters(Express 라우터) -> Core Services -> Driven Adapters(Gemini, FFmpeg, Repository) 헥사고날 레이어 분리 및 의존성 주입 완성"
  - standard_id: DEV-SEC-001
    status: Pass
    details: "SEC-001 API Key .env 격리 및 .gitignore 등록 완료, SEC-002 ZenionVaultRepository 경로 트래버설 방어 로직 구현 및 단위 검증 통과"
  - standard_id: DEV-ERR-001
    status: Pass
    details: "Express 글로벌 예외 핸들러 및 JSON 에러 응답 포맷 일관성 확보"

open_issues: []

orchestrator_decision_needed:
  - item: "BW-001 (AI Director & Quality Screening Wave) 착수 승인"
    reason: "BW-000 스캐폴드 환경 및 스켈레톤 인터페이스가 안정적으로 검증되었으므로 후속 Build Wave로 전이 가능합니다."
```

---

## 3. Detailed Verification Results

### 3.1 Smoke Test Execution Log

```text
> lyrify@0.1.0 test
> node tests/smoke.test.js

🧪 [Smoke Test Suite] Starting ZENION Music Studio Scaffold Verification...

  ✅ PASS: Track Entity - Creation and Lifecycle Methods
  ✅ PASS: ZenionVaultRepository - Persistence & Path Traversal Prevention (SEC-002)
  ✅ PASS: DirectorService & GeminiProvider - Style Recipe Planning (SCN-001, API-001)
  ✅ PASS: QualityJudgeService - AI 1st Screening (SCN-002, API-003)
  ✅ PASS: VideoRenderService & ReleaseKitService - Video Export & SNS Kit (API-006, API-007)
  ✅ PASS: Security Checks - Secret Isolation (SEC-001) & .gitignore Rules
  ✅ PASS: Express Application - Server Initialization & Hexagonal Wiring

========================================
🎉 Smoke Tests Finished: 7/7 Passed (100%)
========================================
```

### 3.2 Key Architectural Highlights

1. **Docker 및 Media Engine 환경**:
   - `Dockerfile`에 Linux Debian 12 Bookworm(`node:20-bookworm-slim`), `ffmpeg`, `fonts-noto-cjk`, `libass-dev`, `fontconfig` 사전 설치.
   - `docker-compose.yml`을 통해 Host `C:\Users\julyi\Documents\ZENION-MUSIC` ↔ Container `/data/ZENION-MUSIC`, Host `C:\Users\julyi\Documents\ACE-Step-1.5` ↔ Container `/data/ACE-Step-1.5` 볼륨 마운트 바인딩.
2. **Hexagonal Architecture 기반 모듈화**:
   - 도메인 엔티티: `Track`
   - 코어 서비스: `DirectorService`, `QualityJudgeService`, `VaultStorageService`, `VideoRenderService`, `ReleaseKitService`
   - 외부 어댑터: `GeminiProvider`, `FFmpegVideoEncoder`, `ZenionVaultRepository`
   - REST 라우터: `director.routes.js`, `tracks.routes.js`, `video.routes.js`, `release.routes.js`
3. **보안 기준 준수**:
   - `SEC-001`: Google Gemini API Key `.env` 분리 및 `.gitignore` 등록.
   - `SEC-002`: `ZenionVaultRepository.isSafePath()`를 통해 상대 경로 이탈 (`../../etc/passwd` 등) 원천 차단.
