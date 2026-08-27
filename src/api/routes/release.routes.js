import express from 'express';

/**
 * SNS Release Kit Hub Routes
 * Related Contracts: API-007, SCN-005
 * 
 * @param {Object} services
 * @param {import('../../core/services/ReleaseKitService.js').ReleaseKitService} services.releaseService
 * @returns {express.Router}
 */
export function createReleaseRouter({ releaseService }) {
  const router = express.Router();

  // GET /api/tracks/:id/release-kit (API-007)
  router.get('/:id/release-kit', (req, res, next) => {
    try {
      const releaseKit = releaseService.getReleaseKit(req.params.id);
      if (!releaseKit) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }
      return res.json({ success: true, releaseKit });
    } catch (err) {
      next(err);
    }
  });

  return router;
}
