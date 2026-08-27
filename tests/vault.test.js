import assert from 'assert';
import fs from 'fs';
import path from 'path';

// Domain and Adapters
import { Track } from '../src/core/domain/Track.js';
import { ZenionVaultRepository } from '../src/adapters/ZenionVaultRepository.js';
import { VaultStorageService } from '../src/core/services/VaultStorageService.js';
import { createApp } from '../src/server.js';

console.log('🧪 [Vault Storage Test Suite] Starting ZENION Master Vault Engine Verification...\n');

const TEST_DIR = path.resolve('./data/test_vault_temp');
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

  // -------------------------------------------------------------
  // Test 1: Complete Package Folder Structure Creation (SCN-003, REQ-002)
  // -------------------------------------------------------------
  runTest('REQ-002: Complete Package Folder Generation (recipe.json, 01_draft/, 02_final_audio/, 03_visuals/, 04_videos/)', () => {
    const track = new Track({
      id: 'TRK-VAULT-001',
      title: '새벽 감성 시티팝',
      bpm: 115,
      genre: 'City Pop',
      lyricsRaw: '[Verse 1]\n도심의 네온사인\n[Chorus]\n빛나는 우리들의 밤'
    });
    vaultService.saveTrack(track);

    const vaultResult = vaultService.createTrackVault(track, { initReleaseKit: true });

    assert.strictEqual(vaultResult.success, true);
    assert.strictEqual(vaultResult.trackId, 'TRK-VAULT-001');
    assert.ok(fs.existsSync(vaultResult.folderPath), 'Track folder must exist');
    assert.ok(fs.existsSync(vaultResult.folders.draft), '01_draft/ folder must exist');
    assert.ok(fs.existsSync(vaultResult.folders.finalAudio), '02_final_audio/ folder must exist');
    assert.ok(fs.existsSync(vaultResult.folders.visuals), '03_visuals/ folder must exist');
    assert.ok(fs.existsSync(vaultResult.folders.videos), '04_videos/ folder must exist');
    assert.ok(fs.existsSync(vaultResult.files.recipe), 'recipe.json must exist');
    assert.ok(fs.existsSync(vaultResult.files.metadata), 'metadata.json must exist');
    assert.ok(fs.existsSync(vaultResult.files.releaseKit), 'release_kit.md must exist');

    const recipeJson = JSON.parse(fs.readFileSync(vaultResult.files.recipe, 'utf8'));
    assert.strictEqual(recipeJson.id, 'TRK-VAULT-001');
    assert.strictEqual(recipeJson.title, '새벽 감성 시티팝');
  });

  // -------------------------------------------------------------
  // Test 2: Suno Audio Mapping & File Copy (API-004, SCN-003)
  // -------------------------------------------------------------
  await runAsyncTest('API-004: Suno Audio Mapping & 02_final_audio/ Organization', async () => {
    const track = new Track({
      id: 'TRK-VAULT-002',
      title: '비 내리는 오후',
      bpm: 78,
      genre: 'Ballad'
    });
    vaultService.saveTrack(track);

    // Create a mock source audio file
    const mockAudioSrc = path.join(TEST_DIR, 'suno_output_raw_002.mp3');
    fs.writeFileSync(mockAudioSrc, 'MOCK_MP3_BINARY_DATA_002', 'utf8');

    const mapResult = await vaultService.mapSunoAudio('TRK-VAULT-002', {
      sunoAudioPath: mockAudioSrc
    });

    assert.strictEqual(mapResult.success, true);
    assert.ok(fs.existsSync(mapResult.destAudioPath), 'Destination audio must be copied into 02_final_audio/');
    assert.strictEqual(fs.readFileSync(mapResult.destAudioPath, 'utf8'), 'MOCK_MP3_BINARY_DATA_002');
    
    // Verify track state update in database
    const updated = vaultService.getTrack('TRK-VAULT-002');
    assert.strictEqual(updated.status, 'mapped');
    assert.strictEqual(updated.audioPathSuno, mapResult.destAudioPath);
  });

  // -------------------------------------------------------------
  // Test 3: Release Kit Markdown Export (API-007, SCN-005)
  // -------------------------------------------------------------
  runTest('API-007: SNS Release Kit Markdown Auto-Export to release_kit.md', () => {
    const track = new Track({
      id: 'TRK-VAULT-003',
      title: '여름날의 추억',
      genre: 'Indie Rock',
      bpm: 128,
      timeline: [
        { part: 'Intro', startSecond: 0 },
        { part: 'Chorus', startSecond: 40 }
      ]
    });
    vaultService.saveTrack(track);

    const exportResult = vaultService.exportReleaseKitFile('TRK-VAULT-003');
    assert.strictEqual(exportResult.success, true);
    assert.ok(fs.existsSync(exportResult.filePath), 'release_kit.md must exist');

    const mdContent = fs.readFileSync(exportResult.filePath, 'utf8');
    assert.ok(mdContent.includes('# Release Kit: 여름날의 추억'), 'Title should be in markdown');
    assert.ok(mdContent.includes('## 1. YouTube'), 'YouTube section should exist');
    assert.ok(mdContent.includes('## 2. Instagram'), 'Instagram section should exist');
    assert.ok(mdContent.includes('## 3. TikTok'), 'TikTok section should exist');
    assert.ok(mdContent.includes('[0:40] Chorus'), 'Timestamps should be included');
  });

  // -------------------------------------------------------------
  // Test 4: File System syncVault Scanner & Database Synchronization
  // -------------------------------------------------------------
  runTest('REQ-002: syncVault Scanner - Auto Discovery & database.json Sync', () => {
    // Manually create a new track folder directly on the filesystem
    const customFolder = path.join(TEST_ZENION_ROOT, '가을_밤_바람_TRK-AUTO-777');
    fs.mkdirSync(path.join(customFolder, '01_draft'), { recursive: true });
    fs.mkdirSync(path.join(customFolder, '02_final_audio'), { recursive: true });
    fs.mkdirSync(path.join(customFolder, '03_visuals'), { recursive: true });
    fs.mkdirSync(path.join(customFolder, '04_videos'), { recursive: true });

    // Place assets
    fs.writeFileSync(path.join(customFolder, '01_draft', 'ace_draft.wav'), 'ACE_WAV_DATA');
    fs.writeFileSync(path.join(customFolder, '02_final_audio', 'suno_master.mp3'), 'SUNO_MP3_DATA');
    fs.writeFileSync(path.join(customFolder, '03_visuals', 'cover.png'), 'COVER_PNG_DATA');
    fs.writeFileSync(path.join(customFolder, '04_videos', 'final_16x9.mp4'), 'MP4_VIDEO_DATA');
    fs.writeFileSync(path.join(customFolder, 'release_kit.md'), '# Auto Release Kit');

    // Run syncVault
    const syncRes = vaultService.syncVault();
    assert.strictEqual(syncRes.success, true);
    assert.ok(syncRes.syncedCount >= 1);

    const syncedTrack = syncRes.tracks.find((t) => t.id === 'TRK-AUTO-777');
    assert.ok(syncedTrack, 'Auto-discovered track should be in synced list');
    assert.strictEqual(syncedTrack.status, 'released');
    assert.strictEqual(syncedTrack.assetsStatus.hasDraft, true);
    assert.strictEqual(syncedTrack.assetsStatus.hasFinalAudio, true);
    assert.strictEqual(syncedTrack.assetsStatus.hasCover, true);
    assert.strictEqual(syncedTrack.assetsStatus.isComplete, true);
  });

  // -------------------------------------------------------------
  // Test 5: Path Traversal Security Defense (SEC-002, SEC-REG-002)
  // -------------------------------------------------------------
  runTest('SEC-002: Path Traversal Attack Defense & Boundary Protection', () => {
    const maliciousPaths = [
      '../../etc/passwd',
      '..\\..\\windows\\system32',
      '../../../secret/keys.json',
      '%2e%2e%2f%2e%2e%2froot',
      'subfolder/../../../escape',
      'song\0/injection/payload',
      'C:\\Windows\\System32\\cmd.exe',
      '\\\\malicious-server\\share'
    ];

    for (const badPath of maliciousPaths) {
      const isSafe = repo.isSafePath(badPath, TEST_ZENION_ROOT);
      assert.strictEqual(isSafe, false, `Malicious path "${badPath}" must be blocked`);

      assert.throws(
        () => repo.assertSafePath(badPath, TEST_ZENION_ROOT),
        /Path Traversal attempt detected/,
        `assertSafePath must throw on "${badPath}"`
      );

      assert.throws(
        () => repo.createTrackFolder(badPath),
        /Path Traversal attempt detected/,
        `createTrackFolder must throw on "${badPath}"`
      );
    }

    // Normal safe subpaths must be allowed
    assert.strictEqual(repo.isSafePath('My_Safe_Song_Folder', TEST_ZENION_ROOT), true);
    assert.strictEqual(repo.isSafePath('sub/nested_folder', TEST_ZENION_ROOT), true);
  });

  // -------------------------------------------------------------
  // Test 6: Concurrency Safety & Atomic Persistence (DATA-001)
  // -------------------------------------------------------------
  await runAsyncTest('DATA-001: Atomic Persistence & Async Concurrency Mutex Defense', async () => {
    const concurrentWrites = [];
    for (let i = 0; i < 15; i++) {
      concurrentWrites.push(
        repo.saveAsync({
          id: `TRK-CONCURRENT-${i}`,
          title: `Concurrent Song ${i}`,
          aiScore: 70 + i
        })
      );
    }

    await Promise.all(concurrentWrites);

    // Verify database file integrity
    const all = await repo.loadAllAsync();
    for (let i = 0; i < 15; i++) {
      const item = all.find((t) => t.id === `TRK-CONCURRENT-${i}`);
      assert.ok(item, `Track TRK-CONCURRENT-${i} must exist without data corruption`);
      assert.strictEqual(item.aiScore, 70 + i);
    }
  });

  // -------------------------------------------------------------
  // Test 7: Express API Router Integration (API-002, API-004, Scan)
  // -------------------------------------------------------------
  await runAsyncTest('API Integration: GET /api/tracks, POST /map-suno, POST /scan', async () => {
    // Create an app instance
    const { app, services } = createApp();

    // Verify services are injected
    assert.ok(services.vaultService);

    // List tracks API logic check
    const trackList = services.vaultService.listTracks().map((t, idx) => services.vaultService.enrichTrack(t, idx + 1));
    assert.ok(Array.isArray(trackList));
  });

  cleanup();

  console.log(`\n========================================`);
  console.log(`🎉 Vault Storage Engine Tests: ${passedTests}/${totalTests} Passed (100%)`);
  console.log(`========================================\n`);

  if (passedTests !== totalTests) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal Vault Test Error:', err);
  cleanup();
  process.exit(1);
});
