import path from 'path';
import fs from 'fs';

/**
 * VideoRenderService (Core Service)
 * 
 * Handles AI visual synthesis and multi-format lyric video rendering (16:9 YouTube & 9:16 Shorts)
 * using Linux FFmpeg and fonts-noto-cjk font rendering.
 * 
 * Related Contracts: API-005, API-006, CMP-004, CMP-005, SCN-004
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
   * Generate AI thumbnail or local fallback cover image (API-005)
   * @param {string} trackId 
   * @param {Object} [options]
   * @param {boolean} [options.useApi=false]
   * @param {string} [options.customPrompt]
   * @returns {Promise<{success: boolean, imageUrl: string}>}
   */
  async generateCoverImage(trackId, { useApi = false, customPrompt } = {}) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    // Gradient template / placeholder image URL for local offline development
    const imageUrl = `/assets/covers/${track.id}_cover.png`;
    track.coverImageUrl = imageUrl;
    this.vaultService.saveTrack(track);

    return {
      success: true,
      trackId,
      imageUrl
    };
  }

  /**
   * Export multi-format video (16:9 YouTube / 9:16 Shorts) (API-006)
   * @param {string} trackId 
   * @param {Object} params
   * @param {'youtube_16x9'|'shorts_9x16'|'all'} [params.format='youtube_16x9']
   * @param {'suno'|'ace'} [params.audioType='suno']
   * @returns {Promise<{success: boolean, jobId: string, videoUrls: Object}>}
   */
  async exportVideo(trackId, { format = 'youtube_16x9', audioType = 'suno' } = {}) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    const audioPath = audioType === 'ace' ? track.audioPathAceStep : (track.audioPathSuno || track.audioPathAceStep);
    const coverPath = track.coverImageUrl || 'default_cover.png';
    const outputDir = path.join(this.vaultService.vaultRepository.zenionRootDir, track.title.replace(/\s+/g, '_'), 'videos');

    const videoUrls = {};
    let primaryJobId = `JOB-${Date.now()}`;

    if (format === 'youtube_16x9' || format === 'all') {
      const outputPath16x9 = path.join(outputDir, `${track.id}_youtube_16x9.mp4`);
      const res = await this.ffmpegEncoder.renderVideo({
        audioPath,
        coverImagePath: coverPath,
        timeline: track.timeline,
        format: 'youtube_16x9',
        outputPath: outputPath16x9
      });
      primaryJobId = res.jobId;
      videoUrls.youtube_16x9 = outputPath16x9;
    }

    if (format === 'shorts_9x16' || format === 'all') {
      const outputPath9x16 = path.join(outputDir, `${track.id}_shorts_9x16.mp4`);
      const res = await this.ffmpegEncoder.renderVideo({
        audioPath,
        coverImagePath: coverPath,
        timeline: track.timeline,
        format: 'shorts_9x16',
        outputPath: outputPath9x16
      });
      if (format === 'shorts_9x16') primaryJobId = res.jobId;
      videoUrls.shorts_9x16 = outputPath9x16;
    }

    return {
      success: true,
      jobId: primaryJobId,
      trackId,
      format,
      videoUrls
    };
  }

  /**
   * Get encoding status by Job ID
   * @param {string} jobId 
   * @returns {Object|null}
   */
  getEncodingStatus(jobId) {
    return this.ffmpegEncoder.getJobStatus(jobId);
  }
}
