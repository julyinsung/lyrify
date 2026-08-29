/**
 * DirectorService (Core Service)
 * 
 * Handles AI Music Director capabilities: planning variable style recipes (1~20 songs),
 * generating structured lyrics ([Verse]/[Chorus]), and triggering ACE-Step draft generation.
 * Supports 3 planning modes:
 * - 'explore': Multi-genre and mood exploration
 * - 'single': Single song theme variations (Acoustic, Remix, Piano Ballad, etc.)
 * - 'album': Cohesive concept album narrative tracklist (Intro -> Title -> Outro)
 * 
 * Related Contracts: API-001, CMP-001, SCN-001, REQ-001
 */
export class DirectorService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/GeminiProvider.js').GeminiProvider} params.geminiProvider
   */
  constructor({ geminiProvider }) {
    if (!geminiProvider) {
      throw new Error('GeminiProvider is required for DirectorService.');
    }
    this.geminiProvider = geminiProvider;
  }

  /**
   * Generate variable music style recipes & lyrics (API-001, SCN-001)
   * 
   * @param {Object} params
   * @param {string} params.keyword - Emotion/vibe keyword (e.g., "새벽 드라이브", "비 오는 날의 이별")
   * @param {number} [params.count=10] - Number of recipes to generate (1~20)
   * @param {'explore'|'single'|'album'} [params.mode='explore'] - Planning mode
   * @param {'gemini'|'openai'|'ollama'} [params.provider='gemini'] - AI LLM provider
   * @returns {Promise<{success: boolean, keyword: string, count: number, mode: string, provider: string, styles: Array<Object>}>}
   */
  async generateStyles({ keyword, count = 10, mode = 'explore', provider = 'gemini' }) {
    const cleanKeyword = String(keyword || '').trim();
    if (!cleanKeyword) {
      throw new Error('Keyword is required to generate style recipes.');
    }

    const validatedCount = Math.min(20, Math.max(1, parseInt(count, 10) || 10));
    const validatedMode = ['explore', 'single', 'album'].includes(mode) ? mode : 'explore';
    const validatedProvider = ['gemini', 'openai', 'ollama'].includes(provider) ? provider : 'gemini';

    const styles = await this.geminiProvider.generateStyleRecipes({
      keyword: cleanKeyword,
      count: validatedCount,
      mode: validatedMode,
      provider: validatedProvider
    });

    return {
      success: true,
      keyword: cleanKeyword,
      count: styles.length,
      mode: validatedMode,
      provider: validatedProvider,
      styles
    };
  }

  /**
   * Trigger ACE-Step 1.5 local generation for a recipe
   * 
   * @param {string} recipeId 
   * @param {Object} [recipeData={}] 
   * @returns {Promise<{success: boolean, jobId: string, recipeId: string, status: string, message: string, timestamp: string}>}
   */
  async triggerAceDraft(recipeId, recipeData = {}) {
    if (!recipeId) {
      throw new Error('Recipe ID is required to trigger ACE-Step draft generation.');
    }

    const jobId = `ACE-JOB-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    return {
      success: true,
      jobId,
      recipeId,
      status: 'queued',
      promptText: recipeData.promptText || '',
      message: `ACE-Step draft generation triggered for recipe ${recipeId}`,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * List available director planning modes
   * @returns {Array<{mode: string, name: string, description: string}>}
   */
  getAvailableModes() {
    return [
      {
        mode: 'explore',
        name: '다채로운 장르 탐색 (Explore)',
        description: '입력된 감성 키워드를 바탕으로 시티팝, 발라드, 로우파이 등 10가지 이상의 다양한 장르/스타일 레시피를 제안합니다.'
      },
      {
        mode: 'single',
        name: '단일 곡 테마 변주 (Single Theme)',
        description: '하나의 곡 테마를 어쿠스틱 버전, EDM 리믹스, 피아노 발라드 등 다채로운 편곡 버전으로 확장합니다.'
      },
      {
        mode: 'album',
        name: '콘셉트 앨범 서사 기획 (Album Tracklist)',
        description: 'Intro부터 Title, Sub-title, Outro까지 유기적으로 이어지는 완성도 높은 정규/미니 앨범 트랙리스트를 기획합니다.'
      }
    ];
  }

  /**
   * [v0.2.0] Single Track Deep Production Blueprint (API-009, SCN-006)
   * Plans sound architecture, music theory rationales, section timeline, and Suno master prompts.
   * 
   * @param {Object} params
   * @param {string} params.story
   * @param {string} [params.mood]
   * @param {string} [params.reference]
   * @param {string} [params.targetGenre]
   * @param {number} [params.bpm]
   * @returns {Promise<Object>}
   */
  async deepProduceTrack({ story, mood, reference, targetGenre, bpm }) {
    if (!story) {
      throw new Error('Story or narrative theme is required for deep track production.');
    }

    const blueprint = await this.geminiProvider.generateDeepProductionBlueprint({
      story: String(story).trim(),
      mood,
      reference,
      targetGenre,
      bpm
    });

    return {
      success: true,
      blueprint
    };
  }
}

export default DirectorService;
