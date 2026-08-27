/**
 * Track Domain Entity
 * 
 * Represents an AI-generated/curated music track within the ZENION Music Studio pipeline.
 * Adheres to DATA-001 (database.json schema) and supports the lifecycle from
 * Director style recipe -> ACE draft -> AI screening -> Suno mapping -> Video export -> Release kit.
 * 
 * Related Contracts: DATA-001, API-001 ~ API-008
 */
export class Track {
  /**
   * @param {Object} params
   * @param {string} params.id
   * @param {string} params.title
   * @param {number} [params.bpm=120]
   * @param {string} [params.genre='Pop']
   * @param {string} [params.lyricsRaw='']
   * @param {number} [params.aiScore=0]
   * @param {string} [params.aiReview='']
   * @param {Object} [params.techCheck={ clipping: false, silence: false }]
   * @param {string} [params.audioPathAceStep='']
   * @param {string} [params.audioPathSuno='']
   * @param {string} [params.coverImageUrl='']
   * @param {Array<{part: string, startSecond: number}>} [params.timeline=[]]
   * @param {Object} [params.releaseKit=null]
   * @param {string} [params.status='draft']
   * @param {string} [params.createdAt]
   * @param {string} [params.updatedAt]
   */
  constructor({
    id,
    title,
    bpm = 120,
    genre = 'Pop',
    lyricsRaw = '',
    aiScore = 0,
    aiReview = '',
    techCheck = { clipping: false, silence: false },
    audioPathAceStep = '',
    audioPathSuno = '',
    coverImageUrl = '',
    timeline = [],
    releaseKit = null,
    status = 'draft',
    createdAt = new Date().toISOString(),
    updatedAt = new Date().toISOString()
  }) {
    if (!id || !title) {
      throw new Error('Track ID and title are required.');
    }

    this.id = id;
    this.title = title;
    this.bpm = Number(bpm) || 120;
    this.genre = genre;
    this.lyricsRaw = lyricsRaw;
    this.aiScore = Math.min(100, Math.max(0, Number(aiScore) || 0));
    this.aiReview = aiReview;
    this.techCheck = techCheck;
    this.audioPathAceStep = audioPathAceStep;
    this.audioPathSuno = audioPathSuno;
    this.coverImageUrl = coverImageUrl;
    this.timeline = Array.isArray(timeline) ? timeline : [];
    this.releaseKit = releaseKit;
    this.status = status;
    this.createdAt = createdAt;
    this.updatedAt = updatedAt;
  }

  /**
   * Update AI quality score & evaluation review (API-003)
   * @param {number} score 
   * @param {string} review 
   * @param {Object} [techCheck]
   */
  updateEvaluation(score, review, techCheck = { clipping: false, silence: false }) {
    this.aiScore = Math.min(100, Math.max(0, Number(score) || 0));
    this.aiReview = review;
    this.techCheck = techCheck;
    this.status = 'evaluated';
    this.updatedAt = new Date().toISOString();
  }

  /**
   * Map commercial Suno audio file (API-004)
   * @param {string} sunoPath 
   */
  mapSunoAudio(sunoPath) {
    if (!sunoPath) throw new Error('Suno audio path is required.');
    this.audioPathSuno = sunoPath;
    this.status = 'mapped';
    this.updatedAt = new Date().toISOString();
  }

  /**
   * Set timeline sync timestamps (API-008)
   * @param {Array<{part: string, startSecond: number}>} timeline 
   */
  setTimeline(timeline) {
    if (!Array.isArray(timeline)) throw new Error('Timeline must be an array.');
    this.timeline = timeline;
    this.updatedAt = new Date().toISOString();
  }

  /**
   * Set SNS release kit (API-007)
   * @param {Object} kit 
   */
  setReleaseKit(kit) {
    this.releaseKit = kit;
    this.status = 'released';
    this.updatedAt = new Date().toISOString();
  }

  /**
   * Convert entity to plain JSON object
   * @returns {Object}
   */
  toJSON() {
    return {
      id: this.id,
      title: this.title,
      bpm: this.bpm,
      genre: this.genre,
      lyricsRaw: this.lyricsRaw,
      aiScore: this.aiScore,
      aiReview: this.aiReview,
      techCheck: this.techCheck,
      audioPathAceStep: this.audioPathAceStep,
      audioPathSuno: this.audioPathSuno,
      coverImageUrl: this.coverImageUrl,
      timeline: this.timeline,
      releaseKit: this.releaseKit,
      status: this.status,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }
}
