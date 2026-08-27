import express from 'express';

/**
 * SNS Release Kit Hub Routes
 * Related Contracts: API-007, SCN-005, REQ-003
 * 
 * @param {Object} services
 * @param {import('../../core/services/ReleaseKitService.js').ReleaseKitService} services.releaseService
 * @returns {express.Router}
 */
export function createReleaseRouter({ releaseService }) {
  const router = express.Router();

  // GET /api/tracks/:id/release-kit (API-007, SCN-005) - Query platform-tailored SNS release kit
  router.get('/:id/release-kit', (req, res, next) => {
    try {
      const releaseKit = releaseService.getReleaseKit(req.params.id);
      if (!releaseKit) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }
      return res.json({
        success: true,
        releaseKit,
        youtube: releaseKit.youtube,
        instagram: releaseKit.instagram,
        tiktok: releaseKit.tiktok
      });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/release-kit (API-007) - Explicitly generate or refresh SNS release kit
  router.post('/:id/release-kit', (req, res, next) => {
    try {
      const { title, genre, bpm } = req.body || {};
      const releaseKit = releaseService.generateReleaseKit(req.params.id, { title, genre, bpm });
      return res.json({
        success: true,
        releaseKit,
        youtube: releaseKit.youtube,
        instagram: releaseKit.instagram,
        tiktok: releaseKit.tiktok
      });
    } catch (err) {
      next(err);
    }
  });

  return router;
}

export default createReleaseRouter;
