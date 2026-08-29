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
    /**
   * Structured generation via Google Gemini SDK (@google/genai)
   * @private
   */
  async _generateWithGeminiSdk({ keyword, count, mode }) {
    const prompt = `You are the Lead Music Director and Professional Songwriter of ZENION AI Music Studio.
Generate exactly ${count} distinct, highly creative, and complete commercial song recipes based on the keyword/theme: "${keyword}".
The planning mode is "${mode}".
- explore mode: Diverse genre exploration (City Pop, K-Pop Ballad, Lo-Fi Chillhop, Synthwave, R&B Soul, Acoustic Indie, Modern Rock, Nu-Disco, Deep House, etc.).
- single mode: Stylistic arrangement variations of a single core song (Original Radio Edit, Acoustic Unplugged, Lo-Fi Midnight, Synthwave Club, Stripped Piano, Cinematic Orchestral, etc.).
- album mode: Cohesive concept album narrative tracklist (Track 1: Prologue Intro, Track 2: Lead Title Track, Track 3: Sub Title Groove, ..., Final Track: Epilogue Outro).

CRITICAL REQUIREMENTS FOR SUNO AI OPTIMIZATION:
1. Every track MUST include professional Suno AI style prompt tags formatted as: "[Style Tags: {genre}, {tempo} bpm, {instruments}, {mood}, {vocal_type}]".
2. Lyrics MUST be full-scale, emotional, poetic Korean lyrics featuring complete song structure:
   - [Intro - Instrumental Vibe]
   - [Verse 1] (4-6 poetic lines)
   - [Pre-Chorus] (2-4 lines building tension)
   - [Chorus] (4-6 lines memorable main hook)
   - [Verse 2] (4-6 lines narrative continuation)
   - [Bridge] (3-4 lines emotional climax)
   - [Solo / Instrumental Break]
   - [Chorus] (Explosive full chorus)
   - [Outro] (Fading emotional finish)
   - [Fade Out]`;

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
              intro: { type: Type.STRING },
              verse1: { type: Type.STRING },
              preChorus: { type: Type.STRING },
              chorus: { type: Type.STRING },
              verse2: { type: Type.STRING },
              bridge: { type: Type.STRING },
              outro: { type: Type.STRING }
            },
            required: ['verse1', 'chorus', 'verse2']
          },
          sunoStylePrompt: { type: Type.STRING },
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
        temperature: 0.75
      }
    });

    const parsed = JSON.parse(response.text);
    if (Array.isArray(parsed)) {
      return parsed.map((item, index) => {
        const lyr = item.lyrics || {};
        const fullLyrics = [
          lyr.intro ? `[Intro]\n${lyr.intro}` : '[Intro - Instrumental]',
          `[Verse 1]\n${lyr.verse1 || ''}`,
          lyr.preChorus ? `[Pre-Chorus]\n${lyr.preChorus}` : '',
          `[Chorus]\n${lyr.chorus || ''}`,
          `[Verse 2]\n${lyr.verse2 || ''}`,
          lyr.bridge ? `[Bridge]\n${lyr.bridge}` : '',
          '[Instrumental Break]',
          `[Chorus]\n${lyr.chorus || ''}`,
          lyr.outro ? `[Outro]\n${lyr.outro}` : '[Outro]\n[Fade Out]'
        ].filter(Boolean).join('\n\n');

        const stylePrompt = item.sunoStylePrompt || `${item.genre || 'City Pop'}, ${item.bpm || 118} bpm, ${item.instruments || 'synths, bass'}, melodic, emotional, high quality`;

        return {
          id: item.id || `RECIPE-${String(index + 1).padStart(3, '0')}`,
          title: item.title || `${keyword} - Track #${index + 1}`,
          genre: item.genre || 'Pop',
          bpm: Number(item.bpm) || 120,
          instruments: item.instruments || 'Piano, Drums, Bass, Synthesizer',
          lyricTheme: item.lyricTheme || `${keyword} 스토리텔링`,
          lyrics: lyr,
          fullLyrics,
          sunoStylePrompt: stylePrompt,
          promptText: item.promptText || `[Genre: ${item.genre || 'Pop'}] [BPM: ${item.bpm || 120}] [Theme: ${keyword}] [Style: ${stylePrompt}]`,
          mode: mode,
          concept: item.concept || `${mode} Track ${index + 1}`
        };
      });
    }

    return null;
  }

  /**
   * High quality offline style & lyrics recipe generator supporting Suno AI tags, 3 modes and 1~20 tracks
   * @private
   */
  _generateOfflineRecipes({ keyword, count, mode }) {
    const recipes = [];

    // Genre catalog for 'explore' mode with rich Suno AI prompt tags & lyrics
    const exploreCatalog = [
      {
        genre: '80s Japanese City Pop',
        bpm: 118,
        instruments: 'Funky Slap Bass, Brass Horn Section, Sparkling FM Synths, Clean Electric Guitar, Acoustic Drums',
        vocal: 'Female Lead, Warm & Bright Velvet Tone',
        mood: 'Nostalgic, Romantic, Groovy, Tokyo Night Drive',
        sunoStyle: '80s Japanese City Pop, funk, slap bass, lush brass, sparkling synths, 118 bpm, groovy, nostalgic female vocal, studio quality',
        verse1: `네온사인 물든 밤거리 위로\n조용히 번지는 젖은 아스팔트 불빛\n룸미러 속 스쳐가는 도시의 그림자\n잊혀진 라디오 멜로디가 귓가에 흘러`,
        preChorus: `차창을 내리면 불어오는 서늘한 바람\n마음 한구석에 숨겨둔 너의 기억을 깨워`,
        chorus: `비 오는 날의 네온사인 시티팝\n밤하늘을 수놓은 오색빛깔 우리들의 추억\n끝나지 않을 것 같던 그 여름밤의 드라이브\n이 도시에 영원히 울려 퍼지는 노래`,
        verse2: `신호등이 깜빡이는 교차로에 서서\n너와 함께 걷던 그 골목길을 바라봐\n빗방울이 유리창을 토닥일 때마다\n선명해지는 너의 따스했던 미소`,
        bridge: `멈춰버린 시간도, 흩어진 계절도\n이 밤의 그루브 속에 모두 다시 살아나`,
        outro: `흐르는 멜로디에 실려 보내는 안녕\n네온 불빛 속으로 아련히 사라지는 밤\n[Fade Out]`
      },
      {
        genre: 'Emotional K-Pop Ballad',
        bpm: 72,
        instruments: 'Grand Piano, 24-Piece String Orchestra, Acoustic Bass, Delicate Drum Brush, Cello Solo',
        vocal: 'Airy & Powerful Korean Emotional Vocal, Dramatic High Notes',
        mood: 'Heartbreaking, Melancholic, Tearful, Cinematic',
        sunoStyle: 'Korean emotional ballad, grand piano, lush string orchestra, dramatic, 72 bpm, heartfelt, powerful vocal, acoustic cello, cinematic',
        verse1: `창밖으로 하나둘 떨어지는 빗방울 소리\n텅 빈 방 안을 가득 채우는 서늘한 침묵\n서랍 깊은 곳에 묻어둔 너의 편지 속\n여전히 온기가 남아있는 우리들의 날들`,
        preChorus: `시간이 흐르면 잊혀질 거라 믿었어\n하지만 계절이 돌아올 때마다 가슴이 저려와`,
        chorus: `너를 사랑했던 그 모든 순간들이\n비가 되어 가슴 깊은 곳으로 흘러내려\n아무리 지우려 해도 지워지지 않는 사람\n눈물로 써 내려간 나의 마지막 고백`,
        verse2: `함께 걷던 우산 아래 나누었던 숨결\n작은 온기마저 소중했던 그 계절의 끝\n이제는 혼자 남아 비를 맞으며\n너 없는 세상에 홀로 익숙해져 가`,
        bridge: `다시 한 번만 너의 이름을 부를 수 있다면\n내 모든 걸 버려서라도 널 안아줄 텐데`,
        outro: `빗소리에 묻어둔 못다 한 이야기\n안녕, 나의 찬란했던 사랑아\n[Slow Fade Out]`
      },
      {
        genre: 'Lo-Fi Midnight Chillhop',
        bpm: 84,
        instruments: 'Fender Rhodes Electric Piano, Vinyl Crackle, Muted Jazz Guitar, Soft Boom-Bap Drums, Rain Ambient FX',
        vocal: 'Warm Whispering Male/Female Vocal, Lo-Fi Tape Saturation',
        mood: 'Cozy, Relaxing, Melancholy, Late Night Study',
        sunoStyle: 'Lofi chillhop, warm rhodes piano, vinyl crackle, muted jazz guitar, soft drums, rain sounds, cozy, 84 bpm, late night, relaxing',
        verse1: `새벽 두 시, 책상 위 커피잔의 온기\n창문을 두드리는 차분한 빗소리 리듬\n로파이 비트 위에 얹어보는 조용한 생각들\n지나간 하루의 무게를 천천히 내려놓네`,
        preChorus: `턴테이블 바늘이 긁히는 따스한 소리\n복잡했던 마음이 서서히 녹아내리고`,
        chorus: `자정의 빗소리와 함께 흐르는 칠홉\n어두운 방 안을 밝히는 은은한 스탠드 불빛\n숨 가빴던 세상에서 벗어나 잠시 쉬어가\n이 밤의 온도는 너와 나의 멜로디`,
        verse2: `벽시계 초침 소리마저 리듬이 되는 순간\n헤드폰 너머로 번지는 나른한 베이스라인\n적어두지 못한 일기장의 마지막 줄에\n오늘의 감정을 소박하게 새겨두네`,
        bridge: `어지러운 내일 걱정은 창밖에 두고\n지금 이 멜로디에 온전히 나를 맡겨`,
        outro: `커피 한 모금과 깊어지는 새벽\n빗소리 속으로 부드럽게 흩어지네\n[Vinyl Crackle & Rain Fade Out]`
      },
      {
        genre: '80s Synthwave / Retrowave',
        bpm: 124,
        instruments: 'Analog Juno Synths, LinnDrum, Driving Arpeggiated Bass, Chorus Guitar, Gated Reverb Snare',
        vocal: 'Vocoder & Reverb Lead Vocal, Cybernetic 80s Vibe',
        mood: 'Futuristic, High Energy, Neon Highway, Cyberpunk',
        sunoStyle: '80s synthwave, retrowave, analog juno synth, arpeggiated bass, linndrum, 124 bpm, neon drive, gated reverb, cybernetic, energetic',
        verse1: `보랏빛 네온이 번지는 끝없는 사이버 고속도로\n가속 페달을 밟으며 어둠을 뚫고 질주해\n디지털 계기판 위에 떠오르는 너의 좌표\n80년대 레트로 신스가 심장을 두드려`,
        preChorus: `사이버 시티의 밤은 잠들지 않고\n전파를 타고 흐르는 우리의 시그널`,
        chorus: `네온 하이웨이를 달리는 레트로웨이브\n시속 140km로 날아가는 아날로그 신스 사운드\n과거와 미래가 교차하는 레이저 불빛 아래\n우리의 드라이브는 끝나지 않아`,
        verse2: `사이드미러 너머로 멀어지는 크롬빛 빌딩숲\n비트에 맞춰 요동치는 묵직한 아르페지오 베이스\n시간의 왜곡을 넘어 너에게 닿을 때까지\n이 밤의 에너지는 멈추지 않아`,
        bridge: `[Synth Solo]\n(Dramatic Analog Arpeggio & Gated Snare Burst)`,
        outro: `네온의 끝자락에서 맞이하는 여명\n디지털 지평선 너머로 사라지는 밤\n[Laser Synth Fade Out]`
      },
      {
        genre: 'Modern R&B / Neo-Soul',
        bpm: 80,
        instruments: 'Electric Piano, Deep 808 Sub-Bass, Smooth Finger Snaps, Lush Vocal Harmonies, Clean Strat Guitar',
        vocal: 'Sensual, Smooth Falsetto, Soulful Vocal Runs',
        mood: 'Groovy, Sensual, Intimate, Midnight Candlelight',
        sunoStyle: 'Modern R&B, neo-soul, rhodes electric piano, deep 808 bass, finger snaps, lush harmonies, 80 bpm, sensual, smooth falsetto, groove',
        verse1: `촛불 하나 켜둔 채 마주 앉은 새벽\n와인잔에 비친 너의 깊은 눈빛\n말하지 않아도 전해지는 공기의 떨림\n부드러운 소울 그루브가 우리 사이를 감싸네`,
        preChorus: `손끝이 닿을 때 전해지는 전율\n숨소리마저 완벽한 화음이 되는 밤`,
        chorus: `새벽 네 시, 우리만의 네오 소울\n깊은 베이스라인처럼 심장에 스며드는 너\n아침이 오지 않길 바라는 이 순간\n영원히 머물고 싶은 달콤한 멜로디`,
        verse2: `창가에 맺힌 이슬처럼 투명한 감정들\n감미로운 건반 소리에 너를 맡겨봐\n세상 모든 소음이 멈춘 이 작은 방에서\n우리의 사랑은 가장 깊은 빛을 내`,
        bridge: `Baby, don't let this groove fade away\n이 밤이 끝날 때까지 널 놓지 않을게`,
        outro: `속삭이는 애드리브와 부드러운 하모니\n아침 햇살이 스밀 때까지\n[Smooth R&B Fade Out]`
      },
      {
        genre: 'Acoustic Indie Folk Pop',
        bpm: 95,
        instruments: 'Steel-String Acoustic Guitar, Warm Cello, Tambourine, Hand Claps, Glockenspiel, Upright Bass',
        vocal: 'Pure & Organic Singer-Songwriter Vocal, Natural Room Acoustics',
        mood: 'Heartwarming, Breeze, Sunshine, Cozy Cabin',
        sunoStyle: 'Acoustic indie folk pop, steel string acoustic guitar, warm cello, tambourine, hand claps, 95 bpm, singer-songwriter, organic, heartwarming',
        verse1: `따스한 햇살이 비추는 작은 옥상 테라스\n어쿠스틱 기타를 품에 안고 튕기는 첫 음\n바람결에 실려 온 풀내음과 커피 향기\n소박하지만 눈부신 우리들의 일상`,
        preChorus: `특별하지 않아도 좋아\n너와 함께 웃을 수 있다면`,
        chorus: `바람 부는 날의 어쿠스틱 포크 송\n통기타 멜로디에 실어 보내는 소소한 행복\n어깨를 나란히 맞대고 흥얼거리는 노래\n세상 가장 따뜻한 우리의 봄날`,
        verse2: `골목길을 지나가는 사람들의 발걸음\n벽에 걸린 낡은 사진 속 다정한 미소\n시간이 천천히 흐르는 이 오후에\n너를 위한 작은 연주를 들려줄게`,
        bridge: `어려운 말 대신 건네는 따스한 멜로디\n언제나 네 곁에 머물겠다는 약속`,
        outro: `통기타 스트로크 소리와 함께 남는 미소\n라라라 노래하며 걷는 우리들의 길\n[Gentle Acoustic Fade Out]`
      }
    ];

    // Single variations catalog
    const singleCatalog = [
      { name: 'Original Radio Edit', genre: 'Modern Pop', bpm: 116, instruments: 'Full Production, Synths, Punchy Beats', sunoStyle: 'Modern pop, radio edit, punchy beats, sparkling synths, 116 bpm, catchy commercial melody' },
      { name: 'Acoustic Unplugged Ver.', genre: 'Acoustic Indie', bpm: 88, instruments: 'Warm Acoustic Guitar, Upright Piano', sunoStyle: 'Acoustic indie, warm acoustic guitar, upright piano, 88 bpm, intimate unplugged session' },
      { name: 'Lo-Fi Midnight Chillhop Remix', genre: 'Lo-Fi Chillhop', bpm: 82, instruments: 'Vinyl Rhodes, Muted Guitar', sunoStyle: 'Lofi chillhop, vinyl rhodes, muted guitar, 82 bpm, midnight chill remix, relaxing' },
      { name: 'Synthwave Neon Club Mix', genre: 'Synthwave', bpm: 126, instruments: '80s Analog Synths, LinnDrum', sunoStyle: '80s synthwave, driving arpeggio bass, linndrum, 126 bpm, neon club mix, energetic' },
      { name: 'Stripped Piano & Cello Ballad', genre: 'K-Pop Ballad', bpm: 70, instruments: 'Grand Piano, Solo Cello', sunoStyle: 'Korean emotional ballad, grand piano, solo cello, 70 bpm, heartfelt stripped ballad' }
    ];

    // Album narrative catalog
    const albumCatalog = [
      { role: 'Prologue / Intro', titleSuffix: 'Intro: 여명의 빛', genre: 'Cinematic Ambient', bpm: 64, instruments: 'Ambient Drone, Solo Piano', sunoStyle: 'Cinematic ambient, solo piano, atmospheric drone, 64 bpm, prologue intro' },
      { role: 'Lead Title Track', titleSuffix: '타이틀: 운명의 밤', genre: 'Emotional K-Pop Ballad', bpm: 76, instruments: 'Grand Piano, Full Strings', sunoStyle: 'Korean emotional ballad, grand piano, lush string orchestra, 76 bpm, powerful lead title track' },
      { role: 'Sub Title Track', titleSuffix: '서브타이틀: 도시의 네온사인', genre: '80s Japanese City Pop', bpm: 118, instruments: 'Funky Bass, Brass Section', sunoStyle: '80s city pop, funk slap bass, brass, 118 bpm, groovy sub title track' },
      { role: 'B-Side 1: Acoustic', titleSuffix: '골목길의 기억', genre: 'Acoustic Indie Folk Pop', bpm: 92, instruments: 'Acoustic Guitar, Warm Cello', sunoStyle: 'Acoustic indie folk, steel string guitar, cello, 92 bpm, cozy b-side' },
      { role: 'Epilogue / Outro', titleSuffix: 'Outro: 영원의 멜로디', genre: 'Cinematic Ambient', bpm: 65, instruments: 'Solo Grand Piano, Strings', sunoStyle: 'Cinematic ambient, solo piano, string quartet, 65 bpm, epilogue outro, fade out' }
    ];

    for (let i = 0; i < count; i++) {
      const id = `RECIPE-${String(i + 1).padStart(3, '0')}`;
      let title = '';
      let genre = '';
      let bpm = 120;
      let instruments = '';
      let sunoStyle = '';
      let lyricTheme = '';
      let concept = '';
      let verse1 = '';
      let preChorus = '';
      let chorus = '';
      let verse2 = '';
      let bridge = '';
      let outro = '';

      if (mode === 'single') {
        const item = singleCatalog[i % singleCatalog.length];
        const base = exploreCatalog[0];
        title = `${keyword} (${item.name})`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        sunoStyle = item.sunoStyle;
        concept = `[Single Variation] ${item.name}`;
        lyricTheme = `${keyword}의 ${item.name} 감성 편곡`;

        verse1 = base.verse1;
        preChorus = base.preChorus;
        chorus = base.chorus;
        verse2 = base.verse2;
        bridge = base.bridge;
        outro = base.outro;
      } else if (mode === 'album') {
        const item = albumCatalog[i % albumCatalog.length];
        const base = exploreCatalog[i % exploreCatalog.length];
        title = `${item.titleSuffix} - ${keyword}`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        sunoStyle = item.sunoStyle;
        concept = `[${item.role}] ${item.titleSuffix}`;
        lyricTheme = `앨범 [${keyword}]의 ${item.role} 트랙`;

        verse1 = base.verse1;
        preChorus = base.preChorus;
        chorus = base.chorus;
        verse2 = base.verse2;
        bridge = base.bridge;
        outro = base.outro;
      } else {
        const template = exploreCatalog[i % exploreCatalog.length];
        title = `${keyword} - ${template.genre} #${i + 1}`;
        genre = template.genre;
        bpm = template.bpm;
        instruments = template.instruments;
        sunoStyle = template.sunoStyle;
        concept = `Explore Variation #${i + 1} (${genre})`;
        lyricTheme = `${keyword}을 주제로 한 ${template.genre} 완성형 음악 스토리텔링`;

        verse1 = template.verse1;
        preChorus = template.preChorus;
        chorus = template.chorus;
        verse2 = template.verse2;
        bridge = template.bridge;
        outro = template.outro;
      }

      const sunoStylePrompt = `[Style Tags: ${sunoStyle}]`;
      const fullLyrics = [
        `[Intro - ${instruments.split(',')[0]} & Groove]`,
        `[Verse 1]\n${verse1}`,
        preChorus ? `[Pre-Chorus]\n${preChorus}` : '',
        `[Chorus]\n${chorus}`,
        `[Verse 2]\n${verse2}`,
        bridge ? `[Bridge]\n${bridge}` : '',
        `[Instrumental Break - ${instruments.split(',')[1] || 'Solo'}]`,
        `[Chorus]\n${chorus}`,
        `[Outro]\n${outro}`
      ].filter(Boolean).join('\n\n');

      const promptText = `[Genre: ${genre}] [BPM: ${bpm}] [Suno Style: ${sunoStyle}] [Theme: ${keyword}]`;

      recipes.push({
        id,
        title,
        genre,
        bpm,
        instruments,
        lyricTheme,
        lyrics: {
          intro: `[Intro - ${instruments.split(',')[0]}]`,
          verse1: `[Verse 1]\n${verse1}`,
          preChorus: preChorus ? `[Pre-Chorus]\n${preChorus}` : '',
          chorus: `[Chorus]\n${chorus}`,
          verse2: `[Verse 2]\n${verse2}`,
          bridge: bridge ? `[Bridge]\n${bridge}` : '',
          outro: `[Outro]\n${outro}`
        },
        fullLyrics,
        sunoStylePrompt,
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
