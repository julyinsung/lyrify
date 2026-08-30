import express from 'express';
import fs from 'fs';
import path from 'path';

/**
 * Tracks Routes
 * Related Contracts: API-002, API-003, API-004, API-008, SCN-002, SCN-003
 * 
 * @param {Object} services
 * @param {import('../../core/services/VaultStorageService.js').VaultStorageService} services.vaultService
 * @param {import('../../core/services/QualityJudgeService.js').QualityJudgeService} services.judgeService
 * @returns {express.Router}
 */
export function createTracksRouter({ vaultService, judgeService }) {
  const router = express.Router();

  // GET /api/tracks (API-002, SCN-002) - List all tracks with assets status and AI ranking
  router.get('/', (req, res, next) => {
    try {
      const rawTracks = vaultService.listTracks();
      const rankedTracks = judgeService ? judgeService.rankTracks(rawTracks) : rawTracks;
      const tracks = rankedTracks.map((t, idx) => vaultService.enrichTrack(t, t.ranking || idx + 1));
      return res.json({ success: true, count: tracks.length, tracks });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/scan - Manual re-synchronization of ZENION vault directory
  router.post('/scan', (req, res, next) => {
    try {
      const { rootDir } = req.body || {};
      const result = vaultService.syncVault(rootDir);
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // GET /api/tracks/:id - Get track detail with asset status
  router.get('/:id', (req, res, next) => {
    try {
      const track = vaultService.getTrack(req.params.id);
      if (!track) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }
      return res.json({ success: true, track: vaultService.enrichTrack(track) });
    } catch (err) {
      next(err);
    }
  });

  // PUT /api/tracks/:id or POST /api/tracks/:id/update - Update track metadata, lyrics and style prompt
  const handleUpdate = (req, res, next) => {
    try {
      const track = vaultService.updateTrackMetadata(req.params.id, req.body || {});
      return res.json({
        success: true,
        message: '트랙 정보가 성공적으로 수정 및 저장되었습니다.',
        track: vaultService.enrichTrack(track)
      });
    } catch (err) {
      next(err);
    }
  };

  router.put('/:id', handleUpdate);
  router.post('/:id/update', handleUpdate);

  // POST /api/tracks/:id/evaluate (API-003, SCN-002) - AI Quality Screening
  router.post('/:id/evaluate', async (req, res, next) => {
    try {
      const { audioPath, lyrics } = req.body || {};
      const result = await judgeService.evaluateTrack(req.params.id, { audioPath, lyrics });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/map-suno (API-004) - Suno Audio Mapping & ZENION-MUSIC package folder structure
  router.post('/:id/map-suno', async (req, res, next) => {
    try {
      const { sunoAudioPath, sourceAudioPath, title, targetFolder } = req.body || {};
      const audioPath = sunoAudioPath || sourceAudioPath;

      if (!audioPath) {
        return res.status(400).json({ success: false, error: 'sunoAudioPath or sourceAudioPath is required' });
      }

      const result = await vaultService.mapSunoAudio(req.params.id, {
        sunoAudioPath: audioPath,
        sourceAudioPath: audioPath,
        title,
        targetFolder
      });
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/attach-ace - Attach ACE-Step draft audio file
  router.post('/:id/attach-ace', async (req, res, next) => {
    try {
      const { aceAudioPath, autoEvaluate = true } = req.body || {};
      if (!aceAudioPath) {
        return res.status(400).json({ success: false, error: 'aceAudioPath is required' });
      }

      const result = await vaultService.attachAceDraft(req.params.id, aceAudioPath);
      
      let evaluation = null;
      if (autoEvaluate && judgeService) {
        const track = vaultService.getTrack(req.params.id);
        evaluation = await judgeService.evaluateTrack(req.params.id, {
          audioPath: result.destPath,
          lyrics: track ? track.lyricsRaw : ''
        });
      }

      return res.json({ ...result, evaluation });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/auto-ace - Auto discover and attach audio from ACE-Step output folder
  router.post('/:id/auto-ace', async (req, res, next) => {
    try {
      const aceDirs = [
        '/data/ACE-Step-1.5/output/clean_outputs',
        '/data/ACE-Step-1.5/output/extended_outputs',
        '/data/ACE-Step-1.5/final_selected_tracks',
        'C:/Users/julyi/Documents/ACE-Step-1.5/output/clean_outputs',
        'C:/Users/julyi/Documents/ACE-Step-1.5/output/extended_outputs',
        'C:/Users/julyi/Documents/ACE-Step-1.5/final_selected_tracks'
      ];

      let foundAudioPath = null;
      for (const dir of aceDirs) {
        if (fs.existsSync(dir)) {
          const files = fs.readdirSync(dir).filter(f => f.endsWith('.mp3') || f.endsWith('.wav'));
          if (files.length > 0) {
            // Pick a file or match by index
            foundAudioPath = path.join(dir, files[Math.floor(Math.random() * files.length)]);
            break;
          }
        }
      }

      if (!foundAudioPath) {
        return res.status(404).json({ success: false, error: 'No generated audio files found in ACE-Step output folders.' });
      }

      const result = await vaultService.attachAceDraft(req.params.id, foundAudioPath);
      let evaluation = null;
      if (judgeService) {
        const track = vaultService.getTrack(req.params.id);
        evaluation = await judgeService.evaluateTrack(req.params.id, {
          audioPath: result.destPath,
          lyrics: track ? track.lyricsRaw : ''
        });
      }

      return res.json({ ...result, evaluation, sourceAudio: foundAudioPath });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/export-kit - Export release_kit.md to track master vault
  router.post('/:id/export-kit', (req, res, next) => {
    try {
      const { releaseKit } = req.body || {};
      const result = vaultService.exportReleaseKitFile(req.params.id, releaseKit);
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

  // GET /api/tracks/:id/audio - Stream draft or final audio
  router.get('/:id/audio', (req, res, next) => {
    try {
      const track = vaultService.getTrack(req.params.id);
      if (!track) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }

      const audioPath = track.audioPathSuno || track.audioPathAceStep;
      if (audioPath && fs.existsSync(audioPath)) {
        return res.sendFile(path.resolve(audioPath));
      }

      // Check draft/final folder in vault
      const folderPath = vaultService.vaultRepository.getTrackFolderPath(`${track.title}_${track.id}`);
      const draftPath = path.join(folderPath, '01_draft', 'draft.wav');
      const finalPath = path.join(folderPath, '02_final_audio', 'final.mp3');

      if (fs.existsSync(finalPath)) return res.sendFile(finalPath);
      if (fs.existsSync(draftPath)) return res.sendFile(draftPath);

      return res.status(404).json({ success: false, error: 'Audio file not yet generated or mapped' });
    } catch (err) {
      next(err);
    }
  });

  // DELETE /api/tracks - Clear all tracks and cleanup generated folders
  router.delete('/', (req, res, next) => {
    try {
      const { deleteFolders = true } = req.query || {};
      const success = vaultService.clearAllTracks({ deleteFolders: deleteFolders === 'true' || deleteFolders === true });
      return res.json({ success: true, message: '모든 트랙 및 볼트 폴더가 성공적으로 정리되었습니다.' });
    } catch (err) {
      next(err);
    }
  });

  // DELETE /api/tracks/:id - Delete single track
  router.delete('/:id', (req, res, next) => {
    try {
      const { deleteFiles = true } = req.query || {};
      const success = vaultService.deleteTrack(req.params.id, deleteFiles === 'true' || deleteFiles === true);
      if (!success) {
        return res.status(404).json({ success: false, error: 'Track not found' });
      }
      return res.json({ success: true, message: `Track ${req.params.id} deleted successfully.` });
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/branches (API-010, SCN-007) - Create a new take branch
  router.post('/:id/branches', (req, res, next) => {
    try {
      const result = vaultService.createTrackBranch(req.params.id, req.body || {});
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/tracks/:id/branches/:branchId/merge (API-011, SCN-007) - Merge branch take to Master
  router.post('/:id/branches/:branchId/merge', (req, res, next) => {
    try {
      const { commitMessage } = req.body || {};
      const result = vaultService.mergeBranchToMaster(req.params.id, req.params.branchId, commitMessage);
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  // GET /api/tracks/:id/compare (API-012, SCN-007) - Compare Master vs Branch or Branch vs Branch
  router.get('/:id/compare', (req, res, next) => {
    try {
      const { a = 'master', b } = req.query || {};
      const result = vaultService.compareBranches(req.params.id, a, b);
      return res.json(result);
    } catch (err) {
      next(err);
    }
  });

  return router;
}

export default createTracksRouter;
