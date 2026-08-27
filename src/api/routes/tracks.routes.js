import express from 'express';

/**
 * Tracks Routes
 * Related Contracts: API-002, API-003, API-004, API-008
 * 
 * @param {Object} services
 * @param {import('../../core/services/VaultStorageService.js').VaultStorageService} services.vaultService
 * @param {import('../../core/services/QualityJudgeService.js').QualityJudgeService} services.judgeService
 * @returns {express.Router}
 */
export function createTracksRouter({ vaultService, judgeService }) {
  const router = express.Router();

  // GET /api/tracks (API-002) - List all tracks & AI ranking
  router.get('/', (req, res, next) => {
    try {
      const tracks = vaultService.listTracks().map((t) => t.toJSON());
      return res.json({ success: true, count: tracks.length, tracks });
    } catch (err) {
      next(err);
    }
  });

  // GET /api/tracks/:id - Get track detail
  router.get('/:id', (req, res, next) => {
    try {
      const track = vaultService.getTrack(req.params.id);
      if (!track) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }
      return res.json({ success: true, track: track.toJSON() });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/evaluate (API-003) - AI Quality Screening
  router.post('/:id/evaluate', async (req, res, next) => {
    try {
      const { audioPath, lyrics } = req.body || {};
      const result = await judgeService.evaluateTrack(req.params.id, { audioPath, lyrics });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/map-suno (API-004) - Suno Audio Mapping & ZENION-MUSIC organization
  router.post('/:id/map-suno', async (req, res, next) => {
    try {
      const { sunoAudioPath, targetFolder } = req.body || {};
      if (!sunoAudioPath) {
        return res.status(400).json({ success: false, error: 'sunoAudioPath is required' });
      }

      const result = await vaultService.mapSunoTrack(req.params.id, {
        sunoAudioPath,
        targetFolder
      });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/sync (API-008) - Lyric timeline sync
  router.post('/:id/sync', (req, res, next) => {
    try {
      const { timeline } = req.body || {};
      if (!Array.isArray(timeline)) {
        return res.status(400).json({ success: false, error: 'timeline must be an array' });
      }

      const track = vaultService.getTrack(req.params.id);
      if (!track) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }

      track.setTimeline(timeline);
      vaultService.saveTrack(track);

      return res.json({ success: true, updatedTimeline: track.timeline });
    } catch (err) {
      next(err);
    }
  });

  return router;
}
