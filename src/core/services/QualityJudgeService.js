import { Track } from '../domain/Track.js';

/**
 * QualityJudgeService (Core Service)
 * 
 * Performs 1st-stage AI Quality Screening on ACE-Step drafts:
 * checks audio waveforms for technical defects (clipping, silence) via FFmpeg and
 * evaluates lyrics completeness to generate a 100-point AI score & review.
 * 
 * Related Contracts: API-003, CMP-002, SCN-002
 */
export class QualityJudgeService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/FFmpegVideoEncoder.js').FFmpegVideoEncoder} params.ffmpegEncoder
   * @param {import('../../adapters/GeminiProvider.js').GeminiProvider} params.geminiProvider
   * @param {import('./VaultStorageService.js').VaultStorageService} params.vaultService
   */
  constructor({ ffmpegEncoder, geminiProvider, vaultService }) {
    this.ffmpegEncoder = ffmpegEncoder;
    this.geminiProvider = geminiProvider;
    this.vaultService = vaultService;
  }

  /**
   * Evaluate track audio and lyrics quality (API-003)
   * @param {string} trackId 
   * @param {Object} params
   * @param {string} [params.audioPath]
   * @param {string} [params.lyrics]
   * @returns {Promise<{success: boolean, aiScore: number, aiReview: string, techCheck: Object}>}
   */
  async evaluateTrack(trackId, { audioPath, lyrics } = {}) {
    const track = this.vaultService.getTrack(trackId);
    const targetAudio = audioPath || track?.audioPathAceStep || '';
    const targetLyrics = lyrics || track?.lyricsRaw || '';

    // 1. Technical Audio Check
    const techCheck = await this.ffmpegEncoder.analyzeAudioTech(targetAudio);

    // 2. AI Quality & Lyrics Scoring
    const evalResult = await this.geminiProvider.evaluateQuality({
      lyrics: targetLyrics,
      audioMetadata: techCheck
    });

    if (track) {
      track.updateEvaluation(evalResult.aiScore, evalResult.aiReview, {
        clipping: techCheck.clipping,
        silence: techCheck.silence
      });
      this.vaultService.saveTrack(track);
    }

    return {
      success: true,
      trackId,
      aiScore: evalResult.aiScore,
      aiReview: evalResult.aiReview,
      techCheck: {
        clipping: techCheck.clipping,
        silence: techCheck.silence
      }
    };
  }

  /**
   * Rank tracks by AI score
   * @param {Array<Track>} tracks 
   * @returns {Array<Track>}
   */
  rankTracks(tracks) {
    return [...tracks].sort((a, b) => b.aiScore - a.aiScore);
  }
}
