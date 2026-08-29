import express from 'express';

/**
 * AI Co-Producer Agent Routes (API-013, SCN-008)
 * Handles conversational directing, iterative tuning, and branch suggestion.
 * 
 * @param {Object} services
 * @param {import('../../core/services/VaultStorageService.js').VaultStorageService} services.vaultService
 * @param {import('../../adapters/GeminiProvider.js').default} services.geminiProvider
 * @returns {express.Router}
 */
export function createAgentRouter({ vaultService, geminiProvider }) {
  const router = express.Router();

  // POST /api/agent/co-produce (API-013, SCN-008)
  router.post('/co-produce', async (req, res, next) => {
    try {
      const { trackId, userInstruction, branchId = 'master' } = req.body || {};
      if (!userInstruction || typeof userInstruction !== 'string') {
        return res.status(400).json({ success: false, error: 'userInstruction is required' });
      }

      const track = vaultService.getTrack(trackId);
      if (!track) {
        return res.status(404).json({ success: false, error: `Track ${trackId} not found` });
      }

      const tuningResult = await geminiProvider.tuneWithCoProducer({
        trackTitle: track.title,
        currentLyrics: track.lyricsRaw,
        currentStyle: track.sunoStylePrompt,
        userInstruction
      });

      // Automatically create a tuned branch take
      const newBranch = vaultService.createTrackBranch(trackId, {
        parentTakeId: branchId,
        branchName: tuningResult.suggestedBranchName,
        description: tuningResult.tuningNotes.join(' / '),
        lyricsRaw: tuningResult.tunedLyrics,
        sunoStylePrompt: tuningResult.tunedStyle
      });

      return res.json({
        success: true,
        agentResponse: tuningResult.agentResponse,
        tuningNotes: tuningResult.tuningNotes,
        tunedLyrics: tuningResult.tunedLyrics,
        tunedStyle: tuningResult.tunedStyle,
        sections: tuningResult.sections,
        newBranch: newBranch.branch
      });
    } catch (err) {
      next(err);
    }
  });

  return router;
}

export default createAgentRouter;
