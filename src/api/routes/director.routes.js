import express from 'express';

/**
 * AI Music Director Routes
 * Related Contracts: API-001, SCN-001
 * 
 * @param {Object} services
 * @param {import('../../core/services/DirectorService.js').DirectorService} services.directorService
 * @returns {express.Router}
 */
export function createDirectorRouter({ directorService }) {
  const router = express.Router();

  // POST /api/director/generate-styles (API-001)
  router.post('/generate-styles', async (req, res, next) => {
    try {
      const { keyword, count = 10, mode = 'explore', provider = 'gemini' } = req.body;
      if (!keyword) {
        return res.status(400).json({ success: false, error: 'Keyword is required' });
      }

      const result = await directorService.generateStyles({ keyword, count, mode, provider });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/director/trigger-ace
  router.post('/trigger-ace', async (req, res, next) => {
    try {
      const { recipeId, recipeData } = req.body;
      if (!recipeId) {
        return res.status(400).json({ success: false, error: 'Recipe ID is required' });
      }

      const result = await directorService.triggerAceDraft(recipeId, recipeData);
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  return router;
}
