/**
 * ReleaseKitService (Core Service)
 * 
 * Generates platform-tailored SNS Release Kits (YouTube, Instagram Reels, TikTok)
 * containing optimized titles, descriptions, hashtags, and timestamp lyrics for one-click copy and deployment.
 * 
 * Related Contracts: API-007, CMP-006, SCN-005, REQ-003
 */
export class ReleaseKitService {
  /**
   * @param {Object} params
   * @param {import('./VaultStorageService.js').VaultStorageService} params.vaultService
   */
  constructor({ vaultService }) {
    if (!vaultService) {
      throw new Error('VaultStorageService is required for ReleaseKitService.');
    }
    this.vaultService = vaultService;
  }

  /**
   * Format seconds to MM:SS string
   * @param {number} sec 
   * @returns {string}
   */
  _formatTime(sec) {
    const s = Math.max(0, Number(sec) || 0);
    const mins = Math.floor(s / 60);
    const remainingSecs = String(Math.floor(s % 60)).padStart(2, '0');
    return `${mins}:${remainingSecs}`;
  }

  /**
   * Generate and store SNS Release Kit for a track (API-007, SCN-005)
   * 
   * @param {string} trackId 
   * @param {Object} [options]
   * @returns {Object} Release kit object for YouTube, Instagram, and TikTok
   */
  generateReleaseKit(trackId, options = {}) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    const title = options.title || track.title;
    const genre = options.genre || track.genre || 'Pop';
    const bpm = options.bpm || track.bpm || 120;
    const cleanGenre = genre.replace(/[\s/\\-]+/g, '');

    // 1. Build structured timestamp lyrics
    let timestampLyrics = '';
    if (Array.isArray(track.timeline) && track.timeline.length > 0) {
      timestampLyrics = track.timeline
        .map((t) => `[${this._formatTime(t.startSecond)}] ${t.part}`)
        .join('\n');
    } else {
      timestampLyrics = [
        '[0:00] Intro',
        '[0:15] Verse 1',
        '[0:45] Chorus',
        '[1:15] Verse 2',
        '[1:45] Chorus',
        '[2:15] Outro'
      ].join('\n');
    }

    // 2. Build Platform-tailored Release Kits (SCN-005, REQ-003)
    const releaseKit = {
      trackId: track.id,
      title: title,
      generatedAt: new Date().toISOString(),
      youtube: {
        title: `[Official MV] ${title} - AI Music Studio (${genre})`,
        description: [
          `🎵 Title: ${title}`,
          `🎹 Produced with ZENION Music Studio`,
          `🎼 Genre: ${genre} | BPM: ${bpm}`,
          '',
          `✨ About Track:`,
          track.aiReview ? `AI Director Note: ${track.aiReview}` : `AI 기반 고품질 사운드로 제작된 ${genre} 감성의 신곡입니다.`,
          '',
          `⏱️ Timestamps & Lyrics:`,
          timestampLyrics,
          '',
          `#AIMusic #ZENION #${cleanGenre} #NewMusic #OfficialAudio #AIComposer #KPop`
        ].join('\n'),
        tags: [
          'AI Music',
          'ZENION Studio',
          genre,
          cleanGenre,
          'Korean Music',
          'Official MV',
          'AI Producer',
          'Lo-Fi',
          'Pop Music',
          'New Release'
        ],
        timestampLyrics
      },
      instagram: {
        caption: [
          `✨ 신곡 릴리즈: "${title}" ✨`,
          '',
          `${genre} 감성의 새로운 음악을 지금 만나보세요.`,
          `섬세한 멜로디와 가사가 전하는 감동을 릴스로 감상해 보세요!`,
          '',
          `🔗 프로필 링크에서 풀버전 비디오와 고음질 음원을 확인하실 수 있습니다.`,
          '',
          `🎧 Produced by @zenion.studio`
        ].join('\n'),
        hashtags: [
          '#AI음악',
          '#인디뮤직',
          `#${cleanGenre}`,
          '#음스타그램',
          '#신곡추천',
          '#릴스음악',
          '#AI작곡',
          '#ZENION',
          '#플레이리스트'
        ]
      },
      tiktok: {
        caption: `🎶 "${title}" (${genre}) - 이 음악 어떠신가요? 숏폼 배경음악으로 활용하고 댓글로 감상을 남겨주세요! 🔥 #AI음악 #${cleanGenre} #신곡`,
        hashtags: [
          '#AI음악',
          '#틱톡음악',
          '#음원추천',
          '#Shorts',
          '#ZENION',
          '#AI작곡',
          '#신곡추천',
          `#${cleanGenre}`
        ]
      }
    };

    // Update track and persist
    track.setReleaseKit(releaseKit);
    this.vaultService.saveTrack(track);

    return releaseKit;
  }

  /**
   * Get release kit for a track (cached or freshly generated)
   * 
   * @param {string} trackId 
   * @returns {Object|null}
   */
  getReleaseKit(trackId) {
    const track = this.vaultService.getTrack(trackId);
    if (!track) return null;
    return track.releaseKit || this.generateReleaseKit(trackId);
  }

  /**
   * Format complete Release Kit as a GitHub Flavored Markdown document
   * 
   * @param {Object} track 
   * @param {Object} kit 
   * @returns {string} Markdown text
   */
  formatReleaseKitMarkdown(track, kit) {
    const title = track?.title || kit?.title || 'Unknown Track';
    const genre = track?.genre || 'Pop';
    const bpm = track?.bpm || 120;

    return `# Release Kit: ${title}

---
- **Track ID**: \`${track?.id || kit?.trackId || ''}\`
- **Genre**: ${genre}
- **BPM**: ${bpm}
- **Generated At**: ${kit?.generatedAt || new Date().toISOString()}
---

## 1. YouTube Longform Release

### 📌 Video Title
\`\`\`text
${kit.youtube?.title || ''}
\`\`\`

### 📝 Video Description
\`\`\`text
${kit.youtube?.description || ''}
\`\`\`

### 🏷️ YouTube Tags
${(kit.youtube?.tags || []).map((tag) => `\`${tag}\``).join(', ')}

---

## 2. Instagram Reels Release

### 📱 Post Caption
\`\`\`text
${kit.instagram?.caption || ''}
\`\`\`

### #️⃣ Instagram Hashtags
${(kit.instagram?.hashtags || []).join(' ')}

---

## 3. TikTok Shorts Release

### 🎵 Short Caption
\`\`\`text
${kit.tiktok?.caption || ''}
\`\`\`

### #️⃣ TikTok Hashtags
${(kit.tiktok?.hashtags || []).join(' ')}

---
*Generated automatically by ZENION Music Studio Release Hub Engine (SCN-005, API-007)*
`;
  }
}

export default ReleaseKitService;
