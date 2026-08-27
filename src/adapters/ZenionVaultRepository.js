import fs from 'fs';
import path from 'path';

/**
 * ZenionVaultRepository (Driven Adapter)
 * 
 * Manages database.json (DATA-001) persistence and file system operations within
 * the ZENION-MUSIC repository. Enforces strict Path Traversal prevention (SEC-002).
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
      fs.writeFileSync(this.dbFilePath, JSON.stringify({ tracks: [] }, null, 2), 'utf8');
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
    // Check for null bytes or direct traversal tokens
    if (targetPath.includes('\0') || targetPath.includes('..\\') || targetPath.includes('../')) {
      const resolved = path.resolve(baseDir, targetPath);
      const relative = path.relative(baseDir, resolved);
      return !relative.startsWith('..') && !path.isAbsolute(relative);
    }
    const resolved = path.resolve(baseDir, targetPath);
    const relative = path.relative(baseDir, resolved);
    return !relative.startsWith('..') && !path.isAbsolute(relative);
  }

  /**
   * Load all tracks from database.json
   * @returns {Array<Object>}
   */
  loadAll() {
    try {
      if (!fs.existsSync(this.dbFilePath)) return [];
      const content = fs.readFileSync(this.dbFilePath, 'utf8');
      const parsed = JSON.parse(content || '{"tracks":[]}');
      return Array.isArray(parsed.tracks) ? parsed.tracks : [];
    } catch (err) {
      return [];
    }
  }

  /**
   * Find track by ID
   * @param {string} id 
   * @returns {Object|null}
   */
  findById(id) {
    const tracks = this.loadAll();
    return tracks.find((t) => t.id === id) || null;
  }

  /**
   * Save or update a track record
   * @param {Object} trackData 
   * @returns {Object}
   */
  save(trackData) {
    const tracks = this.loadAll();
    const index = tracks.findIndex((t) => t.id === trackData.id);

    if (index >= 0) {
      tracks[index] = { ...tracks[index], ...trackData, updatedAt: new Date().toISOString() };
    } else {
      tracks.push({ ...trackData, createdAt: trackData.createdAt || new Date().toISOString() });
    }

    fs.writeFileSync(this.dbFilePath, JSON.stringify({ tracks }, null, 2), 'utf8');
    return trackData;
  }

  /**
   * Delete a track by ID
   * @param {string} id 
   * @returns {boolean}
   */
  delete(id) {
    const tracks = this.loadAll();
    const filtered = tracks.filter((t) => t.id !== id);
    if (filtered.length !== tracks.length) {
      fs.writeFileSync(this.dbFilePath, JSON.stringify({ tracks: filtered }, null, 2), 'utf8');
      return true;
    }
    return false;
  }

  /**
   * Create structured folder inside ZENION-MUSIC for a track (API-004)
   * @param {string} folderName 
   * @returns {string} Absolute path to created folder
   */
  createTrackFolder(folderName) {
    // Sanitize folder name
    const sanitized = folderName.replace(/[<>:"/\\|?*]/g, '_').trim();
    const folderPath = path.join(this.zenionRootDir, sanitized);

    if (!this.isSafePath(sanitized, this.zenionRootDir)) {
      throw new Error('Path Traversal attempt detected: ' + folderName);
    }

    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }
    return folderPath;
  }
}
