import fs from 'fs';
import path from 'path';
import { Track } from '../domain/Track.js';

/**
 * VaultStorageService (Core Service)
 * 
 * Manages ZENION-MUSIC master vault asset organization:
 * - SCN-003, REQ-002: Complete package folder structure (recipe.json, 01_draft/, 02_final_audio/, 03_visuals/, 04_videos/, release_kit.md)
 * - syncVault(rootDir): Real-time file system scan & synchronization with database.json
 * - mapSunoAudio(trackId, sourceAudioPath, title): Suno audio mapping, structured storage in 02_final_audio/, status update
 * - exportReleaseKitFile(trackId, releaseKit): Automatic markdown export of SNS release kit
 * 
 * Related Contracts: API-002, API-004, DATA-001, DATA-002, SCN-003, REQ-002
 */
export class VaultStorageService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/ZenionVaultRepository.js').ZenionVaultRepository} params.vaultRepository
   */
  constructor({ vaultRepository }) {
    this.vaultRepository = vaultRepository;
  }

  /**
   * List all tracks sorted by ranking/AI score
   * @returns {Array<Track>}
   */
  listTracks() {
    const rawList = this.vaultRepository.loadAll();
    return rawList
      .map((data) => new Track(data))
      .sort((a, b) => b.aiScore - a.aiScore);
  }

  /**
   * Get track by ID
   * @param {string} id 
   * @returns {Track|null}
   */
  getTrack(id) {
    const data = this.vaultRepository.findById(id);
    return data ? new Track(data) : null;
  }

  /**
   * Save or update a track
   * @param {Track} track 
   * @returns {Track}
   */
  saveTrack(track) {
    this.vaultRepository.save(track.toJSON());
    return track;
  }

  /**
   * Delete a track by ID
   * @param {string} id 
   * @returns {boolean}
   */
  deleteTrack(id) {
    return this.vaultRepository.delete(id);
  }

  /**
   * Create complete package folder structure for a track in ZENION-MUSIC (SCN-003, REQ-002)
   * Structure:
   * - <trackFolder>/
   *   - recipe.json
   *   - metadata.json (compatibility alias)
   *   - 01_draft/
   *   - 02_final_audio/
   *   - 03_visuals/
   *   - 04_videos/
   *   - release_kit.md (when available)
   * 
   * @param {Track|Object|string} trackInput 
   * @param {Object} [options]
   * @param {string} [options.folderName]
   * @param {boolean} [options.initReleaseKit=false]
   * @returns {{success: boolean, trackId: string, folderPath: string, folders: Object, files: Object}}
   */
  createTrackVault(trackInput, options = {}) {
    let track;
    if (typeof trackInput === 'string') {
      track = this.getTrack(trackInput);
      if (!track) throw new Error(`Track with ID ${trackInput} not found.`);
    } else if (trackInput instanceof Track) {
      track = trackInput;
    } else if (typeof trackInput === 'object') {
      track = new Track(trackInput);
    } else {
      throw new Error('Invalid trackInput provided to createTrackVault');
    }

    const sanitizedTitle = track.title.replace(/[<>:"/\\|?*]/g, '_').trim();
    const folderName = options.folderName || `${sanitizedTitle}_${track.id}`;

    // createTrackFolder ensures directory and 4 subdirectories exist safely
    const folderPath = this.vaultRepository.createTrackFolder(folderName);

    const folders = {
      draft: path.join(folderPath, '01_draft'),
      finalAudio: path.join(folderPath, '02_final_audio'),
      visuals: path.join(folderPath, '03_visuals'),
      videos: path.join(folderPath, '04_videos')
    };

    const files = {
      recipe: path.join(folderPath, 'recipe.json'),
      metadata: path.join(folderPath, 'metadata.json'),
      releaseKit: path.join(folderPath, 'release_kit.md')
    };

    // Write recipe.json and metadata.json
    const trackJson = track.toJSON();
    fs.writeFileSync(files.recipe, JSON.stringify(trackJson, null, 2), 'utf8');
    fs.writeFileSync(files.metadata, JSON.stringify(trackJson, null, 2), 'utf8');

    // If release kit exists, write release_kit.md
    if (track.releaseKit || options.initReleaseKit) {
      const kit = track.releaseKit || this._generateDefaultReleaseKit(track);
      const markdown = this._formatReleaseKitMarkdown(track, kit);
      fs.writeFileSync(files.releaseKit, markdown, 'utf8');
    }

    // Persist track entity to database.json
    try {
      this.vaultRepository.saveTrack(track);
    } catch (dbErr) {
      console.warn('[VaultStorageService saveTrack Warning]', dbErr.message);
    }

    return {
      success: true,
      trackId: track.id,
      folderPath,
      folders,
      files
    };
  }

  /**
   * Map commercial Suno AI audio file and structure ZENION-MUSIC asset folder (SCN-003, REQ-002, API-004)
   * 
   * @param {string} trackId 
   * @param {string|Object} sourceAudioPathOrOptions 
   * @param {string} [title]
   * @returns {Promise<{success: boolean, track: Object, zenionTrackPath: string, destAudioPath: string, mappedFiles: Object}>}
   */
  async mapSunoAudio(trackId, sourceAudioPathOrOptions, title) {
    let track = this.getTrack(trackId);

    // Extract options
    let sourcePath = '';
    let targetFolder = '';
    let trackTitle = title || '';

    if (typeof sourceAudioPathOrOptions === 'string') {
      sourcePath = sourceAudioPathOrOptions;
    } else if (typeof sourceAudioPathOrOptions === 'object' && sourceAudioPathOrOptions !== null) {
      sourcePath = sourceAudioPathOrOptions.sourceAudioPath || sourceAudioPathOrOptions.sunoAudioPath || '';
      targetFolder = sourceAudioPathOrOptions.targetFolder || '';
      if (!trackTitle && sourceAudioPathOrOptions.title) {
        trackTitle = sourceAudioPathOrOptions.title;
      }
    }

    if (!track) {
      if (trackTitle) {
        track = new Track({ id: trackId, title: trackTitle });
      } else {
        throw new Error(`Track with ID ${trackId} not found.`);
      }
    }

    // Ensure complete track vault structure
    const vault = this.createTrackVault(track, { folderName: targetFolder });

    // Destination path inside 02_final_audio/
    let fileName = 'suno_master.mp3';
    if (sourcePath) {
      fileName = path.basename(sourcePath);
    }
    const destPath = path.join(vault.folders.finalAudio, fileName);

    // If source file exists on disk, copy it into 02_final_audio/
    if (sourcePath && fs.existsSync(sourcePath)) {
      try {
        fs.copyFileSync(sourcePath, destPath);
      } catch (copyErr) {
        console.warn(`[VaultStorageService] Warning copying suno audio: ${copyErr.message}`);
      }
    }

    // Update track entity
    track.mapSunoAudio(destPath);
    this.saveTrack(track);

    // Update recipe.json and metadata.json in master folder
    fs.writeFileSync(vault.files.recipe, JSON.stringify(track.toJSON(), null, 2), 'utf8');
    fs.writeFileSync(vault.files.metadata, JSON.stringify(track.toJSON(), null, 2), 'utf8');

    return {
      success: true,
      track: track.toJSON(),
      zenionTrackPath: vault.folderPath,
      destAudioPath: destPath,
      mappedFiles: {
        sunoAudio: destPath,
        aceAudio: track.audioPathAceStep,
        coverImage: track.coverImageUrl,
        recipe: vault.files.recipe,
        metadata: vault.files.metadata,
        draftDir: vault.folders.draft,
        finalAudioDir: vault.folders.finalAudio,
        visualsDir: vault.folders.visuals,
        videosDir: vault.folders.videos,
        releaseKitFile: vault.files.releaseKit
      }
    };
  }

  /**
   * Backwards-compatible alias for mapSunoAudio
   * @param {string} trackId 
   * @param {Object} options 
   * @returns {Promise<Object>}
   */
  async mapSunoTrack(trackId, options) {
    return this.mapSunoAudio(trackId, options);
  }

  /**
   * Attach ACE-Step 1.5 draft audio to track (01_draft/draft.mp3)
   * @param {string} trackId 
   * @param {string} sourceAudioPath 
   * @returns {Promise<{success: boolean, track: Object, destPath: string}>}
   */
  async attachAceDraft(trackId, sourceAudioPath) {
    const track = this.getTrack(trackId);
    if (!track) throw new Error(`Track with ID ${trackId} not found.`);

    const vault = this.createTrackVault(track);
    const ext = path.extname(sourceAudioPath) || '.mp3';
    const destPath = path.join(vault.folders.draft, `draft${ext}`);

    if (fs.existsSync(sourceAudioPath)) {
      fs.copyFileSync(sourceAudioPath, destPath);
    }

    track.audioPathAceStep = destPath;
    track.status = 'draft_ready';
    this.saveTrack(track);

    return {
      success: true,
      track: track.toJSON(),
      destPath
    };
  }

  /**
   * Export SNS release kit markdown to release_kit.md in track master vault folder (API-007, SCN-005)
   * 
   * @param {string} trackId 
   * @param {Object} [releaseKit]
   * @returns {{success: boolean, filePath: string, releaseKit: Object, track: Object}}
   */
  exportReleaseKitFile(trackId, releaseKit) {
    const track = this.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    const kit = releaseKit || track.releaseKit || this._generateDefaultReleaseKit(track);
    track.setReleaseKit(kit);
    this.saveTrack(track);

    // Ensure track vault folder exists
    const vault = this.createTrackVault(track);

    // Format and write release_kit.md
    const markdown = this._formatReleaseKitMarkdown(track, kit);
    fs.writeFileSync(vault.files.releaseKit, markdown, 'utf8');

    return {
      success: true,
      filePath: vault.files.releaseKit,
      releaseKit: kit,
      track: track.toJSON()
    };
  }

  /**
   * Scan actual file system and synchronize track metadata with database.json
   * 
   * @param {string} [rootDir] 
   * @returns {{success: boolean, syncedCount: number, tracks: Array<Object>}}
   */
  syncVault(rootDir) {
    const targetDir = path.resolve(rootDir || this.vaultRepository.zenionRootDir);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
      return { success: true, syncedCount: 0, tracks: [] };
    }

    const entries = fs.readdirSync(targetDir, { withFileTypes: true });
    const audioExtensions = new Set(['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']);
    const imageExtensions = new Set(['.png', '.jpg', '.jpeg', '.webp', '.svg']);
    const videoExtensions = new Set(['.mp4', '.mov', '.mkv', '.webm']);

    const existingTracks = this.vaultRepository.loadAll();
    const trackMap = new Map(existingTracks.map((t) => [t.id, t]));
    const syncedTracks = [];

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name.startsWith('.')) continue; // ignore hidden folders

      const folderPath = path.join(targetDir, entry.name);
      const recipePath = path.join(folderPath, 'recipe.json');
      const metadataPath = path.join(folderPath, 'metadata.json');
      const releaseKitPath = path.join(folderPath, 'release_kit.md');

      let trackData = null;

      // Check recipe.json or metadata.json
      if (fs.existsSync(recipePath)) {
        try {
          trackData = JSON.parse(fs.readFileSync(recipePath, 'utf8'));
        } catch (_) {}
      } else if (fs.existsSync(metadataPath)) {
        try {
          trackData = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
        } catch (_) {}
      }

      // Infer if no JSON metadata found
      if (!trackData || !trackData.id) {
        // Example folder: "Song_Title_TRK-001" or "TRK-001" or "My Song"
        const parts = entry.name.split('_');
        let inferredId = '';
        let inferredTitle = entry.name;

        for (const part of parts) {
          if (part.startsWith('TRK-')) {
            inferredId = part;
            break;
          }
        }
        if (!inferredId) {
          inferredId = `TRK-${entry.name.replace(/[^a-zA-Z0-9]/g, '-').slice(0, 16)}-${Date.now().toString().slice(-4)}`;
        }
        if (parts.length > 1 && parts[parts.length - 1] === inferredId) {
          inferredTitle = parts.slice(0, -1).join(' ');
        }

        trackData = {
          id: inferredId,
          title: inferredTitle,
          status: 'draft'
        };
      }

      const track = new Track({ ...trackData, ...(trackMap.get(trackData.id) || {}) });

      // Scan subdirectories
      const draftDir = path.join(folderPath, '01_draft');
      const finalDir = path.join(folderPath, '02_final_audio');
      const visualsDir = path.join(folderPath, '03_visuals');
      const videosDir = path.join(folderPath, '04_videos');

      // 1. Scan 01_draft
      if (fs.existsSync(draftDir)) {
        const draftFiles = fs.readdirSync(draftDir);
        const draftAudio = draftFiles.find((f) => audioExtensions.has(path.extname(f).toLowerCase()));
        if (draftAudio) {
          track.audioPathAceStep = path.join(draftDir, draftAudio);
        }
      }

      // 2. Scan 02_final_audio
      if (fs.existsSync(finalDir)) {
        const finalFiles = fs.readdirSync(finalDir);
        const finalAudio = finalFiles.find((f) => audioExtensions.has(path.extname(f).toLowerCase()));
        if (finalAudio) {
          track.audioPathSuno = path.join(finalDir, finalAudio);
          if (track.status === 'draft') track.status = 'mapped';
        }
      }

      // 3. Scan 03_visuals
      if (fs.existsSync(visualsDir)) {
        const visualFiles = fs.readdirSync(visualsDir);
        const coverImg = visualFiles.find((f) => imageExtensions.has(path.extname(f).toLowerCase()));
        if (coverImg) {
          track.coverImageUrl = path.join(visualsDir, coverImg);
        }
      }

      // 4. Scan 04_videos
      let hasVideos = false;
      if (fs.existsSync(videosDir)) {
        const videoFiles = fs.readdirSync(videosDir);
        hasVideos = videoFiles.some((f) => videoExtensions.has(path.extname(f).toLowerCase()));
      }

      // 5. Scan release_kit.md
      if (fs.existsSync(releaseKitPath)) {
        if (!track.releaseKit) {
          track.releaseKit = this._generateDefaultReleaseKit(track);
        }
        if (hasVideos) {
          track.status = 'released';
        }
      }

      // Save to database.json & write back recipe.json
      this.saveTrack(track);

      try {
        fs.writeFileSync(recipePath, JSON.stringify(track.toJSON(), null, 2), 'utf8');
        fs.writeFileSync(metadataPath, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      } catch (_) {}

      syncedTracks.push(track);
    }

    // Sort by AI score
    syncedTracks.sort((a, b) => b.aiScore - a.aiScore);

    return {
      success: true,
      syncedCount: syncedTracks.length,
      tracks: syncedTracks.map((t, idx) => this.enrichTrack(t, idx + 1))
    };
  }

  /**
   * Update track metadata, lyrics and style prompt
   * @param {string} trackId 
   * @param {Object} updates 
   * @returns {Track}
   */
  updateTrackMetadata(trackId, updates = {}) {
    const track = this.getTrack(trackId);
    if (!track) {
      throw new Error(`트랙을 찾을 수 없습니다: ${trackId}`);
    }

    if (updates.title) track.title = updates.title;
    if (updates.genre) track.genre = updates.genre;
    if (updates.bpm) track.bpm = Number(updates.bpm) || track.bpm;
    if (updates.lyricsRaw !== undefined) track.lyricsRaw = updates.lyricsRaw;
    if (updates.lyrics !== undefined && !updates.lyricsRaw) track.lyricsRaw = typeof updates.lyrics === 'string' ? updates.lyrics : JSON.stringify(updates.lyrics);
    if (updates.sunoStylePrompt) track.sunoStylePrompt = updates.sunoStylePrompt;
    if (updates.aiReview) track.aiReview = updates.aiReview;

    this.saveTrack(track);

    // Sync back to recipe.json
    try {
      const sanitized = track.title.replace(/[<>:"/\\|?*]/g, '_').trim();
      const folderPath = path.join(this.vaultRepository.zenionRootDir, `${sanitized}_${track.id}`);
      if (fs.existsSync(folderPath)) {
        const recipePath = path.join(folderPath, 'recipe.json');
        const metadataPath = path.join(folderPath, 'metadata.json');
        fs.writeFileSync(recipePath, JSON.stringify(track.toJSON(), null, 2), 'utf8');
        fs.writeFileSync(metadataPath, JSON.stringify(track.toJSON(), null, 2), 'utf8');
      }
    } catch (_) {}

    return track;
  }

  /**
   * Determine asset completion status for a track
   * @param {Track|string} trackOrId 
   * @returns {{hasDraft: boolean, hasFinalAudio: boolean, hasCover: boolean, hasVideo: boolean, hasReleaseKit: boolean, isComplete: boolean}}
   */
  getTrackAssetStatus(trackOrId) {
    let track = trackOrId;
    if (typeof trackOrId === 'string') {
      track = this.getTrack(trackOrId);
    }
    if (!track) {
      return { hasDraft: false, hasFinalAudio: false, hasCover: false, hasVideo: false, hasReleaseKit: false, isComplete: false };
    }

    const hasDraft = Boolean(track.audioPathAceStep && (fs.existsSync(track.audioPathAceStep) || track.audioPathAceStep.length > 0));
    const hasFinalAudio = Boolean(track.audioPathSuno && (fs.existsSync(track.audioPathSuno) || track.audioPathSuno.length > 0));
    const hasCover = Boolean(track.coverImageUrl && (fs.existsSync(track.coverImageUrl) || track.coverImageUrl.length > 0));
    const hasReleaseKit = Boolean(track.releaseKit);
    const hasVideo = track.status === 'released';
    const isComplete = Boolean(hasFinalAudio && hasCover && hasReleaseKit);

    return {
      hasDraft,
      hasFinalAudio,
      hasCover,
      hasVideo,
      hasReleaseKit,
      isComplete
    };
  }

  /**
   * Delete track from database and optionally remove vault folder files
   * @param {string} trackId 
   * @param {boolean} [deleteFiles=true] 
   * @returns {boolean}
   */
  deleteTrack(trackId, deleteFiles = true) {
    const track = this.getTrack(trackId);

    if (deleteFiles) {
      try {
        const rootDir = this.vaultRepository.zenionRootDir;
        if (fs.existsSync(rootDir)) {
          const entries = fs.readdirSync(rootDir, { withFileTypes: true });
          for (const entry of entries) {
            if (entry.isDirectory() && entry.name.includes(trackId)) {
              const fullPath = path.join(rootDir, entry.name);
              fs.rmSync(fullPath, { recursive: true, force: true });
            }
          }
        }
        if (track) {
          const sanitized = track.title.replace(/[<>:"/\\|?*]/g, '_').trim();
          const folderPath = path.join(rootDir, `${sanitized}_${track.id}`);
          if (fs.existsSync(folderPath)) {
            fs.rmSync(folderPath, { recursive: true, force: true });
          }
        }
      } catch (err) {
        console.warn(`[VaultStorageService] Error deleting folder for track ${trackId}:`, err.message);
      }
    }

    return this.vaultRepository.delete(trackId);
  }

  /**
   * Clear all tracks from database.json and delete generated track folders in ZENION-MUSIC
   * @param {Object} [options]
   * @param {boolean} [options.deleteFolders=true]
   * @returns {boolean}
   */
  clearAllTracks(options = { deleteFolders: true }) {
    if (options.deleteFolders !== false) {
      try {
        const rootDir = this.vaultRepository.zenionRootDir;
        const preserved = ['BACKUP', '게시된음악', '게시예정음악'];
        if (fs.existsSync(rootDir)) {
          const entries = fs.readdirSync(rootDir, { withFileTypes: true });
          for (const entry of entries) {
            if (entry.isDirectory()) {
              const isPreserved = preserved.some(p => entry.name.startsWith(p));
              if (!isPreserved && (entry.name.includes('TRK-') || entry.name.includes('#'))) {
                const targetPath = path.join(rootDir, entry.name);
                fs.rmSync(targetPath, { recursive: true, force: true });
              }
            }
          }
        }
      } catch (err) {
        console.warn('[VaultStorageService] Error deleting track folders during clearAll:', err.message);
      }
    }

    return this.vaultRepository.clearAll();
  }

  /**
   * Enrich track JSON with assetsStatus and ranking (API-002)
   * @param {Track} track 
   * @param {number} [ranking] 
   * @returns {Object}
   */
  enrichTrack(track, ranking) {
    const json = (track && typeof track.toJSON === 'function') ? track.toJSON() : { ...track };
    return {
      ...json,
      assetsStatus: this.getTrackAssetStatus(track),
      ranking: ranking || null
    };
  }

  /**
   * Generate default release kit if missing
   * @private
   * @param {Track} track 
   * @returns {Object}
   */
  _generateDefaultReleaseKit(track) {
    const title = track.title;
    const genre = track.genre || 'Pop';
    const bpm = track.bpm || 120;

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

    return {
      youtube: {
        title: `[Official MV] ${title} - AI Music Studio (${genre})`,
        description: `🎵 ${title}\n\nProduced with ZENION Music Studio\nGenre: ${genre} | BPM: ${bpm}\n\n⏱️ Timestamps & Lyrics:\n${timestampLyrics}\n\n#AIMusic #ZENION #${genre.replace(/\s+/g, '')} #NewMusic`,
        tags: ['AI Music', 'ZENION Studio', genre, 'Korean Music', 'Pop'],
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
  }

  /**
   * Format SNS release kit to Markdown
   * @private
   * @param {Track} track 
   * @param {Object} kit 
   * @returns {string}
   */
  _formatReleaseKitMarkdown(track, kit) {
    const ytTags = Array.isArray(kit.youtube?.tags) ? kit.youtube.tags.join(', ') : (kit.youtube?.tags || '');
    const instaTags = Array.isArray(kit.instagram?.hashtags) ? kit.instagram.hashtags.join(' ') : (kit.instagram?.hashtags || '');
    const tiktokTags = Array.isArray(kit.tiktok?.hashtags) ? kit.tiktok.hashtags.join(' ') : (kit.tiktok?.hashtags || '');

    return `# Release Kit: ${track.title}

**Genre**: ${track.genre || 'Pop'} | **BPM**: ${track.bpm || 120} | **Track ID**: ${track.id}
**Last Updated**: ${new Date().toISOString()}

---

## 1. YouTube
- **Title**: ${kit.youtube?.title || ''}
- **Description**:
\`\`\`text
${kit.youtube?.description || ''}
\`\`\`
- **Tags**: ${ytTags}

### Timestamps & Lyrics
\`\`\`text
${kit.youtube?.timestampLyrics || ''}
\`\`\`

---

## 2. Instagram
- **Caption**:
\`\`\`text
${kit.instagram?.caption || ''}
\`\`\`
- **Hashtags**: ${instaTags}

---

## 3. TikTok
- **Caption**:
\`\`\`text
${kit.tiktok?.caption || ''}
\`\`\`
- **Hashtags**: ${tiktokTags}
`;
  }
}
