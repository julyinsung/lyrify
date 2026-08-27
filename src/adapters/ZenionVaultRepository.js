import fs from 'fs';
import path from 'path';

/**
 * ZenionVaultRepository (Driven Adapter)
 * 
 * Manages database.json (DATA-001) persistence and file system operations within
 * the ZENION-MUSIC repository. Enforces strict Path Traversal prevention (SEC-002)
 * and atomic concurrency-safe database reads and writes.
 * 
 * Related Contracts: DATA-001, DATA-002, SEC-002, API-002, API-004
 */
export class ZenionVaultRepository {
  /**
   * @param {Object} [config]
   * @param {string} [config.dbFilePath]
   * @param {string} [config.zenionRootDir]
   * @param {string} [config.aceWatchDir]
   */
  constructor(config = {}) {
    this.zenionRootDir = path.resolve(config.zenionRootDir || process.env.ZENION_ROOT_DIR || './data/ZENION-MUSIC');
    this.aceWatchDir = path.resolve(config.aceWatchDir || process.env.ACE_WATCH_DIR || './data/ACE-Step-1.5');
    
    const defaultDbPath = process.env.DATA_DIR ? path.join(process.env.DATA_DIR, 'database.json') : './data/database.json';
    this.dbFilePath = path.resolve(config.dbFilePath || defaultDbPath);
    
    // Concurrency write queue to serialize async writes
    this._writeQueue = Promise.resolve();

    this._initStorage();
  }

  /**
   * Initialize directory and database.json if not present
   * @private
   */
  _initStorage() {
    const dbDir = path.dirname(this.dbFilePath);
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }
    if (!fs.existsSync(this.zenionRootDir)) {
      fs.mkdirSync(this.zenionRootDir, { recursive: true });
    }
    if (!fs.existsSync(this.dbFilePath)) {
      this._atomicWriteFileSync(this.dbFilePath, JSON.stringify({ tracks: [] }, null, 2));
    }
  }

  /**
   * Validate that path does not escape allowed root directory (SEC-002: Path Traversal defense)
   * @param {string} targetPath 
   * @param {string} [baseDir]
   * @returns {boolean}
   */
  isSafePath(targetPath, baseDir = this.zenionRootDir) {
    if (!targetPath || typeof targetPath !== 'string') return false;
    if (targetPath.includes('\0')) return false;

    let decoded = targetPath;
    try {
      decoded = decodeURIComponent(targetPath);
    } catch (_) {
      return false;
    }

    if (decoded.includes('\0')) return false;

    const resolvedBase = path.resolve(baseDir);
    const resolvedTarget = path.resolve(resolvedBase, decoded);

    // Root drive mismatch defense on Windows
    const baseRoot = path.parse(resolvedBase).root.toLowerCase();
    const targetRoot = path.parse(resolvedTarget).root.toLowerCase();
    if (baseRoot !== targetRoot) {
      return false;
    }

    // Relative path check
    const relative = path.relative(resolvedBase, resolvedTarget);
    if (relative.startsWith('..') || path.isAbsolute(relative)) {
      return false;
    }

    return true;
  }

  /**
   * Assert path safety and return resolved path
   * @param {string} targetPath 
   * @param {string} [baseDir]
   * @returns {string} Resolved safe path
   */
  assertSafePath(targetPath, baseDir = this.zenionRootDir) {
    if (!this.isSafePath(targetPath, baseDir)) {
      throw new Error(`Path Traversal attempt detected: "${targetPath}" escapes "${baseDir}"`);
    }
    return path.resolve(baseDir, targetPath);
  }

  /**
   * Atomic sync file writer using temporary file swap
   * @private
   * @param {string} filePath 
   * @param {string} content 
   */
  _atomicWriteFileSync(filePath, content) {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const tempFile = `${filePath}.tmp.${Date.now()}.${Math.random().toString(36).slice(2, 8)}`;
    try {
      fs.writeFileSync(tempFile, content, 'utf8');
      try {
        fs.renameSync(tempFile, filePath);
      } catch (renameErr) {
        // Fallback for Windows lock issues
        fs.copyFileSync(tempFile, filePath);
        fs.unlinkSync(tempFile);
      }
    } catch (err) {
      if (fs.existsSync(tempFile)) {
        try { fs.unlinkSync(tempFile); } catch (_) {}
      }
      throw err;
    }
  }

  /**
   * Atomic async file writer using temporary file swap
   * @private
   * @param {string} filePath 
   * @param {string} content 
   */
  async _atomicWriteFileAsync(filePath, content) {
    const dir = path.dirname(filePath);
    await fs.promises.mkdir(dir, { recursive: true });
    const tempFile = `${filePath}.tmp.${Date.now()}.${Math.random().toString(36).slice(2, 8)}`;
    try {
      await fs.promises.writeFile(tempFile, content, 'utf8');
      try {
        await fs.promises.rename(tempFile, filePath);
      } catch (renameErr) {
        // Fallback for Windows lock issues
        await fs.promises.copyFile(tempFile, filePath);
        await fs.promises.unlink(tempFile);
      }
    } catch (err) {
      if (fs.existsSync(tempFile)) {
        try { await fs.promises.unlink(tempFile); } catch (_) {}
      }
      throw err;
    }
  }

  /**
   * Enqueue write operations to prevent concurrent write collisions
   * @private
   * @param {Function} taskFn 
   * @returns {Promise<any>}
   */
  _enqueueWrite(taskFn) {
    const nextPromise = this._writeQueue.then(() => taskFn()).catch((err) => {
      // Catch and rethrow to maintain queue liveness
      throw err;
    });
    this._writeQueue = nextPromise.catch(() => {});
    return nextPromise;
  }

  /**
   * Load all tracks from database.json (Synchronous)
   * @returns {Array<Object>}
   */
  loadAll() {
    try {
      if (!fs.existsSync(this.dbFilePath)) return [];
      const content = fs.readFileSync(this.dbFilePath, 'utf8');
      const parsed = JSON.parse(content || '{"tracks":[]}');
      return Array.isArray(parsed.tracks) ? parsed.tracks : [];
    } catch (err) {
      console.warn(`[ZenionVaultRepository] Warning reading database.json: ${err.message}`);
      return [];
    }
  }

  /**
   * Load all tracks from database.json (Asynchronous)
   * @returns {Promise<Array<Object>>}
   */
  async loadAllAsync() {
    try {
      if (!fs.existsSync(this.dbFilePath)) return [];
      const content = await fs.promises.readFile(this.dbFilePath, 'utf8');
      const parsed = JSON.parse(content || '{"tracks":[]}');
      return Array.isArray(parsed.tracks) ? parsed.tracks : [];
    } catch (err) {
      console.warn(`[ZenionVaultRepository] Warning reading database.json async: ${err.message}`);
      return [];
    }
  }

  /**
   * Find track by ID (Synchronous)
   * @param {string} id 
   * @returns {Object|null}
   */
  findById(id) {
    const tracks = this.loadAll();
    return tracks.find((t) => t.id === id) || null;
  }

  /**
   * Find track by ID (Asynchronous)
   * @param {string} id 
   * @returns {Promise<Object|null>}
   */
  async findByIdAsync(id) {
    const tracks = await this.loadAllAsync();
    return tracks.find((t) => t.id === id) || null;
  }

  /**
   * Save or update a track record (Synchronous)
   * @param {Object} trackData 
   * @returns {Object}
   */
  save(trackData) {
    const tracks = this.loadAll();
    const index = tracks.findIndex((t) => t.id === trackData.id);

    if (index >= 0) {
      tracks[index] = { ...tracks[index], ...trackData, updatedAt: new Date().toISOString() };
    } else {
      tracks.push({ ...trackData, createdAt: trackData.createdAt || new Date().toISOString(), updatedAt: new Date().toISOString() });
    }

    this._atomicWriteFileSync(this.dbFilePath, JSON.stringify({ tracks }, null, 2));
    return trackData;
  }

  /**
   * Save or update a track record (Asynchronous with Mutex)
   * @param {Object} trackData 
   * @returns {Promise<Object>}
   */
  async saveAsync(trackData) {
    return this._enqueueWrite(async () => {
      const tracks = await this.loadAllAsync();
      const index = tracks.findIndex((t) => t.id === trackData.id);

      if (index >= 0) {
        tracks[index] = { ...tracks[index], ...trackData, updatedAt: new Date().toISOString() };
      } else {
        tracks.push({ ...trackData, createdAt: trackData.createdAt || new Date().toISOString(), updatedAt: new Date().toISOString() });
      }

      await this._atomicWriteFileAsync(this.dbFilePath, JSON.stringify({ tracks }, null, 2));
      return trackData;
    });
  }

  /**
   * Save multiple track records at once
   * @param {Array<Object>} trackList 
   * @returns {Array<Object>}
   */
  saveMany(trackList) {
    const tracks = this.loadAll();
    const trackMap = new Map(tracks.map((t) => [t.id, t]));

    for (const item of trackList) {
      const existing = trackMap.get(item.id);
      if (existing) {
        trackMap.set(item.id, { ...existing, ...item, updatedAt: new Date().toISOString() });
      } else {
        trackMap.set(item.id, { ...item, createdAt: item.createdAt || new Date().toISOString(), updatedAt: new Date().toISOString() });
      }
    }

    const updatedList = Array.from(trackMap.values());
    this._atomicWriteFileSync(this.dbFilePath, JSON.stringify({ tracks: updatedList }, null, 2));
    return updatedList;
  }

  /**
   * Delete a track by ID (Synchronous)
   * @param {string} id 
   * @returns {boolean}
   */
  delete(id) {
    const tracks = this.loadAll();
    const filtered = tracks.filter((t) => t.id !== id);
    if (filtered.length !== tracks.length) {
      this._atomicWriteFileSync(this.dbFilePath, JSON.stringify({ tracks: filtered }, null, 2));
      return true;
    }
    return false;
  }

  /**
   * Delete a track by ID (Asynchronous with Mutex)
   * @param {string} id 
   * @returns {Promise<boolean>}
   */
  async deleteAsync(id) {
    return this._enqueueWrite(async () => {
      const tracks = await this.loadAllAsync();
      const filtered = tracks.filter((t) => t.id !== id);
      if (filtered.length !== tracks.length) {
        await this._atomicWriteFileAsync(this.dbFilePath, JSON.stringify({ tracks: filtered }, null, 2));
        return true;
      }
      return false;
    });
  }

  /**
   * Create structured folder and standard subdirectories inside ZENION-MUSIC for a track (SCN-003, REQ-002, API-004)
   * Standard Subdirectories: 01_draft/, 02_final_audio/, 03_visuals/, 04_videos/
   * 
   * @param {string} folderName 
   * @returns {string} Absolute path to created folder
   */
  createTrackFolder(folderName) {
    // Assert safe path on the input folderName first to block traversal tokens
    if (!this.isSafePath(folderName, this.zenionRootDir)) {
      throw new Error(`Path Traversal attempt detected: ${folderName}`);
    }

    // Sanitize folder name
    const sanitized = folderName.replace(/[<>:"/\\|?*]/g, '_').trim();
    if (!this.isSafePath(sanitized, this.zenionRootDir)) {
      throw new Error(`Path Traversal attempt detected: ${folderName}`);
    }

    const folderPath = path.join(this.zenionRootDir, sanitized);

    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }

    // Standard complete package subdirectories
    const subDirs = ['01_draft', '02_final_audio', '03_visuals', '04_videos'];
    for (const subDir of subDirs) {
      const subPath = path.join(folderPath, subDir);
      if (!fs.existsSync(subPath)) {
        fs.mkdirSync(subPath, { recursive: true });
      }
    }

    return folderPath;
  }

  /**
   * Get safe absolute track folder path
   * @param {string} folderName 
   * @returns {string}
   */
  getTrackFolderPath(folderName) {
    const sanitized = folderName.replace(/[<>:"/\\|?*]/g, '_').trim();
    return this.assertSafePath(sanitized, this.zenionRootDir);
  }
}
