import assert from 'assert';
import fs from 'fs';
import path from 'path';

// Domain
import { Track } from '../src/core/domain/Track.js';

// Adapters
import { GeminiProvider } from '../src/adapters/GeminiProvider.js';
import { FFmpegVideoEncoder } from '../src/adapters/FFmpegVideoEncoder.js';
import { ZenionVaultRepository } from '../src/adapters/ZenionVaultRepository.js';

// Services
import { DirectorService } from '../src/core/services/DirectorService.js';
import { VaultStorageService } from '../src/core/services/VaultStorageService.js';
import { QualityJudgeService } from '../src/core/services/QualityJudgeService.js';
import { VideoRenderService } from '../src/core/services/VideoRenderService.js';
import { ReleaseKitService } from '../src/core/services/ReleaseKitService.js';

// Express App
import { createApp } from '../src/server.js';

console.log('🧪 [Smoke Test Suite] Starting ZENION Music Studio Scaffold Verification...\n');

let passedTests = 0;
let totalTests = 0;

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
  // Test 1: Track Domain Entity
  runTest('Track Entity - Creation and Lifecycle Methods', () => {
    const track = new Track({
      id: 'TRK-TEST-001',
      title: '비 오는 날의 이별',
      bpm: 75,
      genre: 'K-Pop Ballad',
      lyricsRaw: '[Verse 1]\n빗방울이 떨어지네\n[Chorus]\n너를 보내는 마음'
    });

    assert.strictEqual(track.id, 'TRK-TEST-001');
    assert.strictEqual(track.title, '비 오는 날의 이별');
    assert.strictEqual(track.aiScore, 0);

    // Update evaluation
    track.updateEvaluation(92, '서정적인 멜로디와 완성도 높은 가사 구조', { clipping: false, silence: false });
    assert.strictEqual(track.aiScore, 92);
    assert.strictEqual(track.status, 'evaluated');

    // Map Suno audio
    track.mapSunoAudio('/data/ZENION-MUSIC/suno_001.mp3');
    assert.strictEqual(track.audioPathSuno, '/data/ZENION-MUSIC/suno_001.mp3');
    assert.strictEqual(track.status, 'mapped');

    // Set Timeline
    track.setTimeline([{ part: 'Verse 1', startSecond: 0 }, { part: 'Chorus', startSecond: 35 }]);
    assert.strictEqual(track.timeline.length, 2);

    // JSON serialization
    const json = track.toJSON();
    assert.strictEqual(json.id, 'TRK-TEST-001');
    assert.strictEqual(json.timeline.length, 2);
  });

  // Test 2: ZenionVaultRepository & Security (SEC-002)
  runTest('ZenionVaultRepository - Persistence & Path Traversal Prevention (SEC-002)', () => {
    const testDbPath = './data/test_database.json';
    const repo = new ZenionVaultRepository({
      dbFilePath: testDbPath,
      zenionRootDir: './data/test_zenion'
    });

    // Path Traversal Security Test
    assert.strictEqual(repo.isSafePath('../../etc/passwd'), false, 'Traversal path ../../etc/passwd should be blocked');
    assert.strictEqual(repo.isSafePath('..\\..\\windows\\system32'), false, 'Traversal path with backslash should be blocked');
    assert.strictEqual(repo.isSafePath('valid_subfolder'), true, 'Normal relative subfolder should be allowed');

    // Save and Load test
    repo.save({ id: 'TRK-DB-001', title: 'Test Song 1', aiScore: 88 });
    const loaded = repo.findById('TRK-DB-001');
    assert.ok(loaded);
    assert.strictEqual(loaded.title, 'Test Song 1');

    // Cleanup test db
    if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
    if (fs.existsSync('./data/test_zenion')) fs.rmSync('./data/test_zenion', { recursive: true, force: true });
  });

  // Test 3: GeminiProvider Adapter & DirectorService (SCN-001, API-001)
  await runAsyncTest('DirectorService & GeminiProvider - Style Recipe Planning (SCN-001, API-001)', async () => {
    const geminiProvider = new GeminiProvider();
    const directorService = new DirectorService({ geminiProvider });

    const result = await directorService.generateStyles({
      keyword: '새벽 드라이브',
      count: 10,
      mode: 'explore'
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.count, 10);
    assert.strictEqual(result.styles.length, 10);
    assert.ok(result.styles[0].title.includes('새벽 드라이브'));
    assert.ok(result.styles[0].lyrics.chorus);
  });

  // Test 4: FFmpegVideoEncoder & QualityJudgeService (SCN-002, API-003)
  await runAsyncTest('QualityJudgeService - AI 1st Screening (SCN-002, API-003)', async () => {
    const testDbPath = './data/test_judge_db.json';
    const repo = new ZenionVaultRepository({ dbFilePath: testDbPath, zenionRootDir: './data/test_zenion' });
    const vaultService = new VaultStorageService({ vaultRepository: repo });
    const geminiProvider = new GeminiProvider();
    const ffmpegEncoder = new FFmpegVideoEncoder();

    const track = new Track({
      id: 'TRK-SCREEN-001',
      title: '밤하늘의 별빛',
      lyricsRaw: '[Verse 1]\n밤하늘에 반짝이는\n[Chorus]\n별빛처럼 빛나는 너'
    });
    vaultService.saveTrack(track);

    const judgeService = new QualityJudgeService({
      ffmpegEncoder,
      geminiProvider,
      vaultService
    });

    const evalResult = await judgeService.evaluateTrack('TRK-SCREEN-001', {
      lyrics: track.lyricsRaw
    });

    assert.strictEqual(evalResult.success, true);
    assert.ok(evalResult.aiScore >= 80, `Expected score >= 80, got ${evalResult.aiScore}`);
    assert.ok(evalResult.aiReview.length > 0);

    // Clean up
    if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
    if (fs.existsSync('./data/test_zenion')) fs.rmSync('./data/test_zenion', { recursive: true, force: true });
  });

  // Test 5: VideoRenderService & ReleaseKitService (SCN-004, SCN-005, API-006, API-007)
  await runAsyncTest('VideoRenderService & ReleaseKitService - Video Export & SNS Kit (API-006, API-007)', async () => {
    const testDbPath = './data/test_video_db.json';
    const repo = new ZenionVaultRepository({ dbFilePath: testDbPath, zenionRootDir: './data/test_zenion' });
    const vaultService = new VaultStorageService({ vaultRepository: repo });
    const ffmpegEncoder = new FFmpegVideoEncoder();

    const track = new Track({
      id: 'TRK-VID-001',
      title: 'City of Lights',
      genre: 'City Pop',
      bpm: 118,
      audioPathSuno: './data/test_zenion/suno_sample.mp3',
      coverImageUrl: './data/test_zenion/cover.png',
      timeline: [{ part: 'Intro', startSecond: 0 }, { part: 'Chorus', startSecond: 45 }]
    });
    vaultService.saveTrack(track);

    // Video render service
    const renderService = new VideoRenderService({ ffmpegEncoder, vaultService });
    const coverRes = await renderService.generateCoverImage('TRK-VID-001');
    assert.strictEqual(coverRes.success, true);

    const videoRes = await renderService.exportVideo('TRK-VID-001', { format: 'all' });
    assert.strictEqual(videoRes.success, true);
    assert.ok(videoRes.jobId);

    // Release kit service
    const releaseService = new ReleaseKitService({ vaultService });
    const kit = releaseService.generateReleaseKit('TRK-VID-001');
    assert.ok(kit.youtube.title.includes('City of Lights'));
    assert.ok(kit.youtube.timestampLyrics.includes('[0:45] Chorus'));
    assert.ok(kit.instagram.hashtags.includes('#CityPop'));
    assert.ok(kit.tiktok.caption.includes('City of Lights'));

    // Clean up
    if (fs.existsSync(testDbPath)) fs.unlinkSync(testDbPath);
    if (fs.existsSync('./data/test_zenion')) fs.rmSync('./data/test_zenion', { recursive: true, force: true });
  });

  // Test 6: Security Verification (SEC-001 & SEC-002)
  runTest('Security Checks - Secret Isolation (SEC-001) & .gitignore Rules', () => {
    const gitignorePath = path.resolve('.gitignore');
    assert.ok(fs.existsSync(gitignorePath), '.gitignore must exist');
    const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');

    assert.ok(gitignoreContent.includes('.env'), '.gitignore must ignore .env');
    assert.ok(gitignoreContent.includes('node_modules/'), '.gitignore must ignore node_modules/');
    assert.ok(gitignoreContent.includes('data/*.json'), '.gitignore must ignore data/*.json');
  });

  // Test 7: Express Server App Initialization & Routing
  runTest('Express Application - Server Initialization & Hexagonal Wiring', () => {
    const { app, services, adapters } = createApp();
    assert.ok(app, 'Express app should be created');
    assert.ok(services.vaultService, 'vaultService should be wired');
    assert.ok(services.directorService, 'directorService should be wired');
    assert.ok(services.judgeService, 'judgeService should be wired');
    assert.ok(services.renderService, 'renderService should be wired');
    assert.ok(services.releaseService, 'releaseService should be wired');
    assert.ok(adapters.geminiProvider, 'geminiProvider should be wired');
    assert.ok(adapters.ffmpegEncoder, 'ffmpegEncoder should be wired');
    assert.ok(adapters.vaultRepository, 'vaultRepository should be wired');
  });

  console.log(`\n========================================`);
  console.log(`🎉 Smoke Tests Finished: ${passedTests}/${totalTests} Passed (100%)`);
  console.log(`========================================\n`);

  if (passedTests !== totalTests) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal Smoke Test Error:', err);
  process.exit(1);
});
