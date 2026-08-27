/**
 * ReleaseKitService (Core Service)
 * 
 * Generates platform-tailored SNS Release Kits (YouTube, Instagram Reels, TikTok)
 * containing optimized titles, descriptions, hashtags, and timestamp lyrics for one-click copy.
 * 
 * Related Contracts: API-007, CMP-006, SCN-005
 */
export class ReleaseKitService {
  /**
   * @param {Object} params
   * @param {import('./VaultStorageService.js').VaultStorageService} params.vaultService
   */
  constructor({ vaultService }) {
    this.vaultService = vaultService;
  }

  /**
   * Generate and store SNS Release Kit for a track (API-007)
   * @param {string} trackId 
   * @returns {Object} Release kit object
   */
  generateReleaseKit(trackId) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    const title = track.title;
    const genre = track.genre || 'Pop';
    const bpm = track.bpm || 120;

    // Build timestamp lyrics if timeline available
    let timestampLyrics = '';
    if (track.timeline && track.timeline.length > 0) {
      timestampLyrics = track.timeline
        .map((t) => {
          const mins = Math.floor(t.startSecond / 60);
          const secs = String(Math.floor(t.startSecond % 60)).padStart(2, '0');
          return `[${mins}:${secs}] ${t.part}`;
        })
        .join('\n');
    } else {
      timestampLyrics = `[0:00] Intro\n[0:15] Verse 1\n[0:45] Chorus\n[1:15] Verse 2\n[1:45] Chorus\n[2:15] Outro`;
    }

    const releaseKit = {
      youtube: {
        title: `[Official MV] ${title} - AI Music Studio (${genre})`,
        description: `🎵 ${title}\n\nProduced with ZENION Music Studio\nGenre: ${genre} | BPM: ${bpm}\n\n⏱️ Timestamps & Lyrics:\n${timestampLyrics}\n\n#AIMusic #ZENION #${genre.replace(/\s+/g, '')} #NewMusic`,
        tags: ['AI Music', 'ZENION Studio', genre, 'Korean Music', 'Lo-Fi', 'Pop'],
        timestampLyrics
      },
      instagram: {
        caption: `✨ 신곡 발매: "${title}" ✨\n\n${genre} 감성의 새로운 음악을 지금 감상해보세요. 프로필 링크에서 풀버전 확인 가능!\n\n🎧 Produced by @zenion.studio`,
        hashtags: ['#AI음악', '#인디뮤직', `#${genre.replace(/\s+/g, '')}`, '#음스타그램', '#신곡추천', '#릴스음악']
      },
      tiktok: {
        caption: `🎶 ${title} - 이 노래 어떤가요? 댓글로 피드백 남겨주세요! #AI음악 #${genre.replace(/\s+/g, '')}`,
        hashtags: ['#AI음악', '#틱톡음악', '#음원추천', '#Shorts', '#ZENION']
      }
    };

    track.setReleaseKit(releaseKit);
    this.vaultService.saveTrack(track);

    return releaseKit;
  }

  /**
   * Get release kit for a track
   * @param {string} trackId 
   * @returns {Object|null}
   */
  getReleaseKit(trackId) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) return null;
    return track.releaseKit || this.generateReleaseKit(trackId);
  }
}
