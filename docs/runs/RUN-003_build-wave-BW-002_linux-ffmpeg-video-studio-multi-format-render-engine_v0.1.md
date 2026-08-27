# Run 003: Build Wave BW-002 Linux FFmpeg Video Studio & Multi-Format Render Engine

---
document_id: RUN-003
title: Build Wave BW-002 Linux FFmpeg Video Studio & Multi-Format Render Engine
title_ko: BW-002 Linux FFmpeg 비디오 스튜디오 및 멀티 포맷(16:9/9:16) 렌더링 엔진 구축
project: lyrify
profile: product
gate_scope: impl
status: Verified
version: v0.1
owner_role: Build Worker
author: Build Worker (Video Studio Builder)
reviewer: Orchestrator
approver: User
created_at: 2026-08-27
updated_at: 2026-08-27
related_documents:
  - docs/product/PRODUCT_BRIEF.md
  - docs/product/PRODUCT_CONTRACTS.md
  - docs/product/PRODUCT_ARCHITECTURE.md
  - docs/product/PRODUCT_TRACEABILITY.md
  - docs/runs/RUN-001_build-wave-BW-000_scaffold-docker-environment-setup_v0.1.md
  - docs/runs/RUN-002_build-wave-BW-001_zenion-storage-master-vault-engine_v0.1.md
---

## 1. Run Input Contract

```yaml
run_id: RUN-003
bw_id: BW-002
persona: build
skill: build-wave
run_type: BuildWave
gate: impl
goal: "Linux FFmpeg 기반 16:9 유튜브 롱폼(1920x1080) 및 9:16 인스타/틱톡 숏폼(1080x1920) 렌더링 파이프라인 완성, 한글 폰트(/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc) 자막 오버레이, 오디오 파형/duration 추출, 커버 비주얼(03_visuals/cover.png) 생성, 가사 타임라인 싱크(API-008), 04_videos/ 패키징 저장 및 mock/dry-run 모듈화 구현"

related_ids:
  req: [REQ-003]
  ac: [AC-003-01, AC-003-02, AC-003-03]
  func: [FUNC-003, FUNC-004]
  api: [API-003, API-005, API-006, API-008, GAP-001]
  db: [DATA-001, DATA-002]
  sec: [SEC-001, SEC-002]
  test: [REG-004, SEC-REG-002]

target_contracts:
  func: [FUNC-003, FUNC-004]
  api: [API-003, API-005, API-006, API-008, GAP-001]
  db: [DATA-001]
  test: [REG-004]
  interface_contract:
    language: "javascript (ES Modules, Node.js 20 LTS)"
    signatures:
      - "FFmpegVideoEncoder.prototype.getSystemFontPath() -> string"
      - "FFmpegVideoEncoder.prototype.buildRenderOptions(params) -> Object"
      - "FFmpegVideoEncoder.prototype.analyzeAudioTech(audioPath) -> Promise<{ clipping, silence, duration }>"
      - "FFmpegVideoEncoder.prototype.extractWaveform(audioPath, options) -> Promise<{ duration, samples }>"
      - "FFmpegVideoEncoder.prototype.renderVideo(params) -> Promise<{ jobId, outputPath, format, resolution, dryRun? }>"
      - "FFmpegVideoEncoder.prototype.getJobStatus(jobId) -> Object|null"
      - "VideoRenderService.prototype.generateCoverVisual(trackId, options) -> Promise<{ success, trackId, imageUrl, coverPath, prompt }>"
      - "VideoRenderService.prototype.saveLyricTimelineSync(trackId, timeline) -> Promise<{ success, trackId, updatedTimeline }>"
      - "VideoRenderService.prototype.renderTrackVideo(trackId, options) -> Promise<{ success, jobId, trackId, format, videoUrls }>"
      - "createVideoRouter({ renderService }) -> express.Router"
    schemas:
      - "Video Output: { youtube_16x9: 1920x1080 mp4 in 04_videos/, shorts_9x16: 1080x1920 mp4 in 04_videos/ }"
      - "Cover Visual: 03_visuals/cover.png (1080x1080 valid gradient PNG + cover.svg)"
      - "Timeline Sync: [{ part: string, startSecond: number }]"
    error_contracts:
      - "400 Bad Request: Invalid timeline sync payload (not an array)"
      - "404 Not Found: Track not found for image generation, video export, or timeline sync"
      - "404 Not Found: Job ID not found for status polling"

development_standards_applied:
  - standard_id: DEV-DIR-001
    source: docs/product/PRODUCT_ARCHITECTURE.md
    rule: "헥사고날 아키텍처 준수 (Driving REST API -> Core VideoRenderService -> Driven FFmpegVideoEncoder & VaultStorageService)"
  - standard_id: DEV-MEDIA-001
    source: docs/product/PRODUCT_CONTRACTS.md
    rule: "16:9 유튜브 롱폼(1920x1080) 및 9:16 숏폼(1080x1920) H.264/AAC 표준 인코딩 및 한글 폰트 자막 렌더링"
  - standard_id: DEV-TEST-001
    source: docs/core/DEVELOPMENT_STANDARD_RULES.md
    rule: "외부 바이너리(FFmpeg) 의존 없는 dry-run / mock 격리 테스트 지원"

scope:
  writable:
    - src/adapters/FFmpegVideoEncoder.js
    - src/core/services/VideoRenderService.js
    - src/api/routes/video.routes.js
    - tests/video.test.js
    - package.json
    - docs/runs/RUN-003_build-wave-BW-002_linux-ffmpeg-video-studio-multi-format-render-engine_v0.1.md
  readonly:
    - docs/core/
    - docs/templates/
  excluded:
    - session.json

completion_criteria:
  - "16:9(1920x1080) 및 9:16(1080x1920) 멀티 포맷 비디오 렌더링 파이프라인이 완성되고 04_videos/에 저장된다."
  - "한글 폰트(Noto Sans CJK / Nanum Gothic / 시스템 폰트)가 자동 탐색되고 타임라인 자막이 오버레이된다."
  - "오디오 분석 및 duration/waveform 추출 기능이 정상 동작한다."
  - "03_visuals/cover.png에 유효한 커버 이미지가 생성 및 저장된다."
  - "가사 타임라인 싱크 API (API-008) 및 메타데이터 동기화가 동작한다."
  - "외부 FFmpeg 바이너리 유무에 상관없이 통과하는 mock/dry-run 모드가 완비된다."
  - "tests/video.test.js, tests/vault.test.js, tests/smoke.test.js 전체(21/21) 100% 통과한다."

verification:
  owner: orchestrator-rerun
  commands:
    - "npm test"
    - "node tests/video.test.js"
    - "node tests/vault.test.js"
    - "node tests/smoke.test.js"
status: Completed
```

---

## 2. Run Output Contract

```yaml
run_id: RUN-003
bw_id: BW-002
status: Completed
adapter: gemini
completed_at: "2026-08-27T23:36:35+09:00"
evidence:
  - id: EV-002-01
    type: test_log
    path: "tests/video.test.js"
    description: "Linux FFmpeg Video Studio & Multi-Format Render Engine 단위/통합 테스트 7/7 (100%) 통과"
  - id: EV-002-02
    type: test_log
    path: "tests/vault.test.js"
    description: "ZENION Master Vault Storage Engine 테스트 7/7 (100%) 통과"
  - id: EV-002-03
    type: test_log
    path: "tests/smoke.test.js"
    description: "헥사고날 아키텍처 스모크 테스트 7/7 (100%) 통과"

traceability_updates:
  - scenario_id: SCN-004
    status: Completed
  - scenario_id: SCN-005
    status: InProgress

summary:
  ko: "Linux FFmpeg 기반 멀티 포맷(16:9 유튜브 1920x1080, 9:16 숏폼 1080x1920) 비디오 렌더링 파이프라인 및 한글 자막 오버레이, 커버 비주얼 생성(03_visuals/cover.png), 가사 타임라인 싱크(API-008), 오디오 분석 및 파형 추출, mock/dry-run 모듈화 및 REST API 라우터를 완결하고 100% 테스트 검증을 완료했습니다."
  changed_behavior:
    - "FFmpegVideoEncoder에 16:9(1920x1080) 및 9:16(1080x1920) 파라미터 빌더(buildRenderOptions), 한글 폰트(Noto Sans CJK / Nanum Gothic) 자동 탐색 및 타임라인 자막 drawtext 필터 생성이 구현되었습니다."
    - "FFmpegVideoEncoder에 오디오 기술 결함 분석(analyzeAudioTech), duration 프로빙, 파형 데이터 추출(extractWaveform), mock/dry-run 모드가 완비되었습니다."
    - "VideoRenderService.generateCoverVisual()을 통해 트랙 장르 감성에 맞춘 1080x1080 PNG(03_visuals/cover.png) 및 SVG(03_visuals/cover.svg) 커버 이미지가 자동 생성 및 저장됩니다."
    - "VideoRenderService.renderTrackVideo()를 통해 16:9 및 9:16 포맷 비디오가 04_videos/ 디렉토리에 렌더링되고 트랙 상태가 'released'로 갱신됩니다."
    - "VideoRenderService.saveLyricTimelineSync()를 통해 가사 타임스탬프 싱크가 database.json, recipe.json, metadata.json, release_kit.md에 동기화됩니다."
    - "src/api/routes/video.routes.js에 POST /:id/generate-image, POST /:id/export-video, POST /:id/sync, GET /status/:jobId 엔드포인트가 연동되었습니다."

changed_files:
  - file_path: src/adapters/FFmpegVideoEncoder.js
    status: Modified
  - file_path: src/core/services/VideoRenderService.js
    status: Modified
  - file_path: src/api/routes/video.routes.js
    status: Modified
  - file_path: package.json
    status: Modified
  - file_path: tests/video.test.js
    status: Created
  - file_path: docs/runs/RUN-003_build-wave-BW-002_linux-ffmpeg-video-studio-multi-format-render-engine_v0.1.md
    status: Created

related_ids:
  req: [REQ-003]
  ac: [AC-003-01, AC-003-02, AC-003-03]
  func: [FUNC-003, FUNC-004]
  api: [API-003, API-005, API-006, API-008, GAP-001]
  db: [DATA-001, DATA-002]
  sec: [SEC-001, SEC-002]
  test: [REG-004, SEC-REG-002]

verification_results:
  - command: "npm test"
    result: passed
    summary: "21/21 Tests Passed (7 Smoke + 7 Master Vault + 7 Video Studio)"
  - command: "node tests/video.test.js"
    result: passed
    summary: "7/7 Video Studio Tests Passed (Multi-format Pipeline, Korean Subtitles, Waveform, Cover Visuals, Timeline Sync, Video Export, API Routing)"
  - command: "node tests/vault.test.js"
    result: passed
    summary: "7/7 Master Vault Tests Passed"
  - command: "node tests/smoke.test.js"
    result: passed
    summary: "7/7 Smoke Tests Passed"

delegation_records:
  - mode: antigravity-subagent
    delegate: build-worker (Video Studio Builder)
    native_agent: true
    task: "BW-002 Linux FFmpeg Video Studio & Multi-Format Render Engine 구현 및 테스트"
    scope:
      writable:
        - src/adapters/FFmpegVideoEncoder.js
        - src/core/services/VideoRenderService.js
        - src/api/routes/video.routes.js
        - package.json
        - tests/video.test.js
        - docs/runs/RUN-003_build-wave-BW-002_linux-ffmpeg-video-studio-multi-format-render-engine_v0.1.md
    started_at: "2026-08-27T23:27:30+09:00"
    completed_at: "2026-08-27T23:36:35+09:00"
    duration_seconds: 545
    heartbeat_count: 0
    status: worker_completed
    result_summary: "Linux FFmpeg 16:9/9:16 비디오 렌더링, 한글 폰트 자막, 커버 비주얼 생성, 가사 싱크, REST API 라우터 완결 및 21/21 테스트 100% 통과"
    orchestrator_verification:
      - command: "npm test"
        result: passed

standard_compliance_report:
  - standard_id: DEV-DIR-001
    status: Pass
    details: "헥사고날 아키텍처에 따라 비디오 렌더링 코어 서비스, FFmpeg 외부 연동 어댑터, Express REST API 라우터를 완전히 분리"
  - standard_id: DEV-MEDIA-001
    status: Pass
    details: "H.264/AAC 코덱, 16:9(1920x1080) 및 9:16(1080x1920) 해상도, 30fps, 레터박스 패딩, Noto Sans CJK 한글 폰트 자막 오버레이 구현"
  - standard_id: DEV-TEST-001
    status: Pass
    details: "FFmpeg 바이너리가 없거나 테스트 환경에서도 동작하는 dry-run/mock 모드를 구축하여 일관된 CI/CD 테스트 검증 보장"

open_issues: []

orchestrator_decision_needed:
  - item: "Build Wave BW-003 (SNS Release Hub & Quality Judge Suite) 전이 승인"
    reason: "비디오 렌더링 및 자산 패키징이 완결되었으므로 SNS 릴리즈 허브 및 최종 통합 릴리즈 단계로 전이 가능합니다."
```

---

## 3. Detailed Verification Results

### 3.1 Test Suite Execution Log

```text
> lyrify@0.1.0 test
> node tests/smoke.test.js && node tests/vault.test.js && node tests/video.test.js

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

🧪 [Vault Storage Test Suite] Starting ZENION Master Vault Engine Verification...

  ✅ PASS: REQ-002: Complete Package Folder Generation (recipe.json, 01_draft/, 02_final_audio/, 03_visuals/, 04_videos/)
  ✅ PASS: API-004: Suno Audio Mapping & 02_final_audio/ Organization
  ✅ PASS: API-007: SNS Release Kit Markdown Auto-Export to release_kit.md
  ✅ PASS: REQ-002: syncVault Scanner - Auto Discovery & database.json Sync
  ✅ PASS: SEC-002: Path Traversal Attack Defense & Boundary Protection
  ✅ PASS: DATA-001: Atomic Persistence & Async Concurrency Mutex Defense
  ✅ PASS: API Integration: GET /api/tracks, POST /map-suno, POST /scan

========================================
🎉 Vault Storage Engine Tests: 7/7 Passed (100%)
========================================

🧪 [Video Studio Test Suite] Starting Multi-Format Render Engine Verification (REG-004)...

  ✅ PASS: REQ-003: 16:9 YouTube Longform & 9:16 Shorts Rendering Parameter Pipeline Builder
  ✅ PASS: SCN-004: Korean Font Subtitle Detection & Path Normalization
  ✅ PASS: API-003: Audio Duration Probing & Normalized Waveform Extraction
  ✅ PASS: API-005: Cover Visual PNG & SVG Generation in 03_visuals/cover.png
  ✅ PASS: API-008: Save Lyric Timeline Sync & Master Vault Synchronization
  ✅ PASS: API-006: Multi-Format (16:9 & 9:16) Video Export into 04_videos/
  ✅ PASS: API Routing Integration: POST /generate-image, /export-video, /sync, GET /status

========================================
🎉 Video Studio Tests Finished: 7/7 Passed (100%)
========================================
```

### 3.2 Key Technical Achievements

1. **멀티 포맷 비디오 렌더링 파이프라인 (SCN-004, REQ-003, API-006)**:
   - 유튜브 롱폼(16:9, 1920x1080) 및 인스타그램/틱톡 숏폼(9:16, 1080x1920) 해상도에 맞춘 H.264/AAC 인코딩 파이프라인 구축.
   - 원본 비율 유지 및 레터박스(pad) 비디오 필터 적용.
   - `04_videos/<trackId>_youtube_16x9.mp4` 및 `04_videos/<trackId>_shorts_9x16.mp4`로 자동 저장 및 패키징.
2. **한글 폰트 자막 오버레이 및 시스템 폰트 자동 감지**:
   - `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` 및 `NanumGothic`, Windows 맑은 고딕 등 환경별 한글 폰트를 자동 탐지.
   - 타임라인 타임스탬프에 따른 FFmpeg `drawtext` 필터 동적 생성 (`between(t, start, end)`).
3. **오디오 분석 및 파형 추출 (API-003)**:
   - `analyzeAudioTech`를 통한 오디오 duration 프로빙 및 무음/클리핑 결함 판별.
   - `extractWaveform`을 통한 시각화용 정규화(0.1~1.0) 파형 샘플 데이터 추출.
4. **커버 비주얼 생성 (API-005, 03_visuals/cover.png)**:
   - 트랙 장르(City Pop, Ballad, Indie, Rock 등)에 최적화된 그라데이션 컬러 팔레트를 적용한 1080x1080 PNG 및 SVG 타이포그래피 커버 자동 합성.
   - `03_visuals/cover.png` 및 `03_visuals/cover.svg`로 마스터 볼트에 저장.
5. **가사 타임라인 싱크 API (API-008)**:
   - 가사 타임스탬프 동기화 데이터를 저장하고 `recipe.json`, `metadata.json`, `release_kit.md`에 실시간 반영.
6. **완벽한 Mock / Dry-Run 모듈화**:
   - 외부 FFmpeg 바이너리가 없거나 테스트 환경에서도 비디오 placeholder를 생성하고 진행률(0 -> 50 -> 100%)을 시뮬레이션하여 CI/CD에서 무결한 테스트 통과 보장.
