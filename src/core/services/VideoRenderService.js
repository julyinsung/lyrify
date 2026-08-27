import path from 'path';
import fs from 'fs';
import zlib from 'zlib';

function makePngChunk(type, data) {
  const len = data.length;
  const chunk = Buffer.alloc(8 + len + 4);
  chunk.writeUInt32BE(len, 0);
  chunk.write(type, 4, 4, 'ascii');
  data.copy(chunk, 8);
  const typeBuf = Buffer.from(type, 'ascii');
  const crc = zlib.crc32(Buffer.concat([typeBuf, data]));
  chunk.writeUInt32BE(crc, 8 + len);
  return chunk;
}

function generateGradientPng(width, height, r1, g1, b1, r2, g2, b2) {
  const header = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData.writeUInt8(8, 8);
  ihdrData.writeUInt8(6, 9);
  ihdrData.writeUInt8(0, 10);
  ihdrData.writeUInt8(0, 11);
  ihdrData.writeUInt8(0, 12);
  const ihdr = makePngChunk('IHDR', ihdrData);

  const rowSize = 1 + width * 4;
  const rawData = Buffer.alloc(rowSize * height);

  for (let y = 0; y < height; y++) {
    const rowOffset = y * rowSize;
    rawData.writeUInt8(0, rowOffset);
    const t = y / height;
    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);

    for (let x = 0; x < width; x++) {
      const pxOffset = rowOffset + 1 + x * 4;
      rawData.writeUInt8(r, pxOffset);
      rawData.writeUInt8(g, pxOffset + 1);
      rawData.writeUInt8(b, pxOffset + 2);
      rawData.writeUInt8(255, pxOffset + 3);
    }
  }

  const compressed = zlib.deflateSync(rawData);
  const idat = makePngChunk('IDAT', compressed);
  const iend = makePngChunk('IEND', Buffer.alloc(0));

  return Buffer.concat([header, ihdr, idat, iend]);
}

/**
 * VideoRenderService (Core Service)
 * 
 * Handles AI visual synthesis (03_visuals/cover.png) and multi-format lyric video rendering
 * (16:9 YouTube longform & 9:16 Shorts/TikTok) into 04_videos/ using Linux FFmpeg.
 * Also manages lyric timeline synchronization (API-008).
 * 
 * Related Contracts: API-005, API-006, API-008, CMP-004, CMP-005, SCN-004, REQ-003
 */
export class VideoRenderService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/FFmpegVideoEncoder.js').FFmpegVideoEncoder} params.ffmpegEncoder
   * @param {import('./VaultStorageService.js').VaultStorageService} params.vaultService
   */
  constructor({ ffmpegEncoder, vaultService }) {
    this.ffmpegEncoder = ffmpegEncoder;
    this.vaultService = vaultService;
  }

  /**
   * Generate AI thumbnail / cover visual and save to 03_visuals/cover.png (API-005, SCN-004, REQ-003)
   * 
   * @param {string} trackId 
   * @param {Object} [options]
   * @param {boolean} [options.useApi=false]
   * @param {string} [options.customPrompt]
   * @returns {Promise<{success: boolean, trackId: string, imageUrl: string, coverPath: string, prompt: string}>}
   */
  async generateCoverVisual(trackId, { useApi = false, customPrompt } = {}) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    // Ensure complete track vault structure
    const vault = this.vaultService.createTrackVault(track);
    const coverPath = path.join(vault.folders.visuals, 'cover.png');
    const svgPath = path.join(vault.folders.visuals, 'cover.svg');

    // Genre-based color gradients
    const genre = (track.genre || 'Pop').toLowerCase();
    let r1 = 30, g1 = 30, b1 = 80, r2 = 220, g2 = 60, b2 = 140;
    if (genre.includes('ballad') || genre.includes('ambient')) {
      r1 = 15; g1 = 32; b1 = 67; r2 = 70; g2 = 130; b2 = 180;
    } else if (genre.includes('city') || genre.includes('disco')) {
      r1 = 40; g1 = 10; b1 = 70; r2 = 255; g2 = 110; b2 = 199;
    } else if (genre.includes('indie') || genre.includes('acoustic')) {
      r1 = 60; g1 = 40; b1 = 20; r2 = 230; g2 = 150; b2 = 60;
    } else if (genre.includes('rock') || genre.includes('metal')) {
      r1 = 20; g1 = 20; b1 = 20; r2 = 180; g2 = 30; b2 = 30;
    }

    // 1. Generate standalone valid PNG cover image
    const pngBuffer = generateGradientPng(1080, 1080, r1, g1, b1, r2, g2, b2);
    fs.writeFileSync(coverPath, pngBuffer);

    // 2. Generate complementary SVG cover image with typography
    const promptText = customPrompt || (`Album cover for ${track.title}, ${track.genre} mood, high quality studio visual`);
    const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="rgb(${r1},${g1},${b1})"/>
<stop offset="100%" stop-color="rgb(${r2},${g2},${b2})"/>
</linearGradient></defs>
<rect width="1080" height="1080" fill="url(#bg)"/>
<text x="540" y="460" font-family="sans-serif" font-size="64" font-weight="bold" fill="#ffffff" text-anchor="middle">${track.title}</text>
<text x="540" y="540" font-family="sans-serif" font-size="32" fill="#e0e0e0" text-anchor="middle">${track.genre || 'AI Music'} • ${track.bpm || 120} BPM</text>
<text x="540" y="880" font-family="sans-serif" font-size="24" font-weight="600" fill="#ffffff" opacity="0.75" letter-spacing="4" text-anchor="middle">ZENION AI MUSIC STUDIO</text>
</svg>`;
    fs.writeFileSync(svgPath, svgContent, 'utf8');

    // Update track cover image path
    track.coverImageUrl = coverPath;
    this.vaultService.saveTrack(track);

    // Update recipe.json and metadata.json
    try {
      fs.writeFileSync(vault.files.recipe, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      fs.writeFileSync(vault.files.metadata, JSON.stringify(track.toJSON(), null, 2), 'utf8');
    } catch (_) {}

    return {
      success: true,
      trackId: track.id,
      imageUrl: coverPath,
      coverPath,
      prompt: promptText
    };
  }

  /**
   * Backwards-compatible alias for generateCoverVisual (API-005)
   * @param {string} trackId 
   * @param {Object} [options]
   * @returns {Promise<Object>}
   */
  async generateCoverImage(trackId, options) {
    return this.generateCoverVisual(trackId, options);
  }

  /**
   * Save lyric timeline timestamps synchronization (API-008, SCN-004)
   * 
   * @param {string} trackId 
   * @param {Array<{part: string, startSecond: number}>} timeline 
   * @returns {Promise<{success: boolean, trackId: string, updatedTimeline: Array<Object>}>}
   */
  async saveLyricTimelineSync(trackId, timeline) {
    if (!Array.isArray(timeline)) {
      throw new Error('Timeline must be an array.');
    }

    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    track.setTimeline(timeline);
    this.vaultService.saveTrack(track);

    // Update vault recipe.json, metadata.json and release_kit.md if folder exists
    const vault = this.vaultService.createTrackVault(track);
    try {
      fs.writeFileSync(vault.files.recipe, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      fs.writeFileSync(vault.files.metadata, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      if (track.releaseKit) {
        this.vaultService.exportReleaseKitFile(trackId, track.releaseKit);
      }
    } catch (_) {}

    return {
      success: true,
      trackId: track.id,
      updatedTimeline: track.timeline
    };
  }

  /**
   * Render multi-format video (16:9 YouTube & 9:16 Shorts) into 04_videos/ (SCN-004, REQ-003, API-006)
   * 
   * @param {string} trackId 
   * @param {Object} [params]
   * @param {'youtube_16x9'|'shorts_9x16'|'all'} [params.format='youtube_16x9']
   * @param {'suno'|'ace'} [params.audioType='suno']
   * @param {boolean} [params.dryRun]
   * @returns {Promise<{success: boolean, jobId: string, trackId: string, format: string, videoUrls: Object}>}
   */
  async renderTrackVideo(trackId, { format = 'youtube_16x9', audioType = 'suno', dryRun } = {}) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    // Ensure complete track vault structure
    const vault = this.vaultService.createTrackVault(track);

    // Resolve audio path
    let audioPath = audioType === 'ace'
      ? (track.audioPathAceStep || path.join(vault.folders.draft, 'draft_audio.wav'))
      : (track.audioPathSuno || track.audioPathAceStep || path.join(vault.folders.finalAudio, 'suno_master.mp3'));

    // Resolve or generate cover image
    let coverPath = track.coverImageUrl || path.join(vault.folders.visuals, 'cover.png');
    if (!fs.existsSync(coverPath)) {
      const coverRes = await this.generateCoverVisual(trackId);
      coverPath = coverRes.coverPath;
    }

    const videoUrls = {};
    let primaryJobId = `JOB-${Date.now()}`;

    // 16:9 YouTube Longform video
    if (format === 'youtube_16x9' || format === 'all') {
      const outputPath16x9 = path.join(vault.folders.videos, `${track.id}_youtube_16x9.mp4`);
      const res16x9 = await this.ffmpegEncoder.renderVideo({
        audioPath,
        coverImagePath: coverPath,
        timeline: track.timeline,
        format: 'youtube_16x9',
        outputPath: outputPath16x9,
        dryRun
      });
      primaryJobId = res16x9.jobId;
      videoUrls.youtube_16x9 = outputPath16x9;
    }

    // 9:16 Shorts/TikTok Shortform video
    if (format === 'shorts_9x16' || format === 'all') {
      const outputPath9x16 = path.join(vault.folders.videos, `${track.id}_shorts_9x16.mp4`);
      const res9x16 = await this.ffmpegEncoder.renderVideo({
        audioPath,
        coverImagePath: coverPath,
        timeline: track.timeline,
        format: 'shorts_9x16',
        outputPath: outputPath9x16,
        dryRun
      });
      if (format === 'shorts_9x16') primaryJobId = res9x16.jobId;
      videoUrls.shorts_9x16 = outputPath9x16;
    }

    // Update track status to released
    track.status = 'released';
    this.vaultService.saveTrack(track);

    try {
      fs.writeFileSync(vault.files.recipe, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      fs.writeFileSync(vault.files.metadata, JSON.stringify(track.toJSON(), null, 2), 'utf8');
    } catch (_) {}

    return {
      success: true,
      jobId: primaryJobId,
      trackId,
      format,
      videoUrls
    };
  }

  /**
   * Backwards-compatible alias for renderTrackVideo (API-006)
   * @param {string} trackId 
   * @param {Object} [params]
   * @returns {Promise<Object>}
   */
  async exportVideo(trackId, params) {
    return this.renderTrackVideo(trackId, params);
  }

  /**
   * Get encoding status by Job ID (GAP-001)
   * @param {string} jobId 
   * @returns {Object|null}
   */
  getEncodingStatus(jobId) {
    return this.ffmpegEncoder.getJobStatus(jobId);
  }
}
