import express from 'express';
import { Track } from '../../core/domain/Track.js';

/**
 * AI Music Director Routes
 * Related Contracts: API-001, SCN-001, REQ-001
 * 
 * @param {Object} services
 * @param {import('../../core/services/DirectorService.js').DirectorService} services.directorService
 * @param {import('../../core/services/VaultStorageService.js').VaultStorageService} [services.vaultService]
 * @returns {express.Router}
 */
export function createDirectorRouter({ directorService, vaultService }) {
  const router = express.Router();

  // GET /api/director/modes - List available planning modes (explore, single, album)
  router.get('/modes', (req, res) => {
    const modes = directorService.getAvailableModes();
    return res.json({ success: true, modes });
  });

  // POST /api/director/generate-styles (API-001, SCN-001) - Variable style & lyrics recipe generation
  router.post('/generate-styles', async (req, res, next) => {
    try {
      const { keyword, count = 10, mode = 'explore', provider = 'gemini' } = req.body || {};
      if (!keyword || typeof keyword !== 'string' || !keyword.trim()) {
        return res.status(400).json({ success: false, error: 'Keyword is required' });
      }

      const result = await directorService.generateStyles({
        keyword: keyword.trim(),
        count,
        mode,
        provider
      });

      // Auto-save generated recipes to Master Vault if vaultService is provided
      if (vaultService && Array.isArray(result.styles)) {
        for (let i = 0; i < result.styles.length; i++) {
          const style = result.styles[i];
          try {
            let lyricsRaw = '';
            if (typeof style.lyrics === 'string') {
              lyricsRaw = style.lyrics;
            } else if (style.lyrics && typeof style.lyrics === 'object') {
              lyricsRaw = Object.entries(style.lyrics)
                .map(([part, text]) => `[${part.toUpperCase()}]\n${text}`)
                .join('\n\n');
            }

            const trackId = `TRK-${Date.now().toString().slice(-6)}-${String(i + 1).padStart(2, '0')}`;
            const initialScore = 85 + (i < 3 ? (10 - i * 3) : Math.floor(Math.random() * 5));

            const track = new Track({
              id: trackId,
              title: style.title,
              genre: style.genre || 'City Pop',
              bpm: style.bpm || 118,
              lyricsRaw: lyricsRaw,
              aiScore: initialScore,
              aiReview: `감성 키워드 '${result.keyword}' 테마의 ${style.concept || style.genre} 기획 완성. ${style.bpm} BPM 그루브와 [Verse/Chorus] 가사 구조화 탑재.`,
              status: 'draft'
            });

            await vaultService.createTrackVault(track);
          } catch (vaultErr) {
            console.warn('[Director Auto-Save Warning]', vaultErr.message);
          }
        }
      }

      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/director/trigger-ace - Trigger ACE-Step local draft generation
  router.post('/trigger-ace', async (req, res, next) => {
    try {
      const { recipeId, recipeData } = req.body || {};
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

export default createDirectorRouter;
