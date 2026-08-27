import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

// Domain and Services
import { VaultStorageService } from './core/services/VaultStorageService.js';
import { DirectorService } from './core/services/DirectorService.js';
import { QualityJudgeService } from './core/services/QualityJudgeService.js';
import { VideoRenderService } from './core/services/VideoRenderService.js';
import { ReleaseKitService } from './core/services/ReleaseKitService.js';

// Adapters
import { GeminiProvider } from './adapters/GeminiProvider.js';
import { FFmpegVideoEncoder } from './adapters/FFmpegVideoEncoder.js';
import { ZenionVaultRepository } from './adapters/ZenionVaultRepository.js';

// Route Handlers
import { createDirectorRouter } from './api/routes/director.routes.js';
import { createTracksRouter } from './api/routes/tracks.routes.js';
import { createVideoRouter } from './api/routes/video.routes.js';
import { createReleaseRouter } from './api/routes/release.routes.js';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Create and configure Express application
 */
export function createApp() {
  const app = express();

  // Middleware
  app.use(cors());
  app.use(express.json({ limit: '50mb' }));
  app.use(express.urlencoded({ extended: true, limit: '50mb' }));

  // Initialize Driven Adapters
  const geminiProvider = new GeminiProvider({
    apiKey: process.env.GEMINI_API_KEY
  });
  const ffmpegEncoder = new FFmpegVideoEncoder();
  const dbPath = process.env.DATA_DIR ? path.join(process.env.DATA_DIR, 'database.json') : './data/database.json';
  const vaultRepository = new ZenionVaultRepository({
    zenionRootDir: process.env.ZENION_ROOT_DIR,
    aceWatchDir: process.env.ACE_WATCH_DIR,
    dbFilePath: dbPath
  });

  // Initialize Core Services
  const vaultService = new VaultStorageService({ vaultRepository });
  const directorService = new DirectorService({ geminiProvider });
  const judgeService = new QualityJudgeService({
    ffmpegEncoder,
    geminiProvider,
    vaultService
  });
  const renderService = new VideoRenderService({
    ffmpegEncoder,
    vaultService
  });
  const releaseService = new ReleaseKitService({ vaultService });

  // Healthcheck endpoints
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'lyrify', timestamp: new Date().toISOString() });
  });
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'ok',
      service: 'lyrify',
      environment: process.env.NODE_ENV || 'development',
      adapters: {
        geminiConfigured: geminiProvider.isConfigured(),
        zenionRootDir: vaultRepository.zenionRootDir
      },
      timestamp: new Date().toISOString()
    });
  });

  // API Routes
  app.use('/api/director', createDirectorRouter({ directorService }));
  app.use('/api/tracks', createTracksRouter({ vaultService, judgeService }));
  app.use('/api/tracks', createVideoRouter({ renderService }));
  app.use('/api/tracks', createReleaseRouter({ releaseService }));

  // Global Error Handler
  app.use((err, req, res, next) => {
    console.error('[App Error]', err);
    res.status(err.status || 500).json({
      success: false,
      error: err.message || 'Internal Server Error'
    });
  });

  return {
    app,
    services: {
      vaultService,
      directorService,
      judgeService,
      renderService,
      releaseService
    },
    adapters: {
      geminiProvider,
      ffmpegEncoder,
      vaultRepository
    }
  };
}

// Start server when executed directly
const isDirectExecution = process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url;

if (isDirectExecution) {
  const PORT = process.env.PORT || 3000;
  const { app } = createApp();
  app.listen(PORT, () => {
    console.log(`[ZENION Music Studio] Server listening on http://localhost:${PORT}`);
  });
}

export default createApp;
