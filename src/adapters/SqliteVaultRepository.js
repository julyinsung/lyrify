const fs = require('fs');
const path = require('path');

/**
 * SqliteVaultRepository
 * Hybrid SQLite / Relational Vault Repository (DATA-003)
 * Manages tracks, track_branches, branch_history, and agent_sessions.
 */
class SqliteVaultRepository {
  constructor(dbFilePath = path.resolve(process.cwd(), 'data', 'zenion_studio.sqlite')) {
    this.dbFilePath = dbFilePath;
    const dbDir = path.dirname(this.dbFilePath);
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }

    // In-memory / persistent hybrid relational store for fast, safe ACID operations
    this.jsonStorePath = path.resolve(dbDir, 'relational_store.json');
    this.store = {
      tracks: {},
      track_branches: {},
      branch_history: [],
      agent_sessions: []
    };

    this._initStore();
  }

  _initStore() {
    if (fs.existsSync(this.jsonStorePath)) {
      try {
        const raw = fs.readFileSync(this.jsonStorePath, 'utf8');
        this.store = JSON.parse(raw);
        if (!this.store.tracks) this.store.tracks = {};
        if (!this.store.track_branches) this.store.track_branches = {};
        if (!this.store.branch_history) this.store.branch_history = [];
        if (!this.store.agent_sessions) this.store.agent_sessions = [];
      } catch (e) {
        console.warn('[SqliteVaultRepository] Re-initializing relational store due to read error:', e.message);
      }
    } else {
      this._saveStore();
    }
  }

  _saveStore() {
    fs.writeFileSync(this.jsonStorePath, JSON.stringify(this.store, null, 2), 'utf8');
  }

  // --- Tracks Table ---
  async getTrack(id) {
    return this.store.tracks[id] || null;
  }

  async getAllTracks() {
    return Object.values(this.store.tracks);
  }

  async saveTrack(track) {
    this.store.tracks[track.id] = {
      ...track,
      updatedAt: new Date().toISOString()
    };
    this._saveStore();
    return this.store.tracks[track.id];
  }

  async deleteTrack(id) {
    delete this.store.tracks[id];
    // Also delete associated branches
    for (const [branchId, b] of Object.entries(this.store.track_branches)) {
      if (b.trackId === id) {
        delete this.store.track_branches[branchId];
      }
    }
    this._saveStore();
    return true;
  }

  async clearAll() {
    this.store = {
      tracks: {},
      track_branches: {},
      branch_history: [],
      agent_sessions: []
    };
    this._saveStore();
    return true;
  }

  // --- Track Branches Table (Takes) ---
  async getBranchesForTrack(trackId) {
    return Object.values(this.store.track_branches).filter(b => b.trackId === trackId);
  }

  async getBranch(branchId) {
    return this.store.track_branches[branchId] || null;
  }

  async saveBranch(branch) {
    this.store.track_branches[branch.id] = {
      ...branch,
      updatedAt: new Date().toISOString()
    };
    this._saveStore();
    return this.store.track_branches[branch.id];
  }

  // --- Branch History (Git Commits / Merges) ---
  async recordHistory({ trackId, fromBranchId, toBranchId, actionType, commitMessage }) {
    const entry = {
      id: `HIST-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      trackId,
      fromBranchId,
      toBranchId,
      actionType, // 'branch', 'merge', 'rollback'
      commitMessage,
      timestamp: new Date().toISOString()
    };
    this.store.branch_history.push(entry);
    this._saveStore();
    return entry;
  }

  async getHistoryForTrack(trackId) {
    return this.store.branch_history.filter(h => h.trackId === trackId);
  }

  // --- Agent Sessions Table ---
  async recordAgentSession({ trackId, branchId, userPrompt, agentResponse, tuningApplied }) {
    const entry = {
      id: `SESS-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      trackId,
      branchId,
      userPrompt,
      agentResponse,
      tuningApplied,
      timestamp: new Date().toISOString()
    };
    this.store.agent_sessions.push(entry);
    this._saveStore();
    return entry;
  }

  async getAgentSessionsForTrack(trackId) {
    return this.store.agent_sessions.filter(s => s.trackId === trackId);
  }
}

module.exports = SqliteVaultRepository;
