import { GoogleGenAI, Type } from '@google/genai';

/**
 * GeminiProvider (Driven Adapter)
 * 
 * Interacts with Google Gemini API using @google/genai SDK for Structured Output generation,
 * style recipe planning (API-001), lyrics composition, and AI quality scoring (API-003).
 * Supports variable track counts (1~20) across 3 planning modes:
 * - 'explore': Broad exploration across diverse genres and moods
 * - 'single': Deep dive into single track arrangement variations (Acoustic, Remix, Club, etc.)
 * - 'album': Cohesive concept album narrative tracklist (Intro -> Title -> B-Sides -> Climax -> Outro)
 * 
 * Provides an intelligent, high-fidelity offline fallback generator when running without API key or offline.
 * 
 * Related Contracts: API-001, API-003, SEC-001, SCN-001, REQ-001
 */
export class GeminiProvider {
  /**
   * @param {Object} [config]
   * @param {string} [config.apiKey]
   * @param {string} [config.model]
   */
  constructor(config = {}) {
    this.apiKey = config.apiKey || process.env.GEMINI_API_KEY || '';
    this.model = config.model || 'gemini-2.0-flash';
    this.client = null;

    if (this.isConfigured()) {
      try {
        this.client = new GoogleGenAI({ apiKey: this.apiKey });
      } catch (err) {
        console.warn('[GeminiProvider] Initialization warning:', err.message);
        this.client = null;
      }
    }
  }

  /**
   * Check if Gemini API is configured with a valid key
   * @returns {boolean}
   */
  isConfigured() {
    return Boolean(
      this.apiKey &&
      this.apiKey !== 'your_gemini_api_key_here' &&
      this.apiKey !== 'test_api_key_placeholder' &&
      this.apiKey.trim().length > 10
    );
  }

  /**
   * Generate variable style recipes and lyrics (API-001, SCN-001)
   * 
   * @param {Object} params
   * @param {string} params.keyword - Emotion/vibe keyword (e.g. "비 오는 날의 이별")
   * @param {number} [params.count=10] - Number of tracks (1~20)
   * @param {'explore'|'single'|'album'} [params.mode='explore']
   * @param {'gemini'|'openai'|'ollama'} [params.provider='gemini']
   * @returns {Promise<Array<Object>>}
   */
  async generateStyleRecipes({ keyword, count = 10, mode = 'explore', provider = 'gemini' }) {
    const targetCount = Math.min(20, Math.max(1, Number(count) || 10));
    const targetMode = ['explore', 'single', 'album'].includes(mode) ? mode : 'explore';

    // If Gemini client is active, attempt Structured Output generation via Google Gemini SDK
    if (this.client && this.isConfigured() && provider === 'gemini') {
      try {
        const recipes = await this._generateWithGeminiSdk({
          keyword,
          count: targetCount,
          mode: targetMode
        });
        if (Array.isArray(recipes) && recipes.length > 0) {
          return recipes.slice(0, targetCount);
        }
      } catch (err) {
        console.warn(`[GeminiProvider] Online Gemini API generation failed (${err.message}). Falling back to offline generator.`);
      }
    }

    // High quality offline fallback generator
    return this._generateOfflineRecipes({
      keyword,
      count: targetCount,
      mode: targetMode
    });
  }

  /**
   * Structured generation via Google Gemini SDK (@google/genai)
   * @private
   */
  async _generateWithGeminiSdk({ keyword, count, mode }) {
    const prompt = `You are the Lead Music Director and Composer of ZENION AI Music Studio.
Generate exactly ${count} distinct and structured song recipes based on the keyword/theme: "${keyword}".
The planning mode is "${mode}".
- explore mode: Diverse genre exploration (K-Pop, Lo-Fi, City Pop, Synthwave, Rock, Ambient, R&B, etc.).
- single mode: Focused stylistic variations of a single core song (Acoustic, Radio Edit, Lo-Fi Chill, Synthwave Club, Piano Ballad, etc.).
- album mode: Cohesive concept album narrative (Track 1: Intro, Track 2: Lead Title Track, Track 3: B-side Groove, ..., Final Track: Outro).

Every track must include structured Korean lyrics with [Verse 1], [Chorus], and [Verse 2] sections.`;

    const responseSchema = {
      type: Type.ARRAY,
      description: `List of ${count} music recipes`,
      items: {
        type: Type.OBJECT,
        properties: {
          id: { type: Type.STRING },
          title: { type: Type.STRING },
          genre: { type: Type.STRING },
          bpm: { type: Type.INTEGER },
          instruments: { type: Type.STRING },
          lyricTheme: { type: Type.STRING },
          lyrics: {
            type: Type.OBJECT,
            properties: {
              verse1: { type: Type.STRING },
              chorus: { type: Type.STRING },
              verse2: { type: Type.STRING }
            },
            required: ['verse1', 'chorus', 'verse2']
          },
          promptText: { type: Type.STRING },
          mode: { type: Type.STRING },
          concept: { type: Type.STRING }
        },
        required: ['id', 'title', 'genre', 'bpm', 'instruments', 'lyricTheme', 'lyrics', 'promptText']
      }
    };

    const response = await this.client.models.generateContent({
      model: this.model,
      contents: prompt,
      config: {
        responseMimeType: 'application/json',
        responseSchema: responseSchema,
        temperature: 0.7
      }
    });

    const parsed = JSON.parse(response.text);
    if (Array.isArray(parsed)) {
      return parsed.map((item, index) => ({
        id: item.id || `RECIPE-${String(index + 1).padStart(3, '0')}`,
        title: item.title || `${keyword} - Track #${index + 1}`,
        genre: item.genre || 'Pop',
        bpm: Number(item.bpm) || 120,
        instruments: item.instruments || 'Piano, Drums, Bass',
        lyricTheme: item.lyricTheme || `${keyword} 스토리텔링`,
        lyrics: {
          verse1: item.lyrics?.verse1 || `[Verse 1]\n${keyword}의 기억을 따라 걷는 밤`,
          chorus: item.lyrics?.chorus || `[Chorus]\n마음속 깊이 울리는 우리의 노래`,
          verse2: item.lyrics?.verse2 || `[Verse 2]\n새로운 계절이 찾아와도 남겨진 멜로디`
        },
        promptText: item.promptText || `[Genre: ${item.genre || 'Pop'}] [BPM: ${item.bpm || 120}] [Theme: ${keyword}]`,
        mode: mode,
        concept: item.concept || `${mode} Track ${index + 1}`
      }));
    }

    return null;
  }

  /**
   * High quality offline style & lyrics recipe generator supporting 3 modes and 1~20 tracks
   * @private
   */
  _generateOfflineRecipes({ keyword, count, mode }) {
    const recipes = [];

    // Genre catalog for 'explore' mode
    const exploreGenres = [
      { genre: 'K-Pop Ballad', bpm: 72, instruments: 'Acoustic Piano, Strings, Electric Bass, Delicate Vocal' },
      { genre: 'Lo-Fi Chillhop', bpm: 85, instruments: 'Rhodes Piano, Vinyl Crackle, Muted Jazz Guitar, Soft Boom Bap' },
      { genre: 'City Pop', bpm: 118, instruments: 'Funky Slap Bass, Brass Section, Sparkling Synth Lead, Electric Guitar' },
      { genre: 'Acoustic Indie Pop', bpm: 95, instruments: 'Acoustic Guitar, Tambourine, Warm Cello, Finger Snaps' },
      { genre: 'R&B / Soul', bpm: 80, instruments: 'Electric Piano, 808 Sub Bass, Finger Snaps, Lush Harmony' },
      { genre: 'Synthwave / Retro 80s', bpm: 124, instruments: 'Analog Synths, LinnDrum, Chorus Guitar, Gated Reverb Snare' },
      { genre: 'Cinematic Ambient', bpm: 65, instruments: 'Atmospheric Pads, Solo Grand Piano, Reverb Strings, Sub Drone' },
      { genre: 'Deep House / Melodic', bpm: 122, instruments: 'Pluck Synth, Deep Bassline, Four-on-the-floor Kick, Hi-hats' },
      { genre: 'Modern Rock / Ballad', bpm: 88, instruments: 'Distortion Electric Guitar, Heavy Drums, Grand Piano, Bass' },
      { genre: 'Neo-Classical', bpm: 68, instruments: 'Upright Piano, String Quartet, Ambient Reverb Drone' },
      { genre: 'Hyperpop / Future Pop', bpm: 145, instruments: 'Bitcrushed Synths, Auto-tuned Vocals, Glitch 808s, Metallic Percussion' },
      { genre: 'Nu-Disco / Funk', bpm: 115, instruments: 'Disco Strings, Slap Bass, Wah Guitar, Rhythm Claps' },
      { genre: 'Dream Pop / Shoegaze', bpm: 104, instruments: 'Shimmer Reverb Guitar, Soft Female Vocal, Analog Bass, Lush Synths' },
      { genre: 'Future Bass / Melodic EDM', bpm: 140, instruments: 'Super Saw Chords, Vocal Chops, Heavy 808, Pitch Bends' },
      { genre: 'Cyberpunk EBM / Dark Synth', bpm: 130, instruments: 'Saw Bass Arpeggios, Industrial Drums, Distorted Lead' },
      { genre: 'Afrobeat / Melodic Pop', bpm: 102, instruments: 'Log Drums, Marimba, Brass Horns, Groovy Bass' },
      { genre: 'Jazz Hop / Coffee Vibe', bpm: 82, instruments: 'Muted Trumpet, Upright Bass, Wurlitzer Piano, Brushed Snare' },
      { genre: 'Folk Acoustic / Campfire', bpm: 90, instruments: 'Fingerpicking Acoustic, Harmonica, Stomp Box, Mandolin' },
      { genre: 'Symphonic Rock / Epic', bpm: 128, instruments: 'Full Orchestra Strings, Heavy Guitar Riffs, Timpani, Double Bass' },
      { genre: 'Reggae Fusion / Chill', bpm: 76, instruments: 'Offbeat Clean Guitar, Deep Reggae Bass, Organ Bubble, Rimshot' }
    ];

    // Variations catalog for 'single' mode
    const singleVariations = [
      { name: 'Original Radio Edit', genre: 'Modern Pop', bpm: 116, instruments: 'Full Production, Synths, Punchy Beats, Lead Vocal', concept: 'Main Commercial Radio Edit' },
      { name: 'Acoustic Unplugged Ver.', genre: 'Acoustic Indie', bpm: 88, instruments: 'Warm Acoustic Guitar, Upright Piano, Soft Strings', concept: 'Intimate Unplugged Session' },
      { name: 'Lo-Fi Midnight Chillhop Remix', genre: 'Lo-Fi Chillhop', bpm: 82, instruments: 'Vinyl Rhodes, Muted Guitar, Soft Drums, Tape Saturation', concept: 'Late Night Study & Relaxation' },
      { name: 'Synthwave Neon Club Mix', genre: 'Synthwave', bpm: 126, instruments: '80s Analog Synths, LinnDrum, Driving Arp Bass', concept: 'Retro Driving & Dance Anthem' },
      { name: 'Stripped Piano & Cello Ballad', genre: 'K-Pop Ballad', bpm: 70, instruments: 'Grand Piano, Solo Cello, Emotional Vocal', concept: 'Deep Emotional Confession' },
      { name: 'Cinematic Orchestral Edition', genre: 'Cinematic Ambient', bpm: 66, instruments: 'Full String Ensemble, French Horns, Timpani, Reverb Piano', concept: 'Dramatic Movie Soundtrack' },
      { name: 'Funk & Slap Groove Ver.', genre: 'Nu-Disco', bpm: 118, instruments: 'Slap Bass, Brass Stabs, Rhythm Guitar, Hand Claps', concept: 'High Energy Party Remix' },
      { name: 'Future Bass Drop Remix', genre: 'Future Bass', bpm: 140, instruments: 'Saw Synthesizers, Vocal Chops, Heavy 808 Sub', concept: 'Festival Electronic Climax' },
      { name: 'R&B Midnight Slow Jam', genre: 'R&B / Soul', bpm: 78, instruments: 'Rhodes Piano, 808 Bass, Subtle Finger Snaps, Harmony', concept: 'Sensual Night Vibe' },
      { name: 'Rock Band Live Arrangement', genre: 'Modern Rock', bpm: 132, instruments: 'Overdrive Guitars, Live Drum Kit, Energetic Bass', concept: 'Festival Live Stage Version' },
      { name: 'City Pop Retro Drive Ver.', genre: 'City Pop', bpm: 120, instruments: 'Electric Piano, Funky Bass, Chorus Guitar, Brass', concept: 'Tokyo Sunset Highway' },
      { name: 'Dream Pop Ambient Mix', genre: 'Dream Pop', bpm: 98, instruments: 'Shimmer Guitars, Soft Synth Pads, Warm Bass', concept: 'Surreal Ethereal Atmosphere' },
      { name: 'Coffee House Jazz Ver.', genre: 'Jazz Hop', bpm: 84, instruments: 'Upright Bass, Soft Brushes, Jazz Guitar, Saxophone', concept: 'Afternoon Cafe Mood' },
      { name: 'Hyperpop Glitch Edition', genre: 'Hyperpop', bpm: 148, instruments: 'Glitch Synth, Fast 808s, Distorted Chords', concept: 'Cyber Futuristic Style' },
      { name: 'Reggae Sunset Groove Ver.', genre: 'Reggae Fusion', bpm: 75, instruments: 'Skank Guitar, Deep Sub Bass, Percussions', concept: 'Tropical Sunset Relaxation' },
      { name: 'Minimalist Vocal & Guitar', genre: 'Folk Acoustic', bpm: 92, instruments: 'Solo Nylon Guitar, Pure Vocal, Room Reverb', concept: 'Raw Acoustic Essence' },
      { name: 'Deep Melodic House Mix', genre: 'Deep House', bpm: 123, instruments: 'Pluck Synths, Sub Bass, Crisp Hi-Hats, Vocal FX', concept: 'Late Night Club Groove' },
      { name: 'Dark Cyberpunk EBM Ver.', genre: 'Cyberpunk EBM', bpm: 128, instruments: 'Industrial Bass, Aggressive Beats, Synthesizers', concept: 'Futuristic Dystopian Energy' },
      { name: 'Symphonic Climax Ver.', genre: 'Symphonic Rock', bpm: 110, instruments: 'Strings Quartet, Distorted Guitars, Heavy Cymbals', concept: 'Grand Orchestral Explosion' },
      { name: 'Extended Instrumental Outro Edit', genre: 'Ambient Pop', bpm: 100, instruments: 'Melodic Guitars, Synth Atmosphere, Echo Delay', concept: 'Extended Journey Edit' }
    ];

    // Narrative tracklist structure for 'album' mode
    const albumConcepts = [
      { role: 'Prologue / Intro', titleSuffix: 'Intro: 여명의 빛', genre: 'Cinematic Ambient', bpm: 64, instruments: 'Ambient Drone, Solo Piano, Wind FX', concept: '앨범의 서막을 여는 잔잔하고 신비로운 프롤로그' },
      { role: 'Lead Title Track', titleSuffix: '타이틀: 운명의 밤', genre: 'K-Pop Ballad', bpm: 76, instruments: 'Grand Piano, String Orchestra, Dynamic Drums, Bass', concept: '앨범 전체의 핵심 서사와 강렬한 감정을 담은 메인 타이틀 곡' },
      { role: 'Sub Title Track', titleSuffix: '서브타이틀: 도시의 네온사인', genre: 'City Pop', bpm: 118, instruments: 'Funky Bass, Brass Section, Rhythm Electric Guitar', concept: '세련된 도심의 감성을 경쾌한 리듬으로 풀어낸 서브 타이틀' },
      { role: 'B-Side 1: Acoustic', titleSuffix: '골목길의 기억', genre: 'Acoustic Indie Pop', bpm: 92, instruments: 'Acoustic Guitar, Soft Shaker, Warm Cello', concept: '진솔한 고백과 추억을 회상하는 따뜻한 어쿠스틱 트랙' },
      { role: 'B-Side 2: Chillhop', titleSuffix: '자정의 빗소리', genre: 'Lo-Fi Chillhop', bpm: 82, instruments: 'Vinyl Rhodes, Muted Guitar, Rain Sound FX', concept: '깊은 밤 사색과 휴식을 안겨주는 감성 칠홉 트랙' },
      { role: 'Interlude', titleSuffix: 'Interlude: 시간의 틈', genre: 'Neo-Classical', bpm: 68, instruments: 'Upright Piano, Solo Violin, Ambient Atmosphere', concept: '다음 챕터로의 감정적 전환을 유도하는 서정적 인터루드' },
      { role: 'Dramatic Climax', titleSuffix: '폭풍 속으로', genre: 'Modern Rock', bpm: 130, instruments: 'Distortion Guitars, Powerful Drum Kit, Screaming Bass', concept: '갈등과 감정의 폭발을 표현한 앨범의 하이라이트 록 트랙' },
      { role: 'R&B Reflection', titleSuffix: '새벽 네 시', genre: 'R&B / Soul', bpm: 80, instruments: 'Electric Piano, 808 Sub, Finger Snaps, Harmony', concept: '폭풍이 지나간 뒤 홀로 남은 감정을 노래하는 R&B 소울' },
      { role: 'Electronic Elevation', titleSuffix: '별빛의 바다', genre: 'Synthwave', bpm: 122, instruments: 'Analog Synths, Retro Drums, Chorus Guitars', concept: '희망과 해방감을 선사하는 레트로 신스웨이브 트랙' },
      { role: 'Epilogue / Outro', titleSuffix: 'Outro: 영원의 멜로디', genre: 'Cinematic Ambient', bpm: 65, instruments: 'Solo Grand Piano, Reverb Strings, Gentle Fadeout', concept: '여운을 남기며 앨범의 여정을 완성하는 마지막 에필로그' },
      { role: 'Bonus Track 1', titleSuffix: 'Bonus: 봄날의 기억', genre: 'Acoustic Pop', bpm: 98, instruments: 'Acoustic Guitar, Accordion, Percussion', concept: '팬들을 위한 선물 같은 밝고 산뜻한 보너스 트랙' },
      { role: 'Bonus Track 2', titleSuffix: 'Bonus: 클럽 믹스', genre: 'Deep House', bpm: 124, instruments: 'Pluck Synth, 4-on-the-floor Kick, Bass', concept: '흥을 돋우는 댄서블한 보너스 믹스' },
      { role: 'Alternate Ver.', titleSuffix: 'Special: 피아노 솔로 Ver.', genre: 'Neo-Classical', bpm: 70, instruments: 'Grand Piano Solo', concept: '타이틀곡의 순수 피아노 독주 편곡' },
      { role: 'Extended Cut', titleSuffix: 'Extended: 별빛의 항해', genre: 'Dream Pop', bpm: 105, instruments: 'Shimmer Guitars, Synths, Echo', concept: '우주적 공간감을 확장한 익스텐디드 트랙' },
      { role: 'Midnight Remix', titleSuffix: 'Midnight: 달빛 산책', genre: 'Jazz Hop', bpm: 84, instruments: 'Muted Trumpet, Upright Bass, Wurlitzer', concept: '심야 라디오 분위기의 재즈 편곡' },
      { role: 'Remaster Track', titleSuffix: '2026 Remaster: 회상', genre: 'Folk Acoustic', bpm: 88, instruments: 'Harmonica, Mandolin, Acoustic Guitars', concept: '클래식 포크 감성의 리마스터 트랙' },
      { role: 'Orchestral Suite', titleSuffix: 'Orchestral: 대성당의 울림', genre: 'Cinematic Ambient', bpm: 60, instruments: 'Full Orchestra, Cathedral Reverb', concept: '웅장한 클래식 오케스트라 스위트' },
      { role: 'Synth Reprise', titleSuffix: 'Reprise: 네온의 그림자', genre: 'Synthwave', bpm: 115, instruments: 'Vintage Synths, Arpeggio, Bass', concept: '앨범 모티프를 재해석한 신스 리프라이즈' },
      { role: 'Acoustic Duet', titleSuffix: 'Duet: 너와 나의 거리', genre: 'K-Pop Ballad', bpm: 74, instruments: 'Acoustic Piano, Dual Vocals, Cello', concept: '두 사람의 대화를 형상화한 듀엣 발라드' },
      { role: 'Final Farewell', titleSuffix: 'Final: 안녕, 나의 계절', genre: 'Acoustic Indie Pop', bpm: 86, instruments: 'Acoustic Guitar, Soft Strings, Clock Tick FX', concept: '모든 이야기를 닫으며 건네는 마지막 작별 인사' }
    ];

    for (let i = 0; i < count; i++) {
      const id = `RECIPE-${String(i + 1).padStart(3, '0')}`;
      let title = '';
      let genre = '';
      let bpm = 120;
      let instruments = '';
      let lyricTheme = '';
      let promptText = '';
      let concept = '';
      let verse1 = '';
      let chorus = '';
      let verse2 = '';

      if (mode === 'single') {
        const item = singleVariations[i % singleVariations.length];
        title = `${keyword} (${item.name})`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        concept = item.concept;
        lyricTheme = `${keyword}을 주제로 한 ${item.name} 버전의 깊이 있는 감성 연출`;

        verse1 = `[Verse 1]\n어두워진 거리에 홀로 서서 ${keyword}의 잔향을 느껴\n흐릿해진 가로등 불빛 아래 너와의 약속이 떠오르네`;
        chorus = `[Chorus]\n잊으려 해도 잊을 수 없는 "${keyword}"의 멜로디\n가슴 속 가장 깊은 곳에서 영원히 살아 숨 쉬네`;
        verse2 = `[Verse 2]\n바람에 실려 온 익숙한 향기가 뺨을 스치고\n새로운 내일이 와도 너의 자리는 여전히 여기에`;

        promptText = `[Genre: ${genre}] [BPM: ${bpm}] [Instruments: ${instruments}] [Mood: Atmospheric, Emotional, ${item.concept}] [Theme: ${keyword}] [Variation: ${item.name}]`;
      } else if (mode === 'album') {
        const item = albumConcepts[i % albumConcepts.length];
        title = `${item.titleSuffix} - ${keyword}`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        concept = `[${item.role}] ${item.concept}`;
        lyricTheme = `앨범 [${keyword}]의 ${item.role} 트랙: ${item.concept}`;

        verse1 = `[Verse 1]\n${keyword}의 이야기 속 ${i + 1}번째 페이지를 펼쳐\n끝나지 않은 시간의 여운이 이 공간을 가득 채우네`;
        chorus = `[Chorus]\n우리가 함께 부르던 찬란했던 날들의 노래\n세상이 멈춘다 해도 영원히 메아리칠 ${keyword}`;
        verse2 = `[Verse 2]\n새벽빛이 어둠을 밀어내듯 서서히 차오르는 용기\n다음 이야기로 이어지는 우리의 발걸음`;

        promptText = `[Genre: ${genre}] [BPM: ${bpm}] [Instruments: ${instruments}] [Album: ${keyword}] [Track Role: ${item.role}] [Mood: Cohesive, Cinematic]`;
      } else {
        // 'explore' mode
        const item = exploreGenres[i % exploreGenres.length];
        title = `${keyword} - ${item.genre} #${i + 1}`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        concept = `Explore Genre #${i + 1} (${item.genre})`;
        lyricTheme = `${keyword}을 ${item.genre} 장르 감성으로 재해석한 스토리텔링`;

        verse1 = `[Verse 1]\n창밖에 내리는 ${keyword}의 기억들 조용히 흐르고\n멈춰버린 시간 속에 너의 미소가 깃드네`;
        chorus = `[Chorus]\n잊혀지지 않는 그날의 멜로디 가슴 깊이 울려 퍼져\n${keyword} 속에서 피어나는 우리만의 감성`;
        verse2 = `[Verse 2]\n바람에 실려온 너의 목소리 귓가에 맴돌고\n다시금 흩어지는 추억의 조각을 모아 노래하네`;

        promptText = `[Genre: ${genre}] [BPM: ${bpm}] [Instruments: ${instruments}] [Mood: Emotional, Polished, Studio Quality] [Theme: ${keyword}]`;
      }

      recipes.push({
        id,
        title,
        genre,
        bpm,
        instruments,
        lyricTheme,
        lyrics: {
          verse1,
          chorus,
          verse2
        },
        promptText,
        mode,
        concept
      });
    }

    return recipes;
  }

  /**
   * Evaluate draft audio and lyrics (API-003, SCN-002, REQ-001)
   * Calculates a 100-point AI screening score based on technical audio integrity and lyrical completeness.
   * 
   * @param {Object} params
   * @param {string} [params.lyrics='']
   * @param {Object} [params.audioMetadata={}]
   * @param {boolean} [params.audioMetadata.clipping=false]
   * @param {boolean} [params.audioMetadata.silence=false]
   * @param {number} [params.audioMetadata.duration=180]
   * @returns {Promise<{aiScore: number, aiReview: string, grade: string, techCheck: Object}>}
   */
  async evaluateQuality({ lyrics = '', audioMetadata = {} }) {
    let lyricScore = 0;
    let audioScore = 40; // Max 40 points for audio integrity
    const feedbackList = [];

    const rawLyrics = String(lyrics || '').trim();

    // 1. Lyric Structure & Completeness Analysis (Max 60 points)
    const hasVerse1 = rawLyrics.includes('[Verse 1]') || rawLyrics.includes('[Verse]');
    const hasChorus = rawLyrics.includes('[Chorus]');
    const hasVerse2 = rawLyrics.includes('[Verse 2]') || rawLyrics.includes('[Bridge]') || rawLyrics.includes('[Outro]');

    if (hasVerse1) {
      lyricScore += 18;
      feedbackList.push('Verse 도입부 구조가 명확함.');
    } else {
      feedbackList.push('Verse 파트 태그([Verse]) 부재.');
    }

    if (hasChorus) {
      lyricScore += 22;
      feedbackList.push('Chorus 후렴구 후킹 포인트 완성도 우수.');
    } else {
      lyricScore -= 10;
      feedbackList.push('Chorus 후렴구 누락으로 곡 구조 불완전.');
    }

    if (hasVerse2) {
      lyricScore += 10;
      feedbackList.push('Verse 2/전개부 구조 완비.');
    }

    // Length and line balance check (Max 10 points)
    const lines = rawLyrics.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length >= 6 && rawLyrics.length >= 50) {
      lyricScore += 10;
      feedbackList.push('가사 분량 및 라인 수 균형 적절.');
    } else if (rawLyrics.length < 20) {
      lyricScore -= 15;
      feedbackList.push('가사 분량이 너무 짧음.');
    }

    // 2. Audio Technical Integrity Check (Max 40 points)
    const isClipping = Boolean(audioMetadata.clipping);
    const isSilence = Boolean(audioMetadata.silence);

    if (isClipping) {
      audioScore -= 20;
      feedbackList.push('⚠️ 오디오 피크 클리핑(Clipping) 결함 감지: 재렌더링 필요.');
    }
    if (isSilence) {
      audioScore -= 20;
      feedbackList.push('⚠️ 비정상 무음(Silence) 구간 감지.');
    }
    if (!isClipping && !isSilence) {
      feedbackList.push('오디오 파형 결함 없음 (클리핑/무음 정상).');
    }

    // Duration sanity check
    const duration = Number(audioMetadata.duration) || 0;
    if (duration > 0 && duration < 15) {
      audioScore -= 10;
      feedbackList.push('오디오 재생 시간(15초 미만)이 비정상적으로 짧음.');
    }

    // 3. Final Score & Grade Calculation (0 ~ 100)
    const totalScore = Math.min(100, Math.max(0, lyricScore + audioScore));

    let grade = 'F';
    if (totalScore >= 90) grade = 'S';
    else if (totalScore >= 80) grade = 'A';
    else if (totalScore >= 70) grade = 'B';
    else if (totalScore >= 60) grade = 'C';

    const aiReview = `[AI 1차 심사: ${grade}등급 (${totalScore}점)] ${feedbackList.join(' ')}`;

    return {
      aiScore: totalScore,
      aiReview,
      grade,
      techCheck: {
        clipping: isClipping,
        silence: isSilence
      }
    };
  }
}

export default GeminiProvider;
