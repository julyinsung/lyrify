import { Track } from '../domain/Track.js';

/**
 * QualityJudgeService (Core Service)
 * 
 * Performs 1st-stage AI Quality Screening on ACE-Step drafts:
 * - Checks audio waveforms for technical defects (peak clipping, silence, duration) via FFmpeg
 * - Evaluates lyrics completeness ([Verse 1]/[Chorus] structure, length balance, emotion keywords)
 * - Computes a 100-point AI score, grade (S/A/B/C/F), and comprehensive AI review
 * - Calculates TOP 3 recommended tracks ranking
 * 
 * Related Contracts: API-003, CMP-002, SCN-002, REQ-001
 */
export class QualityJudgeService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/FFmpegVideoEncoder.js').FFmpegVideoEncoder} params.ffmpegEncoder
   * @param {import('../../adapters/GeminiProvider.js').GeminiProvider} params.geminiProvider
   * @param {import('./VaultStorageService.js').VaultStorageService} params.vaultService
   */
  constructor({ ffmpegEncoder, geminiProvider, vaultService }) {
    if (!ffmpegEncoder || !geminiProvider) {
      throw new Error('FFmpegVideoEncoder and GeminiProvider are required for QualityJudgeService.');
    }
    this.ffmpegEncoder = ffmpegEncoder;
    this.geminiProvider = geminiProvider;
    this.vaultService = vaultService;
  }

  /**
   * Evaluate track audio and lyrics quality (API-003, SCN-002)
   * 
   * @param {string} trackId 
   * @param {Object} [params]
   * @param {string} [params.audioPath]
   * @param {string} [params.lyrics]
   * @returns {Promise<{success: boolean, trackId: string, aiScore: number, aiReview: string, grade: string, techCheck: {clipping: boolean, silence: boolean}}>}
   */
  async evaluateTrack(trackId, { audioPath, lyrics } = {}) {
    const track = this.vaultService?.getTrack(trackId);
    const targetAudio = audioPath || track?.audioPathAceStep || '';
    const targetLyrics = lyrics || track?.lyricsRaw || '';

    // 1. Technical Audio Defect Analysis via FFmpeg adapter
    const techCheck = await this.ffmpegEncoder.analyzeAudioTech(targetAudio);

    // 2. AI Quality & Lyrics Scoring via Gemini Provider
    const evalResult = await this.geminiProvider.evaluateQuality({
      lyrics: targetLyrics,
      audioMetadata: techCheck
    });

    // 3. Update track entity in vault storage if available
    if (track) {
      track.updateEvaluation(evalResult.aiScore, evalResult.aiReview, {
        clipping: Boolean(techCheck.clipping),
        silence: Boolean(techCheck.silence)
      });
      this.vaultService.saveTrack(track);
    }

    return {
      success: true,
      trackId,
      aiScore: evalResult.aiScore,
      aiReview: evalResult.aiReview,
      grade: evalResult.grade || (evalResult.aiScore >= 90 ? 'S' : evalResult.aiScore >= 80 ? 'A' : evalResult.aiScore >= 70 ? 'B' : evalResult.aiScore >= 60 ? 'C' : 'F'),
      techCheck: {
        clipping: Boolean(techCheck.clipping),
        silence: Boolean(techCheck.silence)
      }
    };
  }

  /**
   * Rank tracks by AI score and assign TOP recommendation badges
   * 
   * @param {Array<Track|Object>} tracks 
   * @returns {Array<Track|Object>} Ranked tracks with ranking, isTopRecommended, and recommendationBadge
   */
  rankTracks(tracks = []) {
    if (!Array.isArray(tracks)) return [];

    const sorted = [...tracks].sort((a, b) => {
      const scoreA = Number(a.aiScore) || 0;
      const scoreB = Number(b.aiScore) || 0;
      return scoreB - scoreA;
    });

    return sorted.map((item, index) => {
      const ranking = index + 1;
      const score = Number(item.aiScore) || 0;
      const isTopRecommended = ranking <= 3 && score >= 60;
      let recommendationBadge = null;

      if (ranking === 1 && score >= 60) {
        recommendationBadge = 'TOP 1 PICK';
      } else if (ranking === 2 && score >= 60) {
        recommendationBadge = 'TOP 2';
      } else if (ranking === 3 && score >= 60) {
        recommendationBadge = 'TOP 3';
      }

      // If it's a domain Track instance or plain object, attach ranking metadata
      if (typeof item.toJSON === 'function') {
        const obj = item.toJSON();
        obj.ranking = ranking;
        obj.isTopRecommended = isTopRecommended;
        obj.recommendationBadge = recommendationBadge;
        return obj;
      }

      return {
        ...item,
        ranking,
        isTopRecommended,
        recommendationBadge
      };
    });
  }

  /**
   * Get TOP N recommended tracks (Default TOP 3)
   * 
   * @param {Array<Track|Object>} tracks 
   * @param {number} [topN=3] 
   * @returns {Array<Track|Object>}
   */
  getTopRecommendations(tracks = [], topN = 3) {
    const ranked = this.rankTracks(tracks);
    return ranked.slice(0, Math.max(1, topN));
  }
}

export default QualityJudgeService;
