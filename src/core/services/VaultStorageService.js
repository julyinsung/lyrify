import fs from 'fs';
import path from 'path';
import { Track } from '../domain/Track.js';

/**
 * VaultStorageService (Core Service)
 * 
 * Manages ZENION-MUSIC asset organization (audio, cover image, lyrics, metadata.json),
 * Suno AI audio mapping, and track persistence.
 * 
 * Related Contracts: API-002, API-004, DATA-001, DATA-002, CMP-003
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
   * Map Suno AI audio file and structure ZENION-MUSIC asset folder (API-004)
   * @param {string} trackId 
   * @param {Object} params
   * @param {string} params.sunoAudioPath
   * @param {string} [params.targetFolder]
   * @returns {Promise<{success: boolean, zenionTrackPath: string, mappedFiles: Object}>}
   */
  async mapSunoTrack(trackId, { sunoAudioPath, targetFolder }) {
    const track = this.getTrack(trackId);
    if (!track) {
      throw new Error(`Track with ID ${trackId} not found.`);
    }

    const folderName = targetFolder || `${track.title.replace(/\s+/g, '_')}_${track.id}`;
    const trackFolderPath = this.vaultRepository.createTrackFolder(folderName);

    // Update track with Suno audio path
    track.mapSunoAudio(sunoAudioPath);
    this.saveTrack(track);

    // Write metadata.json into the track folder
    const metadataPath = path.join(trackFolderPath, 'metadata.json');
    fs.writeFileSync(metadataPath, JSON.stringify(track.toJSON(), null, 2), 'utf8');

    return {
      success: true,
      zenionTrackPath: trackFolderPath,
      mappedFiles: {
        metadata: metadataPath,
        sunoAudio: sunoAudioPath,
        aceAudio: track.audioPathAceStep,
        coverImage: track.coverImageUrl
      }
    };
  }
}
