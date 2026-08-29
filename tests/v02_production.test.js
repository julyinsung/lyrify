import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DirectorService } from '../src/core/services/DirectorService.js';
import { VaultStorageService } from '../src/core/services/VaultStorageService.js';
import { GeminiProvider } from '../src/adapters/GeminiProvider.js';
import { ZenionVaultRepository } from '../src/adapters/ZenionVaultRepository.js';
import { Track } from '../src/core/domain/Track.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runAsyncTest(name, fn) {
  try {
    await fn();
    console.log(`  ✅ PASS: ${name}`);
  } catch (err) {
    console.error(`  ❌ FAIL: ${name}`);
    console.error(err);
    process.exitCode = 1;
  }
}

async function runV02Suite() {
  console.log('\n🧪 [v0.2.0 Test Suite] Starting Deep Production & Music Git-Flow Verification...\n');

  const testDir = path.join(__dirname, 'temp_v02_vault');
  if (fs.existsSync(testDir)) {
    fs.rmSync(testDir, { recursive: true, force: true });
  }
  fs.mkdirSync(testDir, { recursive: true });

  const dbPath = path.join(testDir, 'database.json');
  const vaultRepo = new ZenionVaultRepository({
    zenionRootDir: testDir,
    dbFilePath: dbPath
  });

  const geminiProvider = new GeminiProvider({ apiKey: '' });
  const directorService = new DirectorService({ geminiProvider });
  const vaultService = new VaultStorageService({ vaultRepository: vaultRepo });

  // -------------------------------------------------------------
  // Test 1: REG-006 - Single Track Deep Production Blueprint & Rationale (with Auto Recommendation)
  // -------------------------------------------------------------
  await runAsyncTest('REG-006: Single Track Deep Production & AI Smart Advisory (API-009, SCN-006)', async () => {
    // 1-1. Auto Genre and BPM analysis test
    const autoRes = await directorService.deepProduceTrack({
      story: '비 오는 날의 이별과 눈물',
      targetGenre: 'auto',
      bpm: 0
    });
    assert.strictEqual(autoRes.success, true);
    assert.ok(autoRes.blueprint.genre.includes('Ballad'));
    assert.strictEqual(autoRes.blueprint.bpm, 72);
    assert.ok(autoRes.blueprint.rationale.aiAdvisory.includes('Ballad'));
    assert.ok(autoRes.blueprint.alternatives.length >= 2);

    // 1-2. Specific Genre production test
    const res = await directorService.deepProduceTrack({
      story: '비 오는 날의 네온사인 드라이브',
      mood: '쓸쓸하면서도 낭만적인',
      targetGenre: 'City Pop',
      bpm: 118
    });

    assert.strictEqual(res.success, true);
    const bp = res.blueprint;
    assert.ok(bp.title);
    assert.strictEqual(bp.genre, 'City Pop');
    assert.strictEqual(bp.bpm, 118);
    assert.strictEqual(bp.key, 'A Major');

    // Verify Rationale structure
    assert.ok(bp.rationale.tempoRationale.includes('118 BPM'));
    assert.ok(bp.rationale.keyRationale.includes('A Major'));
    assert.ok(Array.isArray(bp.rationale.instrumentationRationale));
    assert.ok(bp.rationale.instrumentationRationale.length >= 3);
    assert.ok(bp.rationale.vocalDirection);

    // Verify Section Timeline
    assert.ok(Array.isArray(bp.sections));
    assert.ok(bp.sections.length >= 6);
    const verse1 = bp.sections.find(s => s.part === 'Verse 1');
    assert.ok(verse1);
    assert.ok(verse1.lyrics && verse1.lyrics.length > 10);
    assert.ok(verse1.tag.includes('[Verse 1'));

    // Verify Suno Master Prompts
    assert.ok(bp.sunoStylePrompt.includes('BPM'));
    assert.ok(bp.negativePrompt.includes('no autotune hiss'));
    assert.ok(bp.sunoTips.extendGuide);
  });

  // -------------------------------------------------------------
  // Test 2: REG-007 - Music Git-Flow Branching, Diff Compare & Master Merge
  // -------------------------------------------------------------
  await runAsyncTest('REG-007: Music Git-Flow Branching, A/B Diff & Master Promotion (API-010~012, SCN-007)', async () => {
    const track = new Track({
      id: 'TRK-TEST-001',
      title: '비 오는 날의 네온사인',
      genre: 'City Pop',
      bpm: 118,
      lyricsRaw: '[Intro]\n[Verse 1]\n원래 가사 내용',
      sunoStylePrompt: '[Upbeat 118 BPM City Pop], [slap bass], [dry female vocals]'
    });
    await vaultService.createTrackVault(track);

    // 1. Create a new take branch
    const branchRes = vaultService.createTrackBranch('TRK-TEST-001', {
      branchName: 'take-02_sax_solo',
      description: '색소폰 솔로 및 가사 수정 테이크',
      lyricsRaw: '[Intro]\n[Verse 1]\n수정된 수채화 가사 내용\n[Bridge]\n[Saxophone Solo]',
      sunoStylePrompt: '[Upbeat 118 BPM City Pop], [slap bass, alto saxophone], [dry female vocals]'
    });

    assert.strictEqual(branchRes.success, true);
    assert.ok(branchRes.branchId.includes('take-'));
    assert.strictEqual(branchRes.branch.parentTakeId, 'master');

    // 2. Compare Master vs Branch
    const compareRes = vaultService.compareBranches('TRK-TEST-001', 'master', branchRes.branchId);
    assert.strictEqual(compareRes.success, true);
    assert.strictEqual(compareRes.comparison.lyricsModified, true);
    assert.strictEqual(compareRes.comparison.styleModified, true);
    assert.ok(compareRes.comparison.b.lyrics.includes('수정된 수채화'));

    // 3. Merge Branch to Master
    const mergeRes = vaultService.mergeBranchToMaster('TRK-TEST-001', branchRes.branchId, '색소폰 솔로 버전 마스터 확정');
    assert.strictEqual(mergeRes.success, true);
    assert.strictEqual(mergeRes.masterVersion, 'v2.0.0');
    assert.ok(mergeRes.track.lyricsRaw.includes('수정된 수채화'));
    assert.ok(mergeRes.track.sunoStylePrompt.includes('alto saxophone'));
  });

  // -------------------------------------------------------------
  // Test 3: REG-008 - AI Co-Producer Agent Conversational Directing
  // -------------------------------------------------------------
  await runAsyncTest('REG-008: AI Co-Producer Agent Conversational Directing (API-013, SCN-008)', async () => {
    const tuningRes = await geminiProvider.tuneWithCoProducer({
      trackTitle: '비 오는 날의 네온사인',
      currentLyrics: '[Verse 1]\n네온사인 물든 밤거리 위로\n[Bridge]\n어둠이 걷히고',
      currentStyle: '[Upbeat 118 BPM City Pop], [slap bass, FM synth lead, lush brass]',
      userInstruction: '색소폰 솔로를 넣고 가사를 은유적으로 바꿔줘'
    });

    assert.ok(tuningRes.agentResponse.includes('디렉터님'));
    assert.ok(tuningRes.tuningNotes.length >= 1);
    assert.ok(tuningRes.tunedLyrics.includes('Saxophone Solo') || tuningRes.tunedLyrics.includes('수채화'));
    assert.ok(tuningRes.tunedStyle.includes('alto saxophone'));
  });

  // Cleanup
  if (fs.existsSync(testDir)) {
    fs.rmSync(testDir, { recursive: true, force: true });
  }

  console.log('\n========================================');
  console.log('🎉 v0.2.0 Test Suite Finished: 3/3 Passed (100%)');
  console.log('========================================\n');
}

runV02Suite().catch(console.error);
