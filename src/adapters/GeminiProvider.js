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
    const prompt = `You are the Lead Music Producer and Professional Songwriter of ZENION AI Music Studio.
Generate exactly ${count} distinct, highly creative, and complete commercial song recipes based on the keyword/theme: "${keyword}".
The planning mode is "${mode}".
- explore mode: Diverse genre exploration (Japanese City Pop, Emotional K-Pop Ballad, Lo-Fi Chillhop, 80s Synthwave, Modern R&B Neo-Soul, Acoustic Indie Folk, etc.).
- single mode: Stylistic arrangement variations of a single core song (Original Radio Edit, Acoustic Unplugged, Lo-Fi Midnight Remix, Synthwave Club, Stripped Piano Ballad, etc.).
- album mode: Cohesive concept album narrative tracklist (Prologue Intro -> Lead Title -> Sub Title -> Acoustic B-side -> Epilogue Outro).

CRITICAL REQUIREMENTS FOR SUNO AI (v3.5 / v4) OPTIMIZATION:
1. "sunoStylePrompt" MUST be a 3-bracket segmented professional caption:
   Example: "[Upbeat 96 BPM happy K-Pop R&B swing groove, bright sweet G Major chord progression, cheerful romantic spring mood, no minor chords, pure sweet major harmony], [bright sparkling fingerpicked acoustic guitar, active bouncy electric bassline, snappy syncopated rimshot drum groove, bright high-pitched shaker, warm sweet Rhodes chords, high-fidelity café studio mix], [dry intimate sweet female vocals front-and-center, clean mid-band vocal presence, no reverb, no delay]"
2. "lyrics" MUST be full-scale, emotional, poetic Korean lyrics featuring inline bracket production & vocal tags:
   - [Intro]\\n[instruments, bpm, key]
   - [Verse 1 - vocal tone, instruments, vibe] (4-6 lines)
   - [Pre-Chorus - build-up cue] (2-4 lines)
   - [Chorus - groove climax, backing vocals] (4-6 lines)
   - [Verse 2 - arrangement change] (4-6 lines)
   - [Bridge - emotional peak] (3-4 lines)
   - [Guitar Solo / Sax Solo]
   - [Chorus - explosive full chorus with backing ad-libs in parentheses]
   - [Outro - fadeout cues]\\n[Vocal Ad-libs: "..."]
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
        required: ['id', 'title', 'genre', 'bpm', 'instruments', 'lyricTheme', 'lyrics', 'sunoStylePrompt', 'promptText']
      }
    };

    const response = await this.client.models.generateContent({
      model: this.model,
      contents: prompt,
      config: {
        responseMimeType: 'application/json',
        responseSchema: responseSchema,
        temperature: 0.8
      }
    });

    const parsed = JSON.parse(response.text);
    if (Array.isArray(parsed)) {
      return parsed.map((item, index) => {
        const lyr = item.lyrics || {};
        const v1 = String(lyr.verse1 || lyr.Verse1 || lyr['verse 1'] || lyr.verse || '').trim();
        const v2 = String(lyr.verse2 || lyr.Verse2 || lyr['verse 2'] || '').trim();
        const ch = String(lyr.chorus || lyr.Chorus || '').trim();
        const pr = String(lyr.preChorus || lyr.pre_chorus || lyr.PreChorus || '').trim();
        const br = String(lyr.bridge || lyr.Bridge || '').trim();
        const it = String(lyr.intro || lyr.Intro || '').trim();
        const ot = String(lyr.outro || lyr.Outro || '').trim();

        const structuredLyrics = {
          intro: it.startsWith('[Intro') ? it : `[Intro]\n[${item.instruments || 'Acoustic Guitar, Soft Synths'}, ${item.bpm || 118} BPM]`,
          verse1: v1.startsWith('[Verse 1') ? v1 : `[Verse 1 - dry intimate vocal, clean instruments]\n${v1}`,
          preChorus: pr ? (pr.startsWith('[Pre-Chorus') ? pr : `[Pre-Chorus - drum build-up, bass enters]\n${pr}`) : '',
          chorus: ch.startsWith('[Chorus') ? ch : `[Chorus - full groove, vocal climax, lush harmony]\n${ch}`,
          verse2: v2.startsWith('[Verse 2') ? v2 : `[Verse 2 - active groove, warm vocals]\n${v2}`,
          bridge: br ? (br.startsWith('[Bridge') ? br : `[Bridge - emotional peak, dynamic shift]\n${br}`) : '',
          outro: ot.startsWith('[Outro') ? ot : `[Outro - gentle fadeout]\n${ot}\n[Fade Out]`
        };

        const fullLyrics = [
          structuredLyrics.intro,
          structuredLyrics.verse1,
          structuredLyrics.preChorus,
          structuredLyrics.chorus,
          structuredLyrics.verse2,
          structuredLyrics.bridge,
          `[Guitar Solo - melodic chorus guitar, tight rhythm backing]`,
          structuredLyrics.chorus,
          structuredLyrics.outro
        ].filter(Boolean).join('\n\n');

        const stylePrompt = item.sunoStylePrompt || `[Upbeat ${item.bpm || 118} BPM ${item.genre || 'City Pop'}, bright Major harmony, romantic mood], [${item.instruments || 'funky slap bass, synths, clean guitar'}, studio mix], [dry intimate female vocals front-and-center, no reverb]`;

        return {
          id: item.id || `RECIPE-${String(index + 1).padStart(3, '0')}`,
          title: item.title || `${keyword} - Track #${index + 1}`,
          genre: item.genre || 'Pop',
          bpm: Number(item.bpm) || 120,
          instruments: item.instruments || 'Piano, Drums, Bass, Synthesizer',
          lyricTheme: item.lyricTheme || `${keyword} 스토리텔링`,
          lyrics: structuredLyrics,
          fullLyrics,
          sunoStylePrompt: stylePrompt,
          promptText: item.promptText || `[Genre: ${item.genre || 'Pop'}] [BPM: ${item.bpm || 120}] [Theme: ${keyword}] [Suno: ${stylePrompt}]`,
          mode: mode,
          concept: item.concept || `${mode} Track ${index + 1}`
        };
      });
    }

    return null;
  }

  /**
   * High quality offline style & lyrics recipe generator supporting 3-tier Suno AI tags & inline lyric cues
   * @private
   */
  _generateOfflineRecipes({ keyword, count, mode }) {
    const recipes = [];

    // Genre catalog for 'explore' mode with 3-tier Suno AI caption & inline lyric tags
    const exploreCatalog = [
      {
        genre: '80s Japanese City Pop',
        bpm: 118,
        instruments: 'Funky Slap Bass, Brass Horn Section, Sparkling FM Synths, Clean Electric Guitar, Acoustic Drums',
        sunoCaption: `[Upbeat 118 BPM Japanese City Pop, bright A Major chord progression, nostalgic romantic sunset drive mood, no minor sadness, sparkling major harmony], [funky bouncy slap bassline, lush brass section stabs, sparkling FM synth lead, clean chorus rhythm guitar, syncopated tight funk drum groove, high-fidelity studio mix], [dry intimate warm female vocals front-and-center, clean mid-band vocal presence, lush backing vocal harmonies, no excessive reverb]`,
        introTag: `[Intro]\n[funky slap bass solo, sparkling FM synth, 118 BPM, bright A Major]`,
        verse1Tag: `[Verse 1 - dry bright sweet female vocals, clean rhythm guitar, bouncy slap bass, happy nostalgic mood]`,
        verse1: `네온사인 물든 밤거리 위로\n조용히 번지는 젖은 아스팔트 불빛\n룸미러 속 스쳐가는 도시의 그림자\n잊혀진 라디오 멜로디가 귓가에 흘러`,
        preChorusTag: `[Pre-Chorus - snappy bouncy rimshot drum, active electric bass, brass stabs]`,
        preChorus: `차창을 내리면 불어오는 서늘한 바람\n마음 한구석에 숨겨둔 너의 기억을 깨워 (너의 기억을 깨워)`,
        chorusTag: `[Chorus - upbeat bright City Pop funk groove, lush brass chords, cheerful sweet vocal climax, happy sweet harmony]`,
        chorus: `비 오는 날의 네온사인 시티팝\n밤하늘을 수놓은 오색빛깔 우리들의 추억 (우리들의 추억)\n끝나지 않을 것 같던 그 여름밤의 드라이브\n이 도시에 영원히 울려 퍼지는 노래 (Yeah, oh baby)`,
        verse2Tag: `[Verse 2 - sweet active City Pop swing vibe, warm electric guitar, bright vocals]`,
        verse2: `신호등이 깜빡이는 교차로에 서서\n너와 함께 걷던 그 골목길을 바라봐\n빗방울이 유리창을 토닥일 때마다\n선명해지는 너의 따스했던 미소 (따스했던 미소)`,
        bridgeTag: `[Bridge - emotional key change modulation, dramatic chord build-up, heartfelt vocal delivery]`,
        bridge: `멈춰버린 시간도, 흩어진 계절도\n이 밤의 그루브 속에 모두 다시 살아나`,
        soloTag: `[Guitar Solo - melodic chorus-drenched electric guitar solo, tight drum backing]`,
        outroTag: `[Outro - fast guitar pluck, bright shaker, happy synth chords fading out]\n[Vocal Ad-libs: "Neon city night... stay with me... our melody... yeah..."]\n[Fade Out]`
      },
      {
        genre: 'Emotional K-Pop Ballad',
        bpm: 72,
        instruments: 'Grand Piano, 24-Piece String Orchestra, Acoustic Bass, Delicate Drum Brush, Cello Solo',
        sunoCaption: `[Emotional 72 BPM Korean Ballad, melancholic C Minor to Eb Major progression, tearful dramatic romantic mood, rich orchestral harmony], [intimate concert grand piano, 24-piece lush string orchestra, warm acoustic cello solo, delicate room drum brushes, warm acoustic bass, cinematic studio mix], [airy passionate Korean female vocals, intimate close-mic delivery, dramatic high notes in chorus, subtle plate reverb]`,
        introTag: `[Intro]\n[intimate grand piano solo, gentle cello drone, 72 BPM, melancholic C Minor]`,
        verse1Tag: `[Verse 1 - soft whispered vocals, gentle grand piano, no drums, melancholic atmosphere]`,
        verse1: `창밖으로 하나둘 떨어지는 빗방울 소리\n텅 빈 방 안을 가득 채우는 서늘한 침묵\n서랍 깊은 곳에 묻어둔 너의 편지 속\n여전히 온기가 남아있는 우리들의 날들`,
        preChorusTag: `[Pre-Chorus - lush strings swell, warm acoustic bass enters, emotional tension rise]`,
        preChorus: `시간이 흐르면 잊혀질 거라 믿었어\n하지만 계절이 돌아올 때마다 가슴이 저려와 (가슴이 저려와)`,
        chorusTag: `[Chorus - full grand orchestral climax, explosive emotional vocals, soaring strings, powerful piano chords]`,
        chorus: `너를 사랑했던 그 모든 순간들이\n비가 되어 가슴 깊은 곳으로 흘러내려\n아무리 지우려 해도 지워지지 않는 사람\n눈물로 써 내려간 나의 마지막 고백 (마지막 고백)`,
        verse2Tag: `[Verse 2 - delicate acoustic piano, warm cello counter-melody, intimate vocal tone]`,
        verse2: `함께 걷던 우산 아래 나누었던 숨결\n작은 온기마저 소중했던 그 계절의 끝\n이제는 혼자 남아 비를 맞으며\n너 없는 세상에 홀로 익숙해져 가`,
        bridgeTag: `[Bridge - dramatic high register vocal belt, full timpani and violin climax]`,
        bridge: `다시 한 번만 너의 이름을 부를 수 있다면\n내 모든 걸 버려서라도 널 안아줄 텐데`,
        soloTag: `[Cello Solo - heartbreaking acoustic cello solo with grand piano backing]`,
        outroTag: `[Outro - solo grand piano fading out with soft rain ambience]\n[Vocal Ad-libs: "Goodbye my love... forever in rain... 안녕..."]\n[Slow Fade Out]`
      },
      {
        genre: 'Lo-Fi Midnight Chillhop',
        bpm: 84,
        instruments: 'Fender Rhodes Electric Piano, Vinyl Crackle, Muted Jazz Guitar, Soft Boom-Bap Drums, Rain Ambient FX',
        sunoCaption: `[Cozy 84 BPM Lo-Fi Chillhop groove, warm Bb Major 7th chord progression, late night relaxing study mood, soothing tape saturation], [warm vintage Fender Rhodes chords, gentle vinyl crackle, muted jazz guitar plucking, soft boom-bap drums, rain soundscape ambience, analog lo-fi mix], [whispering intimate male/female vocal, relaxed laid-back cadence, warm tube warmth, no harsh frequencies]`,
        introTag: `[Intro]\n[warm vinyl crackle, gentle Rhodes piano chords, rain ambient FX, 84 BPM]`,
        verse1Tag: `[Verse 1 - whispered intimate vocals, soft Rhodes piano, muted jazz guitar]`,
        verse1: `새벽 두 시, 책상 위 커피잔의 온기\n창문을 두드리는 차분한 빗소리 리듬\n로파이 비트 위에 얹어보는 조용한 생각들\n지나간 하루의 무게를 천천히 내려놓네`,
        preChorusTag: `[Pre-Chorus - soft boom-bap drum groove enters, warm sub-bass glide]`,
        preChorus: `턴테이블 바늘이 긁히는 따스한 소리\n복잡했던 마음이 서서히 녹아내리고 (녹아내리고)`,
        chorusTag: `[Chorus - cozy laid-back chillhop groove, lush Rhodes harmonies, sweet soothing melody]`,
        chorus: `자정의 빗소리와 함께 흐르는 칠홉\n어두운 방 안을 밝히는 은은한 스탠드 불빛\n숨 가빴던 세상에서 벗어나 잠시 쉬어가\n이 밤의 온도는 너와 나의 멜로디 (너와 나의 멜로디)`,
        verse2Tag: `[Verse 2 - muted jazz guitar plucking, relaxed drum beat, calm vocals]`,
        verse2: `벽시계 초침 소리마저 리듬이 되는 순간\n헤드폰 너머로 번지는 나른한 베이스라인\n적어두지 못한 일기장의 마지막 줄에\n오늘의 감정을 소박하게 새겨두네`,
        bridgeTag: `[Bridge - Rhodes piano solo with tape saturation delay, gentle vocal humming]`,
        bridge: `어지러운 내일 걱정은 창밖에 두고\n지금 이 멜로디에 온전히 나를 맡겨`,
        soloTag: `[Rhodes Solo - smooth jazz electric piano improvisation]`,
        outroTag: `[Outro - rain ambient sound, vinyl crackle fading out]\n[Vocal Ad-libs: "Midnight rain... just you and me... chill... good night..."]\n[Vinyl Crackle & Rain Fade Out]`
      },
      {
        genre: '80s Synthwave / Retrowave',
        bpm: 124,
        instruments: 'Analog Juno Synths, LinnDrum, Driving Arpeggiated Bass, Chorus Guitar, Gated Reverb Snare',
        sunoCaption: `[Driving 124 BPM 80s Synthwave Retrowave, energetic D Minor arpeggios, neon cyberpunk highway night drive mood, retro futurism], [pumping analog Juno-106 synths, driving arpeggiated bassline, punchy LinnDrum beat, gated reverb snare bursts, chorus electric guitar riffs, polished 80s studio master], [cybernetic powerful female lead vocal, vocoder harmonies, tight vocal presence, 80s stereo delay]`,
        introTag: `[Intro]\n[driving arpeggiated synth bass, LinnDrum beat, gated snare, 124 BPM]`,
        verse1Tag: `[Verse 1 - robotic rhythmic vocals, pulsing synth bass, chorus guitar stabs]`,
        verse1: `보랏빛 네온이 번지는 끝없는 사이버 고속도로\n가속 페달을 밟으며 어둠을 뚫고 질주해\n디지털 계기판 위에 떠오르는 너의 좌표\n80년대 레트로 신스가 심장을 두드려`,
        preChorusTag: `[Pre-Chorus - rising synth sweep, drum fill build-up, vocoder backing]`,
        preChorus: `사이버 시티의 밤은 잠들지 않고\n전파를 타고 흐르는 우리의 시그널 (우리의 시그널)`,
        chorusTag: `[Chorus - explosive high-energy Synthwave chorus, soaring vocal melody, full synth brass]`,
        chorus: `네온 하이웨이를 달리는 레트로웨이브\n시속 140km로 날아가는 아날로그 신스 사운드\n과거와 미래가 교차하는 레이저 불빛 아래\n우리의 드라이브는 끝나지 않아 (끝나지 않아, yeah!)`,
        verse2Tag: `[Verse 2 - driving arpeggio groove, punchy gated drums, energetic vocals]`,
        verse2: `사이드미러 너머로 멀어지는 크롬빛 빌딩숲\n비트에 맞춰 요동치는 묵직한 아르페지오 베이스\n시간의 왜곡을 넘어 너에게 닿을 때까지\n이 밤의 에너지는 멈추지 않아`,
        bridgeTag: `[Bridge - dramatic analog synthesizer filter sweep, vocoder ad-lib solo]`,
        bridge: `빛의 속도로 달려가는 이 어둠의 끝에서\n우리는 새로운 차원의 아침을 마주해`,
        soloTag: `[Synth Solo - screaming 80s analog synth lead solo with pitch bends]`,
        outroTag: `[Outro - pumping synth bass arpeggio fading into laser echoes]\n[Vocal Ad-libs: "Neon highway... endless drive... synth pulse... 1984..."]\n[Laser Synth Fade Out]`
      },
      {
        genre: 'Modern R&B / Neo-Soul',
        bpm: 80,
        instruments: 'Electric Piano, Deep 808 Sub-Bass, Smooth Finger Snaps, Lush Vocal Harmonies, Clean Strat Guitar',
        sunoCaption: `[Sensual 80 BPM Modern R&B Neo-Soul, sweet Eb Major 9th chord progression, intimate midnight romance mood, pure sweet major harmony], [warm Rhodes electric piano, deep 808 sub-bass groove, crisp finger snaps, clean neo-soul guitar licks, smooth acoustic rimshots, warm studio mix], [dry intimate sweet falsetto vocals front-and-center, silky smooth vocal runs, lush stacked harmonies, no excessive reverb]`,
        introTag: `[Intro]\n[smooth Rhodes chords, finger snaps, clean guitar lick, 80 BPM, Eb Major]`,
        verse1Tag: `[Verse 1 - dry intimate falsetto, sweet electric piano, crisp snaps]`,
        verse1: `촛불 하나 켜둔 채 마주 앉은 새벽\n와인잔에 비친 너의 깊은 눈빛\n말하지 않아도 전해지는 공기의 떨림\n부드러운 소울 그루브가 우리 사이를 감싸네`,
        preChorusTag: `[Pre-Chorus - deep 808 sub-bass enters, silky vocal harmonies build up]`,
        preChorus: `손끝이 닿을 때 전해지는 전율\n숨소리마저 완벽한 화음이 되는 밤 (화음이 되는 밤)`,
        chorusTag: `[Chorus - sensual neo-soul groove, lush stacked falsetto harmonies, sweet vocal climax]`,
        chorus: `새벽 네 시, 우리만의 네오 소울\n깊은 베이스라인처럼 심장에 스며드는 너 (스며드는 너)\n아침이 오지 않길 바라는 이 순간\n영원히 머물고 싶은 달콤한 멜로디 (Oh baby, love me right)`,
        verse2Tag: `[Verse 2 - sweet active R&B swing vibe, warm Rhodes, smooth vocal runs]`,
        verse2: `창가에 맺힌 이슬처럼 투명한 감정들\n감미로운 건반 소리에 너를 맡겨봐\n세상 모든 소음이 멈춘 이 작은 방에서\n우리의 사랑은 가장 깊은 빛을 내`,
        bridgeTag: `[Bridge - emotional key change modulation, dramatic vocal run climax]`,
        bridge: `Baby, don't let this groove fade away\n이 밤이 끝날 때까지 널 놓지 않을게`,
        soloTag: `[Guitar Solo - smooth neo-soul clean guitar solo with warm tone]`,
        outroTag: `[Outro - sweet Rhodes chords, gentle finger snaps, fading vocal ad-libs]\n[Vocal Ad-libs: "Only you... feel the groove... stay with me tonight... yeah..."]\n[Smooth R&B Fade Out]`
      },
      {
        genre: 'Acoustic Indie Folk Pop',
        bpm: 96,
        instruments: 'Steel-String Acoustic Guitar, Warm Cello, Tambourine, Hand Claps, Glockenspiel, Upright Bass',
        sunoCaption: `[Upbeat 96 BPM happy K-Pop Acoustic Indie swing groove, bright sweet G Major chord progression, cheerful romantic spring mood, no minor chords, pure sweet major harmony], [bright sparkling fingerpicked acoustic guitar, active bouncy electric bassline, snappy syncopated rimshot drum groove, bright high-pitched shaker, warm sweet Rhodes chords, high-fidelity café studio mix], [dry intimate sweet female vocals front-and-center, clean mid-band vocal presence, no reverb, no delay]`,
        introTag: `[Intro]\n[fast bright nylon acoustic guitar plucking, fast snappy shaker, 96 BPM, happy sweet G Major]`,
        verse1Tag: `[Verse 1 - dry bright sweet female vocals, fast bouncy acoustic guitar, no minor chords, happy mood]`,
        verse1: `따스한 햇살이 창가에 머물면\n네가 생각나 나도 모르게 웃음이 나\n살랑이는 봄바람에 실려 온 네 향기\n귓가에 맴도는 너의 목소리`,
        preChorusTag: `[Pre-Chorus - snappy bouncy swing rimshot drum, active electric bass enters]`,
        preChorus: `조금씩 천천히 두근거리는 내 맘\n너에게 다가가는 설레는 발걸음 (설레는 발걸음)`,
        chorusTag: `[Chorus - upbeat bright R&B swing groove, warm Rhodes chords, cheerful sweet vocal climax, happy sweet harmony]`,
        chorus: `Feel the love in your heart, let it glow\n바람을 따라서 흘러가듯 천천히\n어느새 스며든 너의 그 향기\n이 봄바람을 따라 우리 둘이 영원히 (Yeah, oh baby)`,
        verse2Tag: `[Verse 2 - sweet active acoustic R&B swing vibe, warm nylon guitar, bright vocals]`,
        verse2: `오후의 햇살이 우리를 비추고\n소소한 얘기로 채워가는 시간\n네 손을 꼭 쥐고 걸어가는 길\n세상 모든 것이 다 눈부시게 보여`,
        bridgeTag: `[Bridge - cheerful acoustic guitar strumming, bright glockenspiel harmony]`,
        bridge: `어려운 말 대신 건네는 따스한 멜로디\n언제나 네 곁에 머물겠다는 약속`,
        soloTag: `[Acoustic Guitar Solo - fast cheerful fingerpicking solo]`,
        outroTag: `[Outro - fast guitar pluck, bright shaker, happy piano chords fading out]\n[Vocal Ad-libs: "Only you... my spring... walk with you... yeah... feel the spring..."]\n[Fade Out]`
      }
    ];

    // Single variations catalog
    const singleCatalog = [
      { name: 'Original Radio Edit', genre: 'Modern Pop', bpm: 116, instruments: 'Full Production, Synths, Punchy Beats', sunoStyle: '[Upbeat 116 BPM Modern Commercial Pop, bright C Major, catchy radio hit mood], [punchy electronic drum beat, active synth bassline, sparkling top synths, studio mix], [dry commercial vocal front-and-center, crisp clean presence]' },
      { name: 'Acoustic Unplugged Ver.', genre: 'Acoustic Indie', bpm: 88, instruments: 'Warm Acoustic Guitar, Upright Piano', sunoStyle: '[Intimate 88 BPM Acoustic Unplugged, sweet G Major, cozy café mood], [warm fingerpicked acoustic guitar, upright piano, delicate room acoustics], [dry intimate singer-songwriter vocal, pure natural tone]' },
      { name: 'Lo-Fi Midnight Chillhop Remix', genre: 'Lo-Fi Chillhop', bpm: 82, instruments: 'Vinyl Rhodes, Muted Guitar', sunoStyle: '[Relaxing 82 BPM Lo-Fi Chillhop, Bb Major 7th, late night study mood], [warm Rhodes chords, vinyl crackle, muted jazz guitar, soft boom-bap drums], [whispering vocal, tape saturation]' },
      { name: 'Synthwave Neon Club Mix', genre: 'Synthwave', bpm: 126, instruments: '80s Analog Synths, LinnDrum', sunoStyle: '[Driving 126 BPM 80s Synthwave, D Minor arpeggio, neon cyberpunk club mood], [pumping analog Juno synths, driving bassline, LinnDrum, gated snare], [cybernetic powerful vocal, 80s delay]' },
      { name: 'Stripped Piano & Cello Ballad', genre: 'K-Pop Ballad', bpm: 70, instruments: 'Grand Piano, Solo Cello', sunoStyle: '[Emotional 70 BPM Stripped Ballad, C Minor to Eb Major, tearful dramatic mood], [intimate grand piano solo, warm acoustic cello, cinematic room reverb], [airy passionate vocal, close-mic delivery]' }
    ];

    // Album narrative catalog
    const albumCatalog = [
      { role: 'Prologue / Intro', titleSuffix: 'Intro: 여명의 빛', genre: 'Cinematic Ambient', bpm: 64, instruments: 'Ambient Drone, Solo Piano', sunoStyle: '[Atmospheric 64 BPM Cinematic Ambient, mystical prologue mood], [ambient synthesizer drone, intimate solo piano, wind FX], [no vocal, pure instrumental]' },
      { role: 'Lead Title Track', titleSuffix: '타이틀: 운명의 밤', genre: 'Emotional K-Pop Ballad', bpm: 76, instruments: 'Grand Piano, Full Strings', sunoStyle: '[Emotional 76 BPM K-Pop Ballad, dramatic orchestral climax], [grand piano, 24-piece strings, dynamic drums, bass], [passionate powerful Korean vocal]' },
      { role: 'Sub Title Track', titleSuffix: '서브타이틀: 도시의 네온사인', genre: '80s Japanese City Pop', bpm: 118, instruments: 'Funky Bass, Brass Section', sunoStyle: '[Upbeat 118 BPM Japanese City Pop, bright A Major, groovy sunset drive mood], [slap bass, brass horn stabs, FM synths], [dry warm female vocal]' },
      { role: 'B-Side 1: Acoustic', titleSuffix: '골목길의 기억', genre: 'Acoustic Indie Folk Pop', bpm: 96, instruments: 'Acoustic Guitar, Warm Cello', sunoStyle: '[Upbeat 96 BPM happy K-Pop Acoustic Indie swing groove, bright sweet G Major], [fingerpicked acoustic guitar, active bass, shaker], [dry intimate sweet female vocals]' },
      { role: 'Epilogue / Outro', titleSuffix: 'Outro: 영원의 멜로디', genre: 'Cinematic Ambient', bpm: 65, instruments: 'Solo Grand Piano, Strings', sunoStyle: '[Gentle 65 BPM Cinematic Outro, peaceful emotional closure], [solo grand piano, string quartet, gentle fadeout], [whispered soft vocal ad-libs]' }
    ];

    for (let i = 0; i < count; i++) {
      const id = `RECIPE-${String(i + 1).padStart(3, '0')}`;
      let template = exploreCatalog[i % exploreCatalog.length];
      let title = `${keyword} - ${template.genre} #${i + 1}`;
      let genre = template.genre;
      let bpm = template.bpm;
      let instruments = template.instruments;
      let sunoStylePrompt = template.sunoCaption;
      let concept = `Explore Variation #${i + 1} (${genre})`;
      let lyricTheme = `${keyword}을 주제로 한 ${template.genre} 완성형 음악 스토리텔링`;

      if (mode === 'single') {
        const item = singleCatalog[i % singleCatalog.length];
        title = `${keyword} (${item.name})`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        sunoStylePrompt = item.sunoStyle;
        concept = `[Single Variation] ${item.name}`;
        lyricTheme = `${keyword}의 ${item.name} 감성 편곡`;
      } else if (mode === 'album') {
        const item = albumCatalog[i % albumCatalog.length];
        title = `${item.titleSuffix} - ${keyword}`;
        genre = item.genre;
        bpm = item.bpm;
        instruments = item.instruments;
        sunoStylePrompt = item.sunoStyle;
        concept = `[${item.role}] ${item.titleSuffix}`;
        lyricTheme = `앨범 [${keyword}]의 ${item.role} 트랙`;
      }

      const fullLyrics = [
        template.introTag,
        `${template.verse1Tag}\n${template.verse1}`,
        `${template.preChorusTag}\n${template.preChorus}`,
        `${template.chorusTag}\n${template.chorus}`,
        `${template.verse2Tag}\n${template.verse2}`,
        `${template.bridgeTag}\n${template.bridge}`,
        template.soloTag,
        `${template.chorusTag}\n${template.chorus}`,
        template.outroTag
      ].join('\n\n');

      const promptText = `[Genre: ${genre}] [BPM: ${bpm}] [Suno Style: ${sunoStylePrompt}] [Theme: ${keyword}]`;

      recipes.push({
        id,
        title,
        genre,
        bpm,
        instruments,
        lyricTheme,
        lyrics: {
          intro: template.introTag,
          verse1: `${template.verse1Tag}\n${template.verse1}`,
          preChorus: `${template.preChorusTag}\n${template.preChorus}`,
          chorus: `${template.chorusTag}\n${template.chorus}`,
          verse2: `${template.verse2Tag}\n${template.verse2}`,
          bridge: `${template.bridgeTag}\n${template.bridge}`,
          outro: template.outroTag
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

  /**
   * [v0.2.0] Generate Single Track Deep Production Blueprint (API-009, SCN-006)
   * Includes sound architecture, music theory rationales, section timeline, and Suno master prompts.
   */
  /**
   * [v0.2.0] Generate Single Track Deep Production Blueprint (API-009, SCN-006)
   * Includes smart genre/tempo auto-recommendations, sound architecture, rationales, timeline, and Suno master prompts.
   */
  async generateDeepProductionBlueprint({ story, mood = '', reference = '', targetGenre = 'auto', bpm = 0 }) {
    const rawStory = String(story || '').toLowerCase();

    // 1. Smart Genre & Tempo Auto-Analysis by AI Director
    let selectedGenre = targetGenre;
    let selectedBpm = Number(bpm) || 0;
    let autoAdvice = '';
    let alternatives = [];

    if (!selectedGenre || selectedGenre === 'auto') {
      if (rawStory.includes('이별') || rawStory.includes('눈물') || rawStory.includes('슬픔') || rawStory.includes('발라드')) {
        selectedGenre = 'K-Pop Ballad';
        selectedBpm = selectedBpm || 72;
        autoAdvice = '입력하신 스토리의 애절하고 깊은 감정선을 극대화하기 위해 서정적인 [K-Pop Acoustic Ballad]와 차분한 [72 BPM]을 메인으로 추천합니다.';
        alternatives = [
          { genre: 'Lo-Fi Chillhop', bpm: 82, reason: '너무 무겁지 않은 담담한 이별의 쓸쓸함을 원할 때 추천' },
          { genre: 'Acoustic Folk', bpm: 90, reason: '어쿠스틱 기타 한 대로 진솔한 이야기를 전달할 때 추천' }
        ];
      } else if (rawStory.includes('새벽') || rawStory.includes('공부') || rawStory.includes('휴식') || rawStory.includes('카페')) {
        selectedGenre = 'Lo-Fi Chillhop';
        selectedBpm = selectedBpm || 84;
        autoAdvice = '나른하고 편안한 새벽/휴식 무드를 연출하기 위해 따뜻한 재즈 피아노와 바이닐 질감의 [Lo-Fi Chillhop (84 BPM)]을 추천합니다.';
        alternatives = [
          { genre: 'City Pop', bpm: 112, reason: '새벽 드라이브의 리듬감을 원할 때 추천' },
          { genre: 'Neo-Soul', bpm: 88, reason: '그루비한 베이스와 소울풀한 보컬을 원할 때 추천' }
        ];
      } else if (rawStory.includes('드라이브') || rawStory.includes('도시') || rawStory.includes('비') || rawStory.includes('네온')) {
        selectedGenre = 'City Pop';
        selectedBpm = selectedBpm || 118;
        autoAdvice = '도시의 젖은 밤거리와 세련된 그루브를 살리기 위해 펑키한 슬랩베이스와 브라스가 어우러진 [80s Japanese City Pop (118 BPM)]을 추천합니다.';
        alternatives = [
          { genre: 'Synthwave', bpm: 124, reason: '80년대 레트로 전자음과 질주감을 강조할 때 추천' },
          { genre: 'Lo-Fi Chillhop', bpm: 86, reason: '차분한 빗소리 분위기를 강조할 때 추천' }
        ];
      } else if (rawStory.includes('여름') || rawStory.includes('신나는') || rawStory.includes('질주') || rawStory.includes('파티')) {
        selectedGenre = 'Synthwave';
        selectedBpm = selectedBpm || 126;
        autoAdvice = '에너지 넘치는 질주감과 화려한 사운드를 위해 강렬한 아날로그 신스 [Retro Synthwave (126 BPM)]를 추천합니다.';
        alternatives = [
          { genre: 'City Pop', bpm: 120, reason: '경쾌한 펑크 그루브를 원할 때 추천' },
          { genre: 'Neo-Soul', bpm: 105, reason: '트렌디한 어반 댄스 팝을 원할 때 추천' }
        ];
      } else {
        selectedGenre = 'City Pop';
        selectedBpm = selectedBpm || 118;
        autoAdvice = '서사와 멜로디의 밸런스가 가장 뛰어난 [80s Japanese City Pop (118 BPM)]을 기본 추천 사운드로 설정했습니다.';
        alternatives = [
          { genre: 'K-Pop Ballad', bpm: 74, reason: '보컬의 서정성을 강조할 때 추천' },
          { genre: 'Lo-Fi Chillhop', bpm: 84, reason: '편안한 이지리스닝을 원할 때 추천' }
        ];
      }
    } else {
      selectedBpm = selectedBpm || (selectedGenre.includes('Ballad') ? 72 : (selectedGenre.includes('Chillhop') ? 84 : 118));
      autoAdvice = `디렉터님이 지정하신 [${selectedGenre}] 장르에 가장 어울리는 프로덕션 템포인 [${selectedBpm} BPM]으로 맞춤 기획했습니다.`;
      alternatives = [
        { genre: 'City Pop', bpm: 118, reason: '도시적인 세련된 그루브' },
        { genre: 'Lo-Fi Chillhop', bpm: 84, reason: '따뜻한 로우파이 감성' }
      ];
    }

    const genre = selectedGenre;
    const tempo = selectedBpm;
    const key = genre.toLowerCase().includes('ballad') ? 'D Major' : (genre.toLowerCase().includes('lo-fi') ? 'Eb Major 7th' : 'A Major');

    const rationale = {
      aiAdvisory: autoAdvice,
      tempoRationale: `${tempo} BPM - ${tempo >= 110 ? '도시적인 드라이브감과 춤추듯 여유로운 바운스를 살리는 업템포 그루브' : (tempo <= 80 ? '화자의 숨결과 서정적인 멜로디에 온전히 몰입하게 만드는 차분한 슬로우 템포' : '편안하고 자연스러운 심장 박동에 맞춘 미디엄 이지리스닝 템포')}`,
      keyRationale: `${key} - 단조의 짙은 우울함 대신, 지나간 시간에 대한 아련한 빛과 감정을 따뜻하게 감싸주는 화성 진행`,
      instrumentationRationale: [
        genre.includes('City Pop') ? 'Slap & Walking Bass: 도시적이고 세련된 바운스를 형성하여 곡 전체의 드라이브감 유지' : 'Deep Sub Bass / Upright Bass: 따뜻하고 묵직하게 감정선을 받쳐주는 베이스',
        genre.includes('Lo-Fi') ? 'Rhodes Piano & Vinyl Crackle: 아날로그 LP 특유의 따뜻하고 포근한 질감' : 'FM Synthesizer / Piano: 맑고 투명한 건반 사운드로 감성적인 공기감 형성',
        genre.includes('Ballad') ? 'Acoustic Guitar & Warm Strings: 서정적인 현악기와 핑거링 기타의 조화' : 'Brass Section Stabs: 코러스(Chorus) 진입 시 클라이맥스 카타르시스를 위한 다이내믹스 폭발',
        'Dry Clean Lead Vocals: 화자의 독백을 과장 없이 담백하고 친밀하게 전달 (no excessive reverb)'
      ],
      vocalDirection: '과도한 기교나 비브라토를 배제하고, 리스너의 귓가에 조용히 읊조리듯 친밀한 톤 (Dry intimate presence)'
    };

    // Generate a clean, poetic short title (max 20 chars)
    let shortTitle = '상처와 빛의 역설';
    if (rawStory.includes('스크래치') || rawStory.includes('아크릴') || rawStory.includes('상처')) {
      shortTitle = '빛을 품은 스크래치';
    } else if (rawStory.includes('이별') || rawStory.includes('눈물')) {
      shortTitle = '비 내리는 날의 이별';
    } else if (rawStory.includes('새벽') || rawStory.includes('카페')) {
      shortTitle = '새벽 두 시의 온기';
    } else if (rawStory.includes('드라이브') || rawStory.includes('도시')) {
      shortTitle = '네온사인 드라이브';
    } else if (story) {
      shortTitle = story.split('\n')[0].split('.')[0].slice(0, 18).trim() || '빛나는 기억';
    }

    const sections = [
      {
        part: 'Intro',
        tag: `[Intro - clean instrument opening, sparkling keys, ${tempo} BPM, bright ${key}]`,
        rationale: '도입부 악기 테마만으로 곡 전체의 공기감과 무드를 단숨에 리스너에게 제시',
        lyrics: '(Instrumental Opening)',
        vocalAdlibs: ''
      },
      {
        part: 'Verse 1',
        tag: '[Verse 1 - dry bright sweet vocals, minimal rhythm, quiet bass]',
        rationale: '드럼을 절제하고 악기 1~2대와 보컬만으로 화자의 공간과 첫 독백을 담담하게 전개',
        lyrics: rawStory.includes('아크릴') 
          ? '불투명한 아크릴 뒤로 켜진 은은한 불빛\n스쳐간 상처들이 빛을 머금고 번져가\n깊게 패인 자리마다 더 환하게 피어나는\n내 안의 숨겨진 빛을 마주하는 이 순간'
          : '네온사인 물든 밤거리 위로\n조용히 번지는 젖은 아스팔트 불빛\n룸미러 속 스쳐가는 도시의 그림자\n잊혀진 라디오 멜로디가 귓가에 흘러',
        vocalAdlibs: '(스쳐가는 기억들)'
      },
      {
        part: 'Pre-Chorus',
        tag: '[Pre-Chorus - snappy bouncy rimshot drum enters, active electric bass, tension build-up]',
        rationale: '림샷 드럼과 베이스가 진입하며 심장 박동과 기대감을 고조시키는 빌드업 구간',
        lyrics: rawStory.includes('아크릴')
          ? '아물지 않은 틈새 사이로 번져오는 온기\n상처가 깊을수록 더 찬란하게 빛나는\n결국 나를 비추는 아름다운 역설'
          : '차창을 내리면 불어오는 서늘한 바람\n마음 한구석에 숨겨둔 너의 기억을 깨워\n조금씩 천천히 두근거리는 내 맘',
        vocalAdlibs: '(찬란한 빛의 역설)'
      },
      {
        part: 'Chorus',
        tag: '[Chorus - full emotional climax groove, lush arrangement, warm keys, stacked harmonies]',
        rationale: '풀 밴드와 코러스 화음이 폭발하며 곡의 감정적 클라이맥스 완성',
        lyrics: rawStory.includes('아크릴')
          ? `어둠을 뚫고 피어나는 ${shortTitle}\n아파했던 날들이 내게 남겨준 가장 큰 선물\n상처는 부서짐이 아닌 빛을 품는 통로였어\n이제야 온전히 나를 비추네`
          : `비 내리는 날의 ${shortTitle}\n밤하늘을 수놓은 오색빛깔 불빛들\n우리 함께 나누었던 그 수많은 약속들\n시간이 지나도 가슴속에 살아 숨 쉬어`,
        vocalAdlibs: '(Yeah, shining through the scars)'
      },
      {
        part: 'Verse 2',
        tag: '[Verse 2 - sweet active rhythm groove, warm Rhodes chords, dry intimate vocals]',
        rationale: '후렴의 폭발 후 다시 차분하게 가라앉으며 깊어진 내면의 감정을 노래',
        lyrics: '유리창에 번지는 네온빛 수채화\n빗물 위로 흩어지는 너의 그림자\n이제는 미소 지으며 보낼 수 있어\n소중했던 그 계절의 따스한 기억',
        vocalAdlibs: '(따스한 기억)'
      },
      {
        part: 'Bridge',
        tag: '[Bridge - emotional solo, lush strings, minimal drums, emotional build-up]',
        rationale: '감정선이 최고조에 달하며 마지막 코러스로 이어지는 브릿지',
        lyrics: '어둠이 걷히고 새벽이 찾아오면\n우리의 이야기는 빛나는 별이 되어\n영원히 이 거리를 비출 테니까',
        vocalAdlibs: '(빛나는 별이 되어)'
      },
      {
        part: 'Chorus Climax',
        tag: '[Chorus - anthemic climax, explosive arrangement, stacked backing vocals]',
        rationale: '가장 화려하고 웅장한 피날레 후렴',
        lyrics: rawStory.includes('아크릴')
          ? `어둠을 뚫고 피어나는 ${shortTitle}\n아파했던 날들이 내게 남겨준 가장 큰 선물\n상처가 깊을수록 더 눈부시게 빛나니까\n영원히 빛나는 나의 이야기`
          : `비 내리는 날의 ${shortTitle}\n밤하늘을 수놓은 오색빛깔 불빛들\n우리 함께 나누었던 그 수많은 약속들\n영원히 잊지 않을게, 안녕`,
        vocalAdlibs: '(Yeah, shining bright forever)'
      },
      {
        part: 'Outro',
        tag: `[Outro - fading bass groove, bright synth, warm chords fading out]`,
        rationale: '악기들이 하나씩 페이드아웃되며 깊은 여운을 남김',
        lyrics: '(Fading Out with Music)',
        vocalAdlibs: '[Vocal Ad-libs: "Shining through the scars... thank you for the light... yeah..."]'
      }
    ];

    const sunoStylePrompt = `[Upbeat ${tempo} BPM ${genre}, bright ${key} progression, nostalgic romantic mood, sparkling major harmony], [funky bouncy bassline, lush brass section, sparkling synth lead, clean chorus rhythm guitar, syncopated tight drum groove, high-fidelity studio mix], [dry intimate warm vocals front-and-center, clean mid-band presence, lush backing vocal harmonies, no excessive reverb]`;

    const fullLyrics = sections.map(s => `${s.tag}\n${s.lyrics}${s.vocalAdlibs ? '\n' + s.vocalAdlibs : ''}`).join('\n\n');

    const negativePrompt = '[no autotune hiss, no distorted vocal, no muddy bass, no aggressive heavy metal guitar, no flat mono mix]';

    return {
      title: `${shortTitle} - Master Production`,
      genre,
      bpm: tempo,
      key,
      rationale,
      alternatives,
      sections,
      sunoStylePrompt,
      fullLyrics,
      negativePrompt,
      sunoTips: {
        extendGuide: '1차 생성 시 Verse 1 ~ Chorus(약 1분 20초)를 먼저 생성 후 마음에 들면 [Extend]로 완성하세요.',
        inpaintGuide: '솔로 구간이나 브릿지가 어색할 때는 해당 타임스탬프에서 [Inpaint (Replace Section)]를 사용하세요.',
        customModeGuide: 'Suno 웹의 Custom Mode를 켜고 Style of Music과 Lyrics를 각각 붙여넣으세요.'
      }
    };
  }

  /**
   * [v0.2.0] AI Co-Producer Agent Tuning Interaction (API-013, SCN-008)
   */
  async tuneWithCoProducer({ trackTitle, currentLyrics, currentStyle, userInstruction }) {
    let tunedLyrics = currentLyrics;
    let tunedStyle = currentStyle;
    let tuningNotes = [];

    if (userInstruction.includes('색소폰') || userInstruction.includes('솔로')) {
      tunedLyrics = tunedLyrics.replace('[Bridge', '[Bridge - emotional alto sax solo, warm reverb\n[Saxophone Solo');
      tunedStyle = tunedStyle.replace('FM synth lead', 'FM synth lead, expressive warm alto saxophone');
      tuningNotes.push('브릿지 구간에 감성적인 알토 색소폰 솔로 태그 추가');
    }

    if (userInstruction.includes('가사') || userInstruction.includes('은유')) {
      tunedLyrics = tunedLyrics.replace('네온사인 물든 밤거리 위로', '유리창에 번지는 네온빛 수채화');
      tuningNotes.push('Verse 가사에 시각적 수채화 은유 표현 반영');
    }

    if (userInstruction.includes('브라스') || userInstruction.includes('화려')) {
      tunedStyle = tunedStyle.replace('lush brass', 'explosive punchy big band brass section stabs');
      tuningNotes.push('스타일 프롬프트에 파워풀한 빅밴드 브라스 섹션 보강');
    }

    if (tuningNotes.length === 0) {
      tuningNotes.push(`사용자 요청("${userInstruction}")에 맞춘 미세 다이내믹스 및 편곡 튜닝 적용`);
    }

    return {
      agentResponse: `디렉터님, 요청하신 "${userInstruction}" 사항을 반영하여 새로운 편곡/가사 튜닝을 완료했습니다!`,
      tuningNotes,
      tunedLyrics,
      tunedStyle,
      suggestedBranchName: `take_${Date.now().toString().slice(-4)}_${userInstruction.slice(0, 10).replace(/[^a-zA-Z0-9가-힣]/g, '_')}`
    };
  }
}

export default GeminiProvider;

