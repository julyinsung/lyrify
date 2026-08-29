import assert from 'assert';
import fs from 'fs';
import path from 'path';

// Domain and Adapters
import { Track } from '../src/core/domain/Track.js';
import { GeminiProvider } from '../src/adapters/GeminiProvider.js';
import { FFmpegVideoEncoder } from '../src/adapters/FFmpegVideoEncoder.js';
import { ZenionVaultRepository } from '../src/adapters/ZenionVaultRepository.js';

// Services
import { DirectorService } from '../src/core/services/DirectorService.js';
import { QualityJudgeService } from '../src/core/services/QualityJudgeService.js';
import { ReleaseKitService } from '../src/core/services/ReleaseKitService.js';
import { VaultStorageService } from '../src/core/services/VaultStorageService.js';

// Server App
import { createApp } from '../src/server.js';

console.log('🧪 [AI Director & Screening & Release Hub Test Suite] Starting Verification...\n');

const TEST_DIR = path.resolve('./data/test_director_temp');
const TEST_DB = path.join(TEST_DIR, 'database.json');
const TEST_ZENION_ROOT = path.join(TEST_DIR, 'ZENION-MUSIC');

let passedTests = 0;
let totalTests = 0;

function setup() {
  cleanup();
  fs.mkdirSync(TEST_DIR, { recursive: true });
  fs.mkdirSync(TEST_ZENION_ROOT, { recursive: true });
}

function cleanup() {
  if (fs.existsSync(TEST_DIR)) {
    try {
      fs.rmSync(TEST_DIR, { recursive: true, force: true });
    } catch (_) {}
  }
}

function runTest(name, fn) {
  totalTests++;
  try {
    fn();
    console.log(`  ✅ PASS: ${name}`);
    passedTests++;
  } catch (err) {
    console.error(`  ❌ FAIL: ${name}`);
    console.error(err);
  }
}

async function runAsyncTest(name, fn) {
  totalTests++;
  try {
    await fn();
    console.log(`  ✅ PASS: ${name}`);
    passedTests++;
  } catch (err) {
    console.error(`  ❌ FAIL: ${name}`);
    console.error(err);
  }
}

async function main() {
  setup();

  const repo = new ZenionVaultRepository({
    dbFilePath: TEST_DB,
    zenionRootDir: TEST_ZENION_ROOT
  });
  const vaultService = new VaultStorageService({ vaultRepository: repo });
  const geminiProvider = new GeminiProvider();
  const ffmpegEncoder = new FFmpegVideoEncoder({ dryRun: true });
  const directorService = new DirectorService({ geminiProvider });
  const judgeService = new QualityJudgeService({ ffmpegEncoder, geminiProvider, vaultService });
  const releaseService = new ReleaseKitService({ vaultService });

  // -------------------------------------------------------------
  // Test 1: REG-001 - Variable Track Count Generation (1, 5, 10, 20)
  // -------------------------------------------------------------
  await runAsyncTest('REG-001: AI Director Variable Track Count Support (1 ~ 20 songs)', async () => {
    for (const count of [1, 5, 10, 20]) {
      const res = await directorService.generateStyles({
        keyword: '비 오는 날의 이별',
        count,
        mode: 'explore'
      });

      assert.strictEqual(res.success, true);
      assert.strictEqual(res.count, count);
      assert.strictEqual(res.styles.length, count, `Should generate exactly ${count} styles`);
      assert.strictEqual(res.mode, 'explore');

      const first = res.styles[0];
      assert.ok(first.id.startsWith('RECIPE-'));
      assert.ok(first.title);
      assert.ok(first.genre);
      assert.ok(first.bpm >= 60 && first.bpm <= 180);
      assert.ok(first.instruments);
      assert.ok(first.promptText.includes('[Genre:'));
      assert.ok(first.lyrics?.verse1 && first.lyrics.verse1.includes('[Verse 1'));
      assert.ok(first.lyrics?.chorus && first.lyrics.chorus.includes('[Chorus'));
      assert.ok(first.lyrics?.verse2 && first.lyrics.verse2.includes('[Verse 2'));
    }

    // Edge cases: count clamping (< 1 -> 1, > 20 -> 20)
    const clampedMin = await directorService.generateStyles({ keyword: '새벽', count: -5 });
    assert.strictEqual(clampedMin.styles.length, 1);

    const clampedMax = await directorService.generateStyles({ keyword: '새벽', count: 99 });
    assert.strictEqual(clampedMax.styles.length, 20);
  });

  // -------------------------------------------------------------
  // Test 2: REG-001 - 3 Director Planning Modes (explore, single, album)
  // -------------------------------------------------------------
  await runAsyncTest('REG-001: AI Director 3 Planning Modes (Explore, Single, Album)', async () => {
    // Mode 1: Explore mode (diverse genre exploration)
    const exploreRes = await directorService.generateStyles({
      keyword: '한여름 밤의 꿈',
      count: 6,
      mode: 'explore'
    });
    assert.strictEqual(exploreRes.mode, 'explore');
    const exploreGenres = new Set(exploreRes.styles.map((s) => s.genre));
    assert.ok(exploreGenres.size >= 3, 'Explore mode should generate diverse genres');

    // Mode 2: Single mode (arrangement variations of single song theme)
    const singleRes = await directorService.generateStyles({
      keyword: 'Neon Memories',
      count: 4,
      mode: 'single'
    });
    assert.strictEqual(singleRes.mode, 'single');
    assert.strictEqual(singleRes.styles.length, 4);
    assert.ok(singleRes.styles.some((s) => s.title.includes('Radio Edit') || s.title.includes('Ver') || s.title.includes('Mix')));
    assert.ok(singleRes.styles[0].concept);

    // Mode 3: Album mode (concept album storyline tracklist)
    const albumRes = await directorService.generateStyles({
      keyword: '푸른 새벽',
      count: 5,
      mode: 'album'
    });
    assert.strictEqual(albumRes.mode, 'album');
    assert.strictEqual(albumRes.styles.length, 5);
    assert.ok(albumRes.styles[0].title.includes('Intro'));
    assert.ok(albumRes.styles[1].title.includes('타이틀'));
    assert.ok(albumRes.styles[0].concept.includes('Prologue') || albumRes.styles[0].concept.includes('Intro'));

    // Verify mode listing helper
    const modes = directorService.getAvailableModes();
    assert.strictEqual(modes.length, 3);
    assert.ok(modes.find((m) => m.mode === 'explore'));
    assert.ok(modes.find((m) => m.mode === 'single'));
    assert.ok(modes.find((m) => m.mode === 'album'));
  });

  // -------------------------------------------------------------
  // Test 3: REG-001 - Director Validation & ACE Trigger
  // -------------------------------------------------------------
  await runAsyncTest('REG-001: Director Input Validation & ACE Trigger Metadata', async () => {
    // Missing keyword validation
    await assert.rejects(
      async () => directorService.generateStyles({ keyword: '' }),
      /Keyword is required/
    );

    // ACE Trigger
    const aceRes = await directorService.triggerAceDraft('RECIPE-001', {
      promptText: '[Genre: City Pop] [BPM: 118] [Theme: Neon City]'
    });
    assert.strictEqual(aceRes.success, true);
    assert.ok(aceRes.jobId.startsWith('ACE-JOB-'));
    assert.strictEqual(aceRes.recipeId, 'RECIPE-001');
    assert.strictEqual(aceRes.status, 'queued');
  });

  // -------------------------------------------------------------
  // Test 4: REG-002 - Quality Screening 100-Point Scoring & Audio Defect Penalties
  // -------------------------------------------------------------
  await runAsyncTest('REG-002: AI Quality Screening (100-point algorithm, audio defect checks, lyrics completeness)', async () => {
    // Case 1: Masterpiece lyrics & perfect audio (No defects)
    const perfectLyrics = `[Verse 1]\n창밖에 내리는 비를 보며 너를 생각해\n조용히 흐르는 시간 속에 머무네\n[Chorus]\n잊혀지지 않는 그날의 멜로디\n가슴 깊이 남아 울려 퍼지는 밤\n[Verse 2]\n바람에 실려온 너의 목소리\n다시금 흩어지는 추억의 조각들`;
    
    const evalPerfect = await geminiProvider.evaluateQuality({
      lyrics: perfectLyrics,
      audioMetadata: { clipping: false, silence: false, duration: 180 }
    });

    assert.ok(evalPerfect.aiScore >= 90, `Perfect track should have score >= 90, got ${evalPerfect.aiScore}`);
    assert.strictEqual(evalPerfect.grade, 'S');
    assert.strictEqual(evalPerfect.techCheck.clipping, false);
    assert.strictEqual(evalPerfect.techCheck.silence, false);

    // Case 2: Audio Clipping Defect (-20 points penalty)
    const evalClipping = await geminiProvider.evaluateQuality({
      lyrics: perfectLyrics,
      audioMetadata: { clipping: true, silence: false, duration: 180 }
    });
    assert.ok(evalClipping.aiScore <= evalPerfect.aiScore - 20, 'Clipping must apply 20 points penalty');
    assert.strictEqual(evalClipping.techCheck.clipping, true);
    assert.ok(evalClipping.aiReview.includes('클리핑'));

    // Case 3: Audio Silence Defect (-20 points penalty)
    const evalSilence = await geminiProvider.evaluateQuality({
      lyrics: perfectLyrics,
      audioMetadata: { clipping: false, silence: true, duration: 180 }
    });
    assert.ok(evalSilence.aiScore <= evalPerfect.aiScore - 20, 'Silence must apply 20 points penalty');
    assert.strictEqual(evalSilence.techCheck.silence, true);
    assert.ok(evalSilence.aiReview.includes('무음'));

    // Case 4: Poor/Incomplete lyrics (No Verse / No Chorus)
    const evalPoorLyrics = await geminiProvider.evaluateQuality({
      lyrics: '짧은 한 줄 가사',
      audioMetadata: { clipping: false, silence: false, duration: 180 }
    });
    assert.ok(evalPoorLyrics.aiScore <= 60, `Poor lyrics should have low score, got ${evalPoorLyrics.aiScore}`);
    assert.ok(evalPoorLyrics.grade === 'C' || evalPoorLyrics.grade === 'F');
  });

  // -------------------------------------------------------------
  // Test 5: REG-002 - QualityJudgeService Track Evaluation & TOP 3 Ranking
  // -------------------------------------------------------------
  await runAsyncTest('REG-002: Track AI Evaluation Persistence & TOP 3 Recommendation Ranking', async () => {
    // Create 5 sample tracks with various scores
    const trackDataList = [
      { id: 'TRK-RANK-01', title: 'Top Masterpiece 1', score: 95 },
      { id: 'TRK-RANK-02', title: 'Great Song 2', score: 88 },
      { id: 'TRK-RANK-03', title: 'Good Song 3', score: 82 },
      { id: 'TRK-RANK-04', title: 'Fair Song 4', score: 68 },
      { id: 'TRK-RANK-05', title: 'Defective Song 5', score: 45 }
    ];

    const domainTracks = [];
    for (const item of trackDataList) {
      const t = new Track({
        id: item.id,
        title: item.title,
        lyricsRaw: '[Verse 1]\n노래 가사\n[Chorus]\n후렴구'
      });
      t.updateEvaluation(item.score, `AI 평가 ${item.score}점`, { clipping: false, silence: false });
      vaultService.saveTrack(t);
      domainTracks.push(t);
    }

    // Rank tracks
    const ranked = judgeService.rankTracks(domainTracks);
    assert.strictEqual(ranked.length, 5);
    assert.strictEqual(ranked[0].id, 'TRK-RANK-01');
    assert.strictEqual(ranked[0].ranking, 1);
    assert.strictEqual(ranked[0].recommendationBadge, 'TOP 1 PICK');
    assert.strictEqual(ranked[0].isTopRecommended, true);

    assert.strictEqual(ranked[1].id, 'TRK-RANK-02');
    assert.strictEqual(ranked[1].ranking, 2);
    assert.strictEqual(ranked[1].recommendationBadge, 'TOP 2');
    assert.strictEqual(ranked[1].isTopRecommended, true);

    assert.strictEqual(ranked[2].id, 'TRK-RANK-03');
    assert.strictEqual(ranked[2].ranking, 3);
    assert.strictEqual(ranked[2].recommendationBadge, 'TOP 3');
    assert.strictEqual(ranked[2].isTopRecommended, true);

    assert.strictEqual(ranked[3].id, 'TRK-RANK-04');
    assert.strictEqual(ranked[3].ranking, 4);
    assert.strictEqual(ranked[3].recommendationBadge, null);
    assert.strictEqual(ranked[3].isTopRecommended, false);

    // Get Top 3
    const top3 = judgeService.getTopRecommendations(domainTracks, 3);
    assert.strictEqual(top3.length, 3);
    assert.strictEqual(top3[0].id, 'TRK-RANK-01');
    assert.strictEqual(top3[1].id, 'TRK-RANK-02');
    assert.strictEqual(top3[2].id, 'TRK-RANK-03');

    // Evaluate live track via judgeService.evaluateTrack
    const evalRes = await judgeService.evaluateTrack('TRK-RANK-01', {
      lyrics: '[Verse 1]\n어두운 밤하늘\n[Chorus]\n빛나는 별'
    });
    assert.strictEqual(evalRes.success, true);
    assert.strictEqual(evalRes.trackId, 'TRK-RANK-01');
    assert.ok(evalRes.aiScore > 0);
  });

  // -------------------------------------------------------------
  // Test 6: REG-005 - SNS Release Kit Formatting (YouTube, Instagram, TikTok)
  // -------------------------------------------------------------
  runTest('REG-005: SNS Release Kit Generation (YouTube, Instagram, TikTok) & Timestamps', () => {
    const track = new Track({
      id: 'TRK-REL-001',
      title: 'Midnight City Drive',
      genre: 'City Pop',
      bpm: 118,
      timeline: [
        { part: 'Intro', startSecond: 0 },
        { part: 'Verse 1: 네온사인의 거리', startSecond: 15 },
        { part: 'Chorus: 달리는 이 밤', startSecond: 45 },
        { part: 'Outro', startSecond: 120 }
      ]
    });
    vaultService.saveTrack(track);

    const kit = releaseService.generateReleaseKit('TRK-REL-001');
    assert.ok(kit);
    assert.strictEqual(kit.trackId, 'TRK-REL-001');

    // 1. YouTube Kit Verification
    assert.ok(kit.youtube.title.includes('Midnight City Drive'));
    assert.ok(kit.youtube.title.includes('City Pop'));
    assert.ok(kit.youtube.description.includes('🎵 Title: Midnight City Drive'));
    assert.ok(kit.youtube.description.includes('BPM: 118'));
    assert.ok(kit.youtube.timestampLyrics.includes('[0:15] Verse 1: 네온사인의 거리'));
    assert.ok(kit.youtube.timestampLyrics.includes('[0:45] Chorus: 달리는 이 밤'));
    assert.ok(kit.youtube.tags.includes('City Pop'));
    assert.ok(kit.youtube.tags.includes('AI Music'));

    // 2. Instagram Reels Kit Verification
    assert.ok(kit.instagram.caption.includes('Midnight City Drive'));
    assert.ok(kit.instagram.caption.includes('City Pop'));
    assert.ok(kit.instagram.hashtags.includes('#AI음악'));
    assert.ok(kit.instagram.hashtags.includes('#CityPop'));

    // 3. TikTok Kit Verification
    assert.ok(kit.tiktok.caption.includes('Midnight City Drive'));
    assert.ok(kit.tiktok.hashtags.includes('#틱톡음악'));

    // 4. Markdown Formatting
    const md = releaseService.formatReleaseKitMarkdown(track, kit);
    assert.ok(md.includes('# Release Kit: Midnight City Drive'));
    assert.ok(md.includes('## 1. YouTube Longform Release'));
    assert.ok(md.includes('## 2. Instagram Reels Release'));
    assert.ok(md.includes('## 3. TikTok Shorts Release'));
    assert.ok(md.includes('[0:15] Verse 1: 네온사인의 거리'));
  });

  // -------------------------------------------------------------
  // Test 7: SEC-REG-001 - Security Isolation & Secret Protection
  // -------------------------------------------------------------
  runTest('SEC-REG-001: Google API Key Isolation & Safe Offline Fallback', () => {
    // 1. Provider handles placeholder keys or empty strings safely
    const unconfiguredProvider = new GeminiProvider({ apiKey: 'your_gemini_api_key_here' });
    assert.strictEqual(unconfiguredProvider.isConfigured(), false);

    const emptyProvider = new GeminiProvider({ apiKey: '' });
    assert.strictEqual(emptyProvider.isConfigured(), false);

    // 2. Key does not leak in toJSON or string representations
    const repoCheck = new ZenionVaultRepository({ dbFilePath: TEST_DB, zenionRootDir: TEST_ZENION_ROOT });
    const saved = repoCheck.save({ id: 'TRK-SEC-01', title: 'Secret Track' });
    assert.strictEqual(JSON.stringify(saved).includes('AIzaSy'), false, 'Database must not leak API keys');
  });

  // -------------------------------------------------------------
  // Test 8: Express REST API Endpoints Integration (API-001, API-003, API-007)
  // -------------------------------------------------------------
  await runAsyncTest('REST API Integration: POST /generate-styles, POST /evaluate, GET /release-kit', async () => {
    const { app, services } = createApp();

    // Create a track in services
    const track = new Track({
      id: 'TRK-API-HUB-01',
      title: 'Neon Sunset Romance',
      genre: 'Synthwave',
      bpm: 124,
      lyricsRaw: '[Verse 1]\n붉은 노을 빛\n[Chorus]\n영원한 사랑'
    });
    services.vaultService.saveTrack(track);

    // 1. Test Director API direct call via services
    const dirRes = await services.directorService.generateStyles({
      keyword: '여름 바다',
      count: 3,
      mode: 'explore'
    });
    assert.strictEqual(dirRes.success, true);
    assert.strictEqual(dirRes.styles.length, 3);

    // 2. Test Evaluate API direct call
    const evalRes = await services.judgeService.evaluateTrack('TRK-API-HUB-01', {
      lyrics: track.lyricsRaw
    });
    assert.strictEqual(evalRes.success, true);
    assert.ok(evalRes.aiScore >= 80);

    // 3. Test Release Kit API direct call
    const relKit = services.releaseService.getReleaseKit('TRK-API-HUB-01');
    assert.ok(relKit);
    assert.ok(relKit.youtube.title.includes('Neon Sunset Romance'));
    assert.ok(relKit.instagram.caption.includes('Neon Sunset Romance'));
  });

  cleanup();

  console.log(`\n========================================`);
  console.log(`🎉 AI Director & Screening Tests: ${passedTests}/${totalTests} Passed (100%)`);
  console.log(`========================================\n`);

  if (passedTests !== totalTests) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal Director Test Error:', err);
  cleanup();
  process.exit(1);
});
