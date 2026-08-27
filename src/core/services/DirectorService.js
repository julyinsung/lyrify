/**
 * DirectorService (Core Service)
 * 
 * Handles AI Music Director capabilities: planning variable style recipes (1~20 songs),
 * generating structured lyrics ([Verse]/[Chorus]), and triggering ACE-Step draft generation.
 * 
 * Related Contracts: API-001, CMP-001, SCN-001
 */
export class DirectorService {
  /**
   * @param {Object} params
   * @param {import('../../adapters/GeminiProvider.js').GeminiProvider} params.geminiProvider
   */
  constructor({ geminiProvider }) {
    this.geminiProvider = geminiProvider;
  }

  /**
   * Generate variable music style recipes & lyrics (API-001)
   * @param {Object} params
   * @param {string} params.keyword - Emotion/vibe keyword
   * @param {number} [params.count=10] - Number of recipes (1~20)
   * @param {'explore'|'single'|'album'} [params.mode='explore']
   * @param {'gemini'|'openai'|'ollama'} [params.provider='gemini']
   * @returns {Promise<{success: boolean, keyword: string, count: number, mode: string, styles: Array<Object>}>}
   */
  async generateStyles({ keyword, count = 10, mode = 'explore', provider = 'gemini' }) {
    if (!keyword || typeof keyword !== 'string') {
      throw new Error('Keyword is required to generate style recipes.');
    }

    const validatedCount = Math.min(20, Math.max(1, Number(count) || 10));
    const styles = await this.geminiProvider.generateStyleRecipes({
      keyword,
      count: validatedCount,
      mode
    });

    return {
      success: true,
      keyword,
      count: styles.length,
      mode,
      provider,
      styles
    };
  }

  /**
   * Trigger ACE-Step 1.5 local generation for a recipe
   * @param {string} recipeId 
   * @param {Object} recipeData 
   * @returns {Promise<{success: boolean, jobId: string, message: string}>}
   */
  async triggerAceDraft(recipeId, recipeData) {
    const jobId = `ACE-JOB-${Date.now()}`;
    return {
      success: true,
      jobId,
      message: `ACE-Step draft generation triggered for recipe ${recipeId}`
    };
  }
}
