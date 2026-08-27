import express from 'express';

/**
 * Video & Visual Studio Routes
 * Related Contracts: API-005, API-006, GAP-001, SCN-004
 * 
 * @param {Object} services
 * @param {import('../../core/services/VideoRenderService.js').VideoRenderService} services.renderService
 * @returns {express.Router}
 */
export function createVideoRouter({ renderService }) {
  const router = express.Router();

  // POST /api/tracks/:id/generate-image (API-005) - AI Thumbnail / Cover synthesis
  router.post('/:id/generate-image', async (req, res, next) => {
    try {
      const { useApi = false, customPrompt } = req.body || {};
      const result = await renderService.generateCoverImage(req.params.id, {
        useApi,
        customPrompt
      });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/export-video (API-006) - Multi-format Video Rendering
  router.post('/:id/export-video', async (req, res, next) => {
    try {
      const { format = 'youtube_16x9', audioType = 'suno' } = req.body || {};
      const result = await renderService.exportVideo(req.params.id, {
        format,
        audioType
      });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // GET /api/video/status/:jobId (GAP-001) - Poll encoding progress
  router.get('/status/:jobId', (req, res, next) => {
    try {
      const status = renderService.getEncodingStatus(req.params.jobId);
      if (!status) {
        return res.status(404).json({ success: false, error: 'Job not found' });
      }
      return res.json({ success: true, job: status });
    } catch (err) {
      next(err);
    }
  });

  return router;
}
