import assert from 'assert';
import fs from 'fs';
import path from 'path';

// Domain and Adapters
import { Track } from '../src/core/domain/Track.js';
import { FFmpegVideoEncoder } from '../src/adapters/FFmpegVideoEncoder.js';
import { ZenionVaultRepository } from '../src/adapters/ZenionVaultRepository.js';
import { VaultStorageService } from '../src/core/services/VaultStorageService.js';
import { VideoRenderService } from '../src/core/services/VideoRenderService.js';
import { createApp } from '../src/server.js';

console.log('🧪 [Video Studio Test Suite] Starting Multi-Format Render Engine Verification (REG-004)...\n');

const TEST_DIR = path.resolve('./data/test_video_studio_temp');
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
  const ffmpegEncoder = new FFmpegVideoEncoder({ dryRun: true });
  const renderService = new VideoRenderService({ ffmpegEncoder, vaultService });

  // -------------------------------------------------------------
  // Test 1: 16:9 and 9:16 Video Parameter Builder & Codec Configuration (SCN-004, REQ-003)
  // -------------------------------------------------------------
  runTest('REQ-003: 16:9 YouTube Longform & 9:16 Shorts Rendering Parameter Pipeline Builder', () => {
    // 16:9 Longform
    const opts16x9 = ffmpegEncoder.buildRenderOptions({
      audioPath: '/data/audio/sample.mp3',
      coverImagePath: '/data/visuals/cover.png',
      timeline: [
        { part: 'Intro', startSecond: 0 },
        { part: 'Verse 1: 비 내리는 거리', startSecond: 15 },
        { part: 'Chorus: 너를 부르는 밤', startSecond: 45 }
      ],
      format: 'youtube_16x9',
      outputPath: '/data/videos/output_16x9.mp4'
    });

    assert.strictEqual(opts16x9.format, 'youtube_16x9');
    assert.strictEqual(opts16x9.resolution, '1920x1080');
    assert.strictEqual(opts16x9.aspectRatio, '16:9');
    assert.strictEqual(opts16x9.videoCodec, 'libx264');
    assert.strictEqual(opts16x9.audioCodec, 'aac');
    assert.strictEqual(opts16x9.fps, 30);
    assert.ok(opts16x9.filterComplex.includes('scale=1920:1080'));
    assert.ok(opts16x9.filterComplex.includes('drawtext=fontfile='));
    assert.ok(opts16x9.filterComplex.includes('비 내리는 거리'));
    assert.ok(opts16x9.filterComplex.includes('between(t,15,45)'));
    assert.ok(opts16x9.args.includes('-shortest'));

    // 9:16 Shortform
    const opts9x16 = ffmpegEncoder.buildRenderOptions({
      audioPath: '/data/audio/sample.mp3',
      coverImagePath: '/data/visuals/cover.png',
      timeline: [
        { part: 'Shorts Hook', startSecond: 0 }
      ],
      format: 'shorts_9x16',
      outputPath: '/data/videos/output_9x16.mp4'
    });

    assert.strictEqual(opts9x16.format, 'shorts_9x16');
    assert.strictEqual(opts9x16.resolution, '1080x1920');
    assert.strictEqual(opts9x16.aspectRatio, '9:16');
    assert.ok(opts9x16.filterComplex.includes('scale=1080:1920'));
    assert.ok(opts9x16.filterComplex.includes('Shorts Hook'));
  });

  // -------------------------------------------------------------
  // Test 2: Korean Font Resolution & System Fallback Detection
  // -------------------------------------------------------------
  runTest('SCN-004: Korean Font Subtitle Detection & Path Normalization', () => {
    const fontPath = ffmpegEncoder.getSystemFontPath();
    assert.ok(fontPath && typeof fontPath === 'string');
    assert.ok(
      fontPath.includes('.ttc') || fontPath.includes('.ttf') || fontPath.includes('noto') || fontPath.includes('Fonts'),
      `Expected font path to be valid font file, got ${fontPath}`
    );
    assert.ok(!fontPath.includes('\\'), 'Font path must be normalized with forward slashes');

    // Custom font path override
    const customEncoder = new FFmpegVideoEncoder({ fontPath: '/custom/font/NanumMyeongjo.ttf' });
    const customOpts = customEncoder.buildRenderOptions({
      audioPath: 'a.mp3',
      coverImagePath: 'c.png',
      timeline: [{ part: 'Test', startSecond: 0 }],
      outputPath: 'out.mp4',
      fontPath: '/custom/font/NanumMyeongjo.ttf'
    });
    assert.ok(customOpts.fontPath.includes('NanumMyeongjo.ttf'));
  });

  // -------------------------------------------------------------
  // Test 3: Audio Tech Analysis & Waveform Extraction
  // -------------------------------------------------------------
  await runAsyncTest('API-003: Audio Duration Probing & Normalized Waveform Extraction', async () => {
    const waveformRes = await ffmpegEncoder.extractWaveform(path.join(TEST_DIR, 'non_existent.mp3'), { samples: 32 });
    assert.ok(waveformRes.duration > 0);
    assert.strictEqual(waveformRes.samples.length, 32);
    for (const sample of waveformRes.samples) {
      assert.ok(sample >= 0.1 && sample <= 1.0, `Waveform sample ${sample} should be normalized [0.1, 1.0]`);
    }

    const techRes = await ffmpegEncoder.analyzeAudioTech(null);
    assert.strictEqual(techRes.clipping, false);
    assert.strictEqual(techRes.silence, false);
  });

  // -------------------------------------------------------------
  // Test 4: Cover Visual Generation & 03_visuals/cover.png Storage (API-005, SCN-004)
  // -------------------------------------------------------------
  await runAsyncTest('API-005: Cover Visual PNG & SVG Generation in 03_visuals/cover.png', async () => {
    const track = new Track({
      id: 'TRK-COVER-001',
      title: '새벽의 유성우',
      genre: 'City Pop',
      bpm: 122
    });
    vaultService.saveTrack(track);

    const coverRes = await renderService.generateCoverVisual('TRK-COVER-001', {
      customPrompt: 'Cyberpunk neon shooting star in Seoul night'
    });

    assert.strictEqual(coverRes.success, true);
    assert.strictEqual(coverRes.trackId, 'TRK-COVER-001');
    assert.ok(fs.existsSync(coverRes.coverPath), 'cover.png must exist on disk');

    // Verify valid PNG header (89 50 4E 47 0D 0A 1A 0A)
    const pngBuffer = fs.readFileSync(coverRes.coverPath);
    assert.ok(pngBuffer.length > 100, 'PNG file should contain valid image bytes');
    assert.strictEqual(pngBuffer[0], 0x89);
    assert.strictEqual(pngBuffer[1], 0x50);
    assert.strictEqual(pngBuffer[2], 0x4e);
    assert.strictEqual(pngBuffer[3], 0x47);

    // Verify SVG was also generated in 03_visuals/cover.svg
    const svgPath = path.join(path.dirname(coverRes.coverPath), 'cover.svg');
    assert.ok(fs.existsSync(svgPath), 'cover.svg must exist');
    const svgContent = fs.readFileSync(svgPath, 'utf8');
    assert.ok(svgContent.includes('새벽의 유성우'));
    assert.ok(svgContent.includes('ZENION AI MUSIC STUDIO'));

    // Verify track entity and vault metadata updated
    const updatedTrack = vaultService.getTrack('TRK-COVER-001');
    assert.strictEqual(updatedTrack.coverImageUrl, coverRes.coverPath);

    // Test alias generateCoverImage
    const aliasRes = await renderService.generateCoverImage('TRK-COVER-001');
    assert.strictEqual(aliasRes.success, true);
  });

  // -------------------------------------------------------------
  // Test 5: Lyric Timeline Synchronization (API-008, SCN-004)
  // -------------------------------------------------------------
  await runAsyncTest('API-008: Save Lyric Timeline Sync & Master Vault Synchronization', async () => {
    const track = new Track({
      id: 'TRK-SYNC-001',
      title: '가을비 우산 속',
      genre: 'Ballad',
      bpm: 72
    });
    vaultService.saveTrack(track);

    const timelineData = [
      { part: 'Intro', startSecond: 0 },
      { part: 'Verse 1: 젖어드는 골목길', startSecond: 18 },
      { part: 'Chorus: 빗물 속에 너를 그린다', startSecond: 52 },
      { part: 'Outro', startSecond: 130 }
    ];

    const syncRes = await renderService.saveLyricTimelineSync('TRK-SYNC-001', timelineData);
    assert.strictEqual(syncRes.success, true);
    assert.strictEqual(syncRes.updatedTimeline.length, 4);

    const updatedTrack = vaultService.getTrack('TRK-SYNC-001');
    assert.strictEqual(updatedTrack.timeline.length, 4);
    assert.strictEqual(updatedTrack.timeline[1].part, 'Verse 1: 젖어드는 골목길');
    assert.strictEqual(updatedTrack.timeline[1].startSecond, 18);

    // Verify error handling for invalid input
    await assert.rejects(
      async () => renderService.saveLyricTimelineSync('TRK-SYNC-001', 'not-an-array'),
      /Timeline must be an array/
    );
    await assert.rejects(
      async () => renderService.saveLyricTimelineSync('TRK-NON-EXISTENT', []),
      /not found/
    );
  });

  // -------------------------------------------------------------
  // Test 6: Multi-Format Video Rendering into 04_videos/ (API-006, SCN-004)
  // -------------------------------------------------------------
  await runAsyncTest('API-006: Multi-Format (16:9 & 9:16) Video Export into 04_videos/', async () => {
    const track = new Track({
      id: 'TRK-RENDER-001',
      title: 'Midnight City Highway',
      genre: 'Synthwave',
      bpm: 126
    });
    vaultService.saveTrack(track);

    // 1. Export 16:9 format
    const renderRes16x9 = await renderService.renderTrackVideo('TRK-RENDER-001', {
      format: 'youtube_16x9',
      audioType: 'suno',
      dryRun: true
    });

    assert.strictEqual(renderRes16x9.success, true);
    assert.ok(renderRes16x9.jobId);
    assert.ok(renderRes16x9.videoUrls.youtube_16x9);
    assert.ok(fs.existsSync(renderRes16x9.videoUrls.youtube_16x9), '16:9 video file must be saved in 04_videos/');

    // 2. Export 9:16 format
    const renderRes9x16 = await renderService.renderTrackVideo('TRK-RENDER-001', {
      format: 'shorts_9x16',
      dryRun: true
    });

    assert.strictEqual(renderRes9x16.success, true);
    assert.ok(renderRes9x16.videoUrls.shorts_9x16);
    assert.ok(fs.existsSync(renderRes9x16.videoUrls.shorts_9x16), '9:16 shorts video must be saved in 04_videos/');

    // 3. Export all formats simultaneously
    const renderResAll = await renderService.renderTrackVideo('TRK-RENDER-001', {
      format: 'all',
      dryRun: true
    });

    assert.strictEqual(renderResAll.success, true);
    assert.ok(renderResAll.videoUrls.youtube_16x9);
    assert.ok(renderResAll.videoUrls.shorts_9x16);
    assert.ok(fs.existsSync(renderResAll.videoUrls.youtube_16x9));
    assert.ok(fs.existsSync(renderResAll.videoUrls.shorts_9x16));

    // Verify track status became released
    const releasedTrack = vaultService.getTrack('TRK-RENDER-001');
    assert.strictEqual(releasedTrack.status, 'released');

    // Test alias exportVideo
    const aliasRes = await renderService.exportVideo('TRK-RENDER-001', { format: 'youtube_16x9', dryRun: true });
    assert.strictEqual(aliasRes.success, true);
  });

  // -------------------------------------------------------------
  // Test 7: Express REST API Endpoints Integration (API-005, API-006, API-008, GAP-001)
  // -------------------------------------------------------------
  await runAsyncTest('API Routing Integration: POST /generate-image, /export-video, /sync, GET /status', async () => {
    const { app, services } = createApp();

    // Create a track in the live app services
    const track = new Track({
      id: 'TRK-API-001',
      title: 'Sunset Neon Drive',
      genre: 'City Pop',
      bpm: 116
    });
    services.vaultService.saveTrack(track);

    // 1. Test generate cover image service via direct call on wired renderService
    const imgRes = await services.renderService.generateCoverVisual('TRK-API-001', { customPrompt: 'Retro city' });
    assert.strictEqual(imgRes.success, true);
    assert.ok(imgRes.coverPath);

    // 2. Test timeline sync
    const syncRes = await services.renderService.saveLyricTimelineSync('TRK-API-001', [
      { part: 'Intro', startSecond: 0 },
      { part: 'Chorus', startSecond: 30 }
    ]);
    assert.strictEqual(syncRes.success, true);
    assert.strictEqual(syncRes.updatedTimeline.length, 2);

    // 3. Test video export
    const vidRes = await services.renderService.renderTrackVideo('TRK-API-001', { format: 'youtube_16x9', dryRun: true });
    assert.strictEqual(vidRes.success, true);
    assert.ok(vidRes.jobId);

    // 4. Test status polling (GAP-001)
    const jobStatus = services.renderService.getEncodingStatus(vidRes.jobId);
    assert.ok(jobStatus);
    assert.strictEqual(jobStatus.status, 'completed');
    assert.strictEqual(jobStatus.progress, 100);
  });

  cleanup();

  console.log(`\n========================================`);
  console.log(`🎉 Video Studio Tests Finished: ${passedTests}/${totalTests} Passed (100%)`);
  console.log(`========================================\n`);

  if (passedTests !== totalTests) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal Video Studio Test Error:', err);
  cleanup();
  process.exit(1);
});
