import React, { useState, useEffect } from 'react';

/**
 * ZENION Music Studio Main App Component
 * Integrates 4 Core UI Contracts:
 * - UI-001: Main Dashboard (AI Screening & Vault)
 * - UI-002: AI Director Planning Suite
 * - UI-003: Track Detail & Video Studio
 * - UI-004: SNS Release Kit Hub
 */
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tracks, setTracks] = useState([]);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [keyword, setKeyword] = useState('비 오는 날의 이별');
  const [styleRecipes, setStyleRecipes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTracks();
  }, []);

  const fetchTracks = async () => {
    try {
      const res = await fetch('/api/tracks');
      const data = await res.json();
      if (data.tracks) {
        setTracks(data.tracks);
        if (data.tracks.length > 0 && !selectedTrack) {
          setSelectedTrack(data.tracks[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch tracks:', err);
    }
  };

  const handleGenerateStyles = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/director/generate-styles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword, count: 10, mode: 'explore' })
      });
      const data = await res.json();
      if (data.styles) {
        setStyleRecipes(data.styles);
      }
    } catch (err) {
      console.error('Failed to generate styles:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header style={{ background: '#161b22', padding: '12px 24px', borderBottom: '1px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#58a6ff' }}>🎵 ZENION Music Studio</span>
          <span style={{ background: '#238636', color: '#fff', fontSize: '11px', padding: '2px 8px', borderRadius: '12px' }}>v0.1 MVP</span>
        </div>
        <nav style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => setActiveTab('dashboard')} style={{ background: activeTab === 'dashboard' ? '#1f6feb' : 'transparent', color: '#fff', border: '1px solid #30363d', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            대시보드 (UI-001)
          </button>
          <button onClick={() => setActiveTab('director')} style={{ background: activeTab === 'director' ? '#1f6feb' : 'transparent', color: '#fff', border: '1px solid #30363d', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            AI 디렉터 (UI-002)
          </button>
          <button onClick={() => setActiveTab('studio')} style={{ background: activeTab === 'studio' ? '#1f6feb' : 'transparent', color: '#fff', border: '1px solid #30363d', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            비디오 스튜디오 (UI-003)
          </button>
          <button onClick={() => setActiveTab('release')} style={{ background: activeTab === 'release' ? '#1f6feb' : 'transparent', color: '#fff', border: '1px solid #30363d', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            SNS 릴리즈 허브 (UI-004)
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
        {activeTab === 'dashboard' && (
          <section>
            <h2>📊 AI Screening & Master Vault (UI-001)</h2>
            <p style={{ color: '#8b949e' }}>ACE 초안 음원 감지, AI 100점 만점 퀄리티 채점 및 상위 TOP 후보 랭킹 뷰</p>
            <div style={{ marginTop: '16px' }}>
              {tracks.length === 0 ? (
                <div style={{ padding: '32px', textAlign: 'center', background: '#161b22', borderRadius: '8px', border: '1px solid #30363d' }}>
                  등록된 음원 자산이 없습니다. AI 디렉터에서 새 레시피를 기획하거나 ACE-Step 초안을 감지하세요.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                  {tracks.map((t) => (
                    <div key={t.id} style={{ background: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold' }}>{t.title}</span>
                        <span style={{ background: '#388bfd33', color: '#58a6ff', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{t.aiScore}점</span>
                      </div>
                      <div style={{ fontSize: '13px', color: '#8b949e', marginTop: '8px' }}>장르: {t.genre} | BPM: {t.bpm}</div>
                      <div style={{ fontSize: '12px', color: '#c9d1d9', marginTop: '8px' }}>{t.aiReview || 'AI 심사 완료'}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {activeTab === 'director' && (
          <section>
            <h2>💡 AI 음악 디렉터 기획 스위트 (UI-002)</h2>
            <p style={{ color: '#8b949e' }}>감성 키워드 하나로 10종의 세부 장르 레시피와 구조화 가사를 즉시 기획합니다.</p>
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="감성 키워드 입력 (예: 비 오는 날의 이별)"
                style={{ flex: 1, padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: '6px', color: '#fff' }}
              />
              <button
                onClick={handleGenerateStyles}
                disabled={loading}
                style={{ background: '#238636', color: '#fff', padding: '10px 20px', borderRadius: '6px', border: 'none', cursor: 'pointer' }}
              >
                {loading ? '생성 중...' : '10종 스타일 레시피 생성'}
              </button>
            </div>

            <div style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {styleRecipes.map((r) => (
                <div key={r.id} style={{ background: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
                  <div style={{ fontWeight: 'bold', color: '#58a6ff' }}>{r.title}</div>
                  <div style={{ fontSize: '12px', color: '#8b949e', marginTop: '4px' }}>{r.genre} (BPM {r.bpm})</div>
                  <div style={{ fontSize: '12px', color: '#8b949e', marginTop: '4px' }}>악기: {r.instruments}</div>
                  <pre style={{ background: '#0d1117', padding: '10px', borderRadius: '6px', fontSize: '11px', marginTop: '8px', whiteSpace: 'pre-wrap' }}>{r.lyrics.chorus}</pre>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'studio' && (
          <section>
            <h2>🎬 비디오 스튜디오 & 듀얼 플레이어 (UI-003)</h2>
            <p style={{ color: '#8b949e' }}>ACE 초안 vs Suno 음원 비교 청음 및 유튜브 16:9 / 숏폼 9:16 비디오 원클릭 인코딩</p>
            <div style={{ padding: '24px', background: '#161b22', borderRadius: '8px', border: '1px solid #30363d', marginTop: '16px' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <button style={{ background: '#1f6feb', color: '#fff', padding: '8px 16px', borderRadius: '6px', border: 'none' }}>16:9 유튜브 롱폼 인코딩</button>
                <button style={{ background: '#8957e5', color: '#fff', padding: '8px 16px', borderRadius: '6px', border: 'none' }}>9:16 인스타/틱톡 숏폼 인코딩</button>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'release' && (
          <section>
            <h2>🚀 SNS 원클릭 릴리즈 허브 (UI-004)</h2>
            <p style={{ color: '#8b949e' }}>유튜브, 인스타그램, 틱톡 업로드 맞춤 제목, 설명문, 해시태그 원클릭 복사</p>
            <div style={{ padding: '24px', background: '#161b22', borderRadius: '8px', border: '1px solid #30363d', marginTop: '16px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>YouTube 릴리즈 키트 예시</div>
              <textarea
                readOnly
                rows={6}
                value="[Official MV] 비 오는 날의 이별 - AI Music Studio (K-Pop Ballad)&#10;&#10;Produced with ZENION Music Studio&#10;#AIMusic #ZENION #KPopBallad"
                style={{ width: '100%', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px', padding: '10px' }}
              />
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
