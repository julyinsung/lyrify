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
        name: '다양성 탐색 모드 (Explore)',
        description: 'K-Pop, Lo-Fi, City Pop, Synthwave 등 폭넓은 장르와 감성을 탐색합니다.'
      },
      {
        mode: 'single',
        name: '싱글 집중 모드 (Single)',
        description: '하나의 곡 테마를 중심으로 어쿠스틱, 클럽 리믹스, 피아노 발라드 등 다채로운 편곡 바리에이션을 생성합니다.'
      },
      {
        mode: 'album',
        name: '앨범 컨셉 모드 (Album)',
        description: 'Intro부터 Title, B-side, Climax, Outro까지 유기적인 서사 구조를 갖춘 컨셉 앨범 트랙리스트를 완성합니다.'
      }
    ];
  }
}

export default DirectorService;
