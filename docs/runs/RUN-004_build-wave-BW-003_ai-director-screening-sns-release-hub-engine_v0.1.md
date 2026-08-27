# RUN-004 Build Wave BW-003 - AI Director Screening & SNS Release Hub Engine

```yaml
run_id: RUN-004
gate: impl
persona: build
adapter: codex-gpt
skill: build-wave
skill_path: .agents/skills/vulcan-impl-wave/SKILL.md
profile: product
bw_id: BW-003
run_type: Implementation
status: Completed
created_at: 2026-08-27
related_ids: [SCN-001, SCN-005, REQ-001, REQ-003, SCN-002, SCN-004, API-007, UI-002, UI-004, API-004, API-006, REG-001, API-001, DATA-001, REG-002, EV-001, REG-005, EV-005, API-002, API-003, SCN-003, API-005, API-008, DATA-002, UI-001, UI-003, EV-002, REQ-002, REG-003, EV-003, REG-004, EV-004]
trace_context:
  seeds: [SCN-001, SCN-005]
  depth: 2
  direction: "both"
  source: "trace-context"
target_contracts:
  scenario: [SCN-001, SCN-005, SCN-002, SCN-004, SCN-003]
  req: [REQ-001, REQ-003, REQ-002]
  api: [API-007, API-004, API-006, API-001, API-002, API-003, API-005, API-008]
  data: [DATA-001, DATA-002]
  ui: [UI-002, UI-004, UI-001, UI-003]
  regression: [REG-001, REG-002, REG-005, REG-003, REG-004]
  test: []
  other: [EV-001, EV-005, EV-002, EV-003, EV-004]
  interface_contract:
    language: "Product profile stack/runtime is defined in PRODUCT_ARCHITECTURE and PRODUCT_CONTRACTS."
    signatures:
      - "GeminiProvider.prototype.generateStyleRecipes({ keyword, count, mode, provider }) -> Promise<Array<Object>>"
      - "GeminiProvider.prototype.evaluateQuality({ lyrics, audioMetadata }) -> Promise<{ aiScore, aiReview, grade, techCheck }>"
      - "DirectorService.prototype.generateStyles({ keyword, count, mode, provider }) -> Promise<{ success, keyword, count, mode, provider, styles }>"
      - "DirectorService.prototype.triggerAceDraft(recipeId, recipeData) -> Promise<{ success, jobId, recipeId, status, message }>"
      - "QualityJudgeService.prototype.evaluateTrack(trackId, { audioPath, lyrics }) -> Promise<{ success, trackId, aiScore, aiReview, grade, techCheck }>"
      - "QualityJudgeService.prototype.rankTracks(tracks) -> Array<Track|Object>"
      - "QualityJudgeService.prototype.getTopRecommendations(tracks, topN) -> Array<Track|Object>"
      - "ReleaseKitService.prototype.generateReleaseKit(trackId, options) -> Object"
      - "ReleaseKitService.prototype.getReleaseKit(trackId) -> Object|null"
      - "ReleaseKitService.prototype.formatReleaseKitMarkdown(track, kit) -> string"
    schemas:
      - "POST /api/director/generate-styles (API-001): Request { keyword, count, mode, provider } -> Response { success, keyword, count, mode, provider, styles: [{ id, title, genre, bpm, instruments, lyricTheme, lyrics: { verse1, chorus, verse2 }, promptText, mode, concept }] }"
      - "POST /api/tracks/:id/evaluate (API-003): Request { audioPath, lyrics } -> Response { success, trackId, aiScore, aiReview, grade, techCheck: { clipping, silence } }"
      - "GET /api/tracks/:id/release-kit (API-007): Response { success, releaseKit: { youtube: { title, description, tags, timestampLyrics }, instagram: { caption, hashtags }, tiktok: { caption, hashtags } } }"
    error_contracts:
      - "400 Bad Request: Keyword is required for style generation"
      - "400 Bad Request: Recipe ID is required for ACE draft trigger"
      - "404 Not Found: Track not found for evaluation or release kit query"
runner_role: worker-runner
source_documents:
  read_first:
    - "AGENTS.md"
    - "session.json"
    - "docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    - ".agents/skills/vulcan-impl-wave/SKILL.md"
  working_documents:
    - "docs/product/PRODUCT_BRIEF.md"
    - "docs/product/PRODUCT_ARCHITECTURE.md"
    - "docs/product/PRODUCT_CONTRACTS.md"
    - "docs/product/PRODUCT_TRACEABILITY.md"
    - "docs/product/REGRESSION_AND_RELEASE_REPORT.md"
  reference_on_demand:
    - "docs/core/DELIVERY_PROFILES.md"
    - "docs/core/TECH_STACK_BASELINES.md"
orchestrator_reference:
  - "docs/core/AGENT_RUN_PROTOCOL.md"
  - "docs/core/RUN_INPUT_CONTRACT.md"
  - "docs/core/RUN_OUTPUT_CONTRACT.md"
scope:
  writable:
    - "docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    - "src/adapters/GeminiProvider.js"
    - "src/core/services/DirectorService.js"
    - "src/core/services/QualityJudgeService.js"
    - "src/core/services/ReleaseKitService.js"
    - "src/api/routes/director.routes.js"
    - "src/api/routes/release.routes.js"
    - "src/api/routes/tracks.routes.js"
    - "tests/director.test.js"
    - "package.json"
    - "docs/product/PRODUCT_TRACEABILITY.md"
  readonly:
    - "docs/core/"
    - "docs/templates/"
    - "docs/product/PRODUCT_BRIEF.md"
    - "docs/product/PRODUCT_ARCHITECTURE.md"
    - "docs/product/PRODUCT_CONTRACTS.md"
    - "docs/product/REGRESSION_AND_RELEASE_REPORT.md"
  excluded:
    - "docs/ref-docs/"
    - "**/*.db"
    - "**/__pycache__/"
    - "**/.ruff_cache/"
    - "**/node_modules/"
    - "**/.next/"
worker_execution_policy:
  forbidden_actions:
    - "Gate 전환을 수행하지 않는다."
    - "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다."
    - "사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다."
    - "scope.writable 밖 파일을 수정하지 않는다."
  required_outputs:
    - "수행한 변경과 검증 결과를 Run 결과에 남긴다."
    - "wave-complete, Gate 전환, session 변경, 최종 승인 판단이 필요하면 Orchestrator 결정 필요 항목으로 반환한다."
  completion_rules:
    - "이 Run의 target_contracts.scenario만 완결한다."
    - "빌드 또는 담당 테스트가 깨진 상태를 완료로 보고하지 않는다."
dependency_install_policy:
  worker_cache_required: true
  npm_cache_env: "npm_config_cache"
  playwright_cache_env: "PLAYWRIGHT_BROWSERS_PATH"
  if_install_blocked: "dependency install이 권한, 인증, 네트워크, registry, cache 문제로 막히면 코드 실패로 단정하지 않고 environment_blocked 또는 not_run으로 보고한다."
development_standards_applied:
  - standard_id: "PRODUCT-LOG-001"
    source: "docs/product/PRODUCT_CONTRACTS.md"
    rule: "사용자 입력, 내부 오류, 저장소 경로, stack trace를 화면이나 공개 응답에 노출하지 않는다."
  - standard_id: "PRODUCT-TEST-001"
    source: "docs/product/REGRESSION_AND_RELEASE_REPORT.md"
    rule: "테스트는 어떤 시나리오와 기대 결과를 검증하는지 사람이 읽을 수 있게 남긴다."
development_standard_checklist:
  logging:
    required: true
    targets:
      - "API handler"
      - "Service or state handler"
    rule: "표준 logger 또는 최소 오류 처리 흐름을 사용하고 민감정보를 로그/화면에 남기지 않는다."
  comments:
    required: true
    targets:
      - "public API handler"
      - "core state mutation function"
    rule: "핵심 책임과 관련 scenario/API/DATA ID를 짧은 주석 또는 docstring으로 남긴다."
  tests:
    required: true
    targets:
      - "scenario smoke"
      - "unit or integration test"
    rule: "테스트 이름이나 설명에 입력값, 기대값, 관련 SCN/REG ID를 남긴다."
verification:
  commands:
    - "npm test"
    - "node tests/director.test.js"
    - "python vulcan.py run-check docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    - "python vulcan.py run-preflight docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
  evidence:
    required: true
    target_documents:
      - "docs/product/PRODUCT_TRACEABILITY.md"
      - "docs/product/evidence/"
verification_results:
  - command: "npm test"
    result: passed
    summary: "29/29 Tests Passed (7 Smoke + 7 Master Vault + 7 Video Studio + 8 AI Director & Screening)"
  - command: "node tests/director.test.js"
    result: passed
    summary: "8/8 AI Director & Screening & SNS Release Hub Tests Passed (REG-001, REG-002, REG-005, SEC-REG-001, API-001, API-003, API-007)"
  - command: "python vulcan.py run-check docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    result: passed
    summary: "Run 검증 통과"
  - command: "python vulcan.py run-preflight docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    result: passed
    summary: "Run preflight 통과"
evidence:
  - id: EV-001
    type: test_log
    path: "tests/director.test.js"
    description: "AI Music Director 가변 스타일(1~20곡) 및 3대 모드(explore, single, album) 검증 (REG-001)"
  - id: EV-002
    type: test_log
    path: "tests/director.test.js"
    description: "AI 1차 퀄리티 스크리닝(100점 채점) 및 TOP 3 랭킹 추천 검증 (REG-002)"
  - id: EV-005
    type: test_log
    path: "tests/director.test.js"
    description: "SNS 멀티 플랫폼(YouTube, Instagram, TikTok) 릴리즈 키트 생성 검증 (REG-005)"
delegation_records:
  - mode: antigravity-subagent
    delegate: build-worker (AI Director & Release Hub Builder)
    native_agent: true
    task: "BW-003 AI Director Screening & SNS Release Hub Engine 구현 및 테스트"
    scope:
      writable:
        - "src/adapters/GeminiProvider.js"
        - "src/core/services/DirectorService.js"
        - "src/core/services/QualityJudgeService.js"
        - "src/core/services/ReleaseKitService.js"
        - "src/api/routes/director.routes.js"
        - "src/api/routes/release.routes.js"
        - "src/api/routes/tracks.routes.js"
        - "tests/director.test.js"
        - "package.json"
        - "docs/product/PRODUCT_TRACEABILITY.md"
        - "docs/runs/RUN-004_build-wave-BW-003_ai-director-screening-sns-release-hub-engine_v0.1.md"
    started_at: "2026-08-27T23:38:40+09:00"
    completed_at: "2026-08-27T23:42:30+09:00"
    duration_seconds: 230
    heartbeat_count: 0
    status: worker_completed
    result_summary: "AI 디렉터 가변 곡 수/3대 모드 기획, AI 1차 퀄리티 스크리닝(100점 채점/TOP 3 랭킹), SNS 릴리즈 키트 허브 구현 및 29/29 테스트 100% 통과"
    orchestrator_verification:
      - command: "npm test"
        result: passed
traceability_updates:
  - scenario_id: SCN-001
    status: Implemented
  - scenario_id: SCN-002
    status: Implemented
  - scenario_id: SCN-003
    status: Implemented
  - scenario_id: SCN-004
    status: Implemented
  - scenario_id: SCN-005
    status: Implemented
findings: []
change_requests: []
open_issues: []
```

## 1. Wave 목표

AI Director Screening & SNS Release Hub Engine 구축 (SCN-001, SCN-002, SCN-005)

## 2. Product 구현 범위

- 기준 시나리오: [SCN-001, SCN-005, SCN-002, SCN-004, SCN-003]
- 관련 요구/계약: [SCN-001, SCN-005, REQ-001, REQ-003, SCN-002, SCN-004, API-007, UI-002, UI-004, API-004, API-006, REG-001, API-001, DATA-001, REG-002, EV-001, REG-005, EV-005, API-002, API-003, SCN-003, API-005, API-008, DATA-002, UI-001, UI-003, EV-002, REQ-002, REG-003, EV-003, REG-004, EV-004]
- Product profile은 audit 산출물 대신 `docs/product/` 문서 세트를 기준으로 구현한다.

## 3. 작업자 입력 계약

- 먼저 `source_documents.read_first`를 읽고 `BW-003` 범위와 관련 ID를 확인한다.
- `source_documents.working_documents`의 Product Brief, Architecture, Contracts, Traceability, Regression 문서를 구현 기준으로 삼는다.
- `target_contracts.scenario`, `api`, `data`, `ui`, `regression`에 없는 기능은 추가하지 않는다.
- `target_contracts.interface_contract`는 세부 class 설계가 아니라 Product 계약 경계다. public API/data/UI shape가 충돌하면 임의 변경하지 말고 `open_issues`로 보고한다.
- `scope.writable` 안에서만 코드, 테스트, 자기 Run, Product Trace/evidence를 수정한다.
- 전체 QA Pass, 릴리즈 가능 여부, Gate 전환은 Orchestrator가 판단한다.

## 4. Orchestrator 지시

- 실제 구현은 native worker(subagent/thread/native branch agent)가 수행한다.
- Orchestrator는 worker 결과의 diff/scope를 확인하고, 관련 테스트를 재실행한 뒤 `wave-complete BW-003` 여부를 판단한다.
- `agent-run`/`run-exec`는 외부 CLI 실행 증적이나 worktree/watchdog이 필요할 때만 선택한다.

## 5. 검증 계획

- worker는 가능한 self-check만 실행하고, 실패/미실행 명령은 이유를 남긴다.
- Orchestrator는 worker가 작성한 테스트와 가능한 build/smoke를 재실행한다.
- Gate 4의 공식 UI/E2E 증적과 릴리즈 판정은 이 Run 완료 조건이 아니다.

## 6. 결과 기록

### 6.1 변경 파일

1. `src/adapters/GeminiProvider.js`:
   - `@google/genai` SDK Structured Outputs(`responseSchema`) 기반 가변 곡 수(1~20곡) 및 3대 모드(`explore`, `single`, `album`) 스타일/가사 레시피 생성 파이프라인 구현
   - API 키 부재 또는 오프라인 환경에서도 20개 장르 및 세부 편곡/컨셉 앨범 서사를 제공하는 고품질 오프라인 레시피 제너레이터 구현
   - 오디오 기술 결함(피크 클리핑 -20점, 무음 -20점) 및 가사 완결도([Verse 1]/[Chorus] 구조, 글자수 균형) 100점 만점 AI 품질 채점 알고리즘 구현
2. `src/core/services/DirectorService.js`:
   - 가변 곡 수(1~20곡), 3대 기획 모드(`explore`, `single`, `album`), 멀티 LLM Provider 입력 유효성 검사 및 스타일 레시피 생성 서비스 완성
   - ACE-Step 1.5 로컬 생성 트리거 (`triggerAceDraft`) 및 기획 모드 메타데이터 제공 (`getAvailableModes`)
3. `src/core/services/QualityJudgeService.js`:
   - 오디오 파형 결함 분석(FFmpeg probe)과 가사 완성도를 종합한 100점 만점 1차 AI 품질 심사(`evaluateTrack`) 완성
   - AI 심사 점수 기반 랭킹 정렬 및 TOP 3 추천 배지 부여(`rankTracks`, `getTopRecommendations`)
4. `src/core/services/ReleaseKitService.js`:
   - YouTube 롱폼(제목, 설명문, 태그, 타임스탬프 가사), Instagram Reels(캡션, 추천 해시태그), TikTok 숏폼(챌린지 캡션, 해시태그) 플랫폼별 최적화 릴리즈 키트 생성
   - 가사 타임라인 기반 `[M:SS]` 포맷 타임스탬프 가사 변환 및 마크다운 내보내기 연동
5. `src/api/routes/director.routes.js`:
   - `POST /api/director/generate-styles` (API-001)
   - `POST /api/director/trigger-ace`
   - `GET /api/director/modes`
6. `src/api/routes/release.routes.js`:
   - `GET /api/tracks/:id/release-kit` (API-007)
   - `POST /api/tracks/:id/release-kit`
7. `src/api/routes/tracks.routes.js`:
   - `POST /api/tracks/:id/evaluate` (API-003)
   - `GET /api/tracks` (API-002, AI 랭킹 정렬 연동)
8. `tests/director.test.js`:
   - REG-001 (가변 곡 수 1~20곡 & 3대 모드 explore/single/album 검증)
   - REG-002 (100점 만점 AI 채점, 클리핑/무음 페널티, TOP 3 랭킹 추천 검증)
   - REG-005 (YouTube, Instagram, TikTok 릴리즈 키트 포맷팅 및 타임스탬프 검증)
   - SEC-REG-001 (Google API Key 비공개 격리 및 안전한 오프라인 폴백 검증)
   - REST API 엔드포인트 통합 검증 (8/8 테스트 통과)
9. `package.json`:
   - `npm test` 스크립트에 `tests/director.test.js` 통합 (`test:director` 추가)
10. `docs/product/PRODUCT_TRACEABILITY.md`:
   - SCN-001 ~ SCN-005 상태를 `Implemented`로 최신화

### 6.2 검증 결과

```text
> lyrify@0.1.0 test
> node tests/smoke.test.js && node tests/vault.test.js && node tests/video.test.js && node tests/director.test.js

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

🧪 [AI Director & Screening & Release Hub Test Suite] Starting Verification...
  ✅ PASS: REG-001: AI Director Variable Track Count Support (1 ~ 20 songs)
  ✅ PASS: REG-001: AI Director 3 Planning Modes (Explore, Single, Album)
  ✅ PASS: REG-001: Director Input Validation & ACE Trigger Metadata
  ✅ PASS: REG-002: AI Quality Screening (100-point algorithm, audio defect checks, lyrics completeness)
  ✅ PASS: REG-002: Track AI Evaluation Persistence & TOP 3 Recommendation Ranking
  ✅ PASS: REG-005: SNS Release Kit Generation (YouTube, Instagram, TikTok) & Timestamps
  ✅ PASS: SEC-REG-001: Google API Key Isolation & Safe Offline Fallback
  ✅ PASS: REST API Integration: POST /generate-styles, POST /evaluate, GET /release-kit
========================================
🎉 AI Director & Screening Tests: 8/8 Passed (100%)
========================================
```

- 전체 단위/통합 테스트: **29/29 (100% 통과)**
- CLI 런체크: `python vulcan.py run-check` 통과
- CLI 사전검증: `python vulcan.py run-preflight` 통과

### 6.3 위임 기록

- **위임 대상**: Build Worker (`AI Director & Release Hub Builder`)
- **수행 작업**: BW-003 AI 디렉터 가변 기획/3대 모드, AI 1차 퀄리티 심사 100점 채점/TOP 3 랭킹, SNS 릴리즈 키트 허브 구현 및 `tests/director.test.js` 100% 검증
- **결과**: `worker_completed`

### 6.4 후속 조치

- **Orchestrator 결정 필요 항목**:
  1. Build Wave BW-003 완료 및 Gate 3 (Implementation Gate) 검증 완료 승인
  2. Gate 4 (QA / Verification Gate) 전이 검토 및 공식 E2E / 통합 릴리즈 판정 진행
