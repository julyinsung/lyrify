# 🎵 ZENION Music Studio (Lyrify) 실전 사용자 매뉴얼

> **"단순한 키워드 나열을 넘어, 음악적 이유(Rationale)와 완결성을 갖춘 히트곡을 기획하고 제작하는 AI 음악 프로덕션 워크스테이션"**

---

## 📑 목차
1. [개요 및 핵심 가치](#1-개요-및-핵심-가치)
2. [전체 프로덕션 워크플로우 5단계](#2-전체-프로덕션-워크플로우-5단계)
3. [Suno AI (v3.5 / v4 / v5) 실전 프롬프트 가이드](#3-suno-ai-실전-프롬프트-가이드)
4. [Music Git-Flow: 원장(Master)과 브랜치(Takes) 관리](#4-music-git-flow-원장master과-브랜치takes-관리)
5. [AI Co-Producer Agent와의 협업 방법](#5-ai-co-producer-agent와의-협업-방법)
6. [비디오 제작 및 SNS 릴리즈 키트 배포](#6-비디오-제작-및-sns-릴리즈-키트-배포)

---

## 1. 개요 및 핵심 가치

ZENION Music Studio는 단순히 기계적으로 가사를 찍어내는 도구가 아닙니다.
* **사운드 아키텍처 (Sound Blueprint)**: BPM, 조성(Key), 악기 편성, 보컬 캐릭터를 선정한 **"음악적 이유(Rationale)"**를 함께 제시합니다.
* **섹션별 인라인 연주 지시어**: `[Intro]`부터 `[Outro]`까지 각 파트의 빌드업 의도와 보컬 감정선을 대본처럼 연출합니다.
* **Music Git-Flow (버전 관리)**: 원장(Master)을 손상시키지 않고 다양한 편곡/가사 실험 브랜치(Takes)를 분기하여 A/B 비교 후 최종 마스터로 승격(Merge)합니다.

---

## 2. 전체 프로덕션 워크플로우 5단계

```
[1단계: 스토리 & 콘셉트 입력] ➔ [2단계: 사운드 설계도(Rationale) 확인] ➔ [3단계: Suno 웹에서 음원 생성]
       ➔ [4단계: 테이크 브랜치 분기 & A/B 청음] ➔ [5단계: 마스터 확정 & 비디오 렌더링]
```

### Step 1. 1곡 심층 기획 (Deep Produce)
1. 브라우저에서 `http://localhost:3000` 접속
2. **곡 테마 / 스토리라인**: 만들고자 하는 곡의 서사와 감정선 입력 (예: *"늦은 밤 비 내리는 도시, 지나간 사랑을 덤덤하게 추억하는 80s 시티팝"*)
3. **`🚀 1곡 심층 프로덕션 기획`** 버튼 클릭 ➔ AI가 BPM, 조성, 악기 편성의 기획 의도와 파트별 가사를 생성합니다.

### Step 2. 사운드 설계도 및 파트별 타임라인 검토
* **음악 기획서**: 왜 118 BPM인지, 왜 A Major인지, 왜 슬랩 베이스와 FM 신스가 들어갔는지 확인합니다.
* **타임라인 에디터**: `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`의 연주 지시어와 가사를 직접 수정할 수 있습니다.

### Step 3. Suno AI 웹 연동 및 고품질 음원 생성
1. **`[📋 Style of Music 복사]`** 클릭 ➔ Suno 웹(`suno.com`)의 Custom Mode **Style of Music** 란에 붙여넣기
2. **`[📋 Lyrics 복사]`** 클릭 ➔ Suno 웹의 **Lyrics** 란에 붙여넣기
3. Suno에서 `Create`를 눌러 2개의 초안 음악 생성 및 감상

### Step 4. 실제 음원 매핑 & 브랜치(Takes) 실험
1. Suno에서 다운로드한 `.mp3` 파일 경로를 Lyrify 스튜디오에 연결
2. 다른 편곡이나 가사를 시도하고 싶을 때 **`🌿 새 브랜치(Take) 생성`** 또는 AI Co-Producer에게 지시
3. **A/B 비교 플레이어**를 통해 원본(Master)과 수정본(Take 2)을 비교 청취

### Step 5. 원장 승격(Merge to Master) 및 비디오 배포
1. 가장 마음에 드는 테이크의 **`🌟 Master로 승격(Merge)`** 버튼을 누르면 최종 음원으로 확정
2. **`🎬 16:9 비디오`** / **`📱 9:16 숏폼`** 버튼을 눌러 자막 비디오 자동 렌더링
3. **`🚀 릴리즈 키트`**에서 유튜브/인스타/틱톡 설명문과 해시태그를 원클릭 복사하여 업로드!

---

## 3. Suno AI 실전 프롬프트 가이드

### 3.1. Style of Music Box (3단 구조화 공식)
* **1단 (장르/BPM/조성/무드)**: `[Upbeat 118 BPM Japanese City Pop, bright A Major, romantic sunset drive mood, sparkling major harmony]`
* **2단 (악기/베이스/드럼/믹싱)**: `[funky bouncy slap bassline, lush brass stabs, FM synth lead, clean chorus rhythm guitar, studio mix]`
* **3단 (보컬/배치/이펙트)**: `[dry intimate warm female vocals front-and-center, clean mid-band presence, no excessive reverb]`

### 3.2. Lyrics Box (인라인 메타태그 규칙)
* **대괄호 `[ ]`**: 연주 및 편곡 지시어 (Suno가 연주 스타일을 전환함)
  - `[Intro - funky slap bass solo, 118 BPM]`
  - `[Verse 1 - dry intimate female vocals, clean guitar]`
  - `[Pre-Chorus - snappy rimshot drum, tension rise]`
  - `[Chorus - full upbeat funk groove, lush brass, stacked harmonies]`
  - `[Guitar Solo - melodic chorus electric guitar]`
  - `[Outro - fading bass groove, brass hits]`
* **소괄호 `( )`**: 보컬 애드리브 및 코러스 백보컬
  - `(우리들의 추억)`, `(Yeah, oh baby)`

---

## 4. Music Git-Flow: 원장(Master)과 브랜치(Takes) 관리

* **원장 (Master v1.0)**: 현재 확정된 곡의 메인 버전 (`ZENION-MUSIC/곡명/master/`)
* **브랜치 (Takes)**: 특정 파트를 실험하기 위해 분기한 버전 (`ZENION-MUSIC/곡명/branches/take-02/`)
* **승격 (Merge)**: 실험 결과가 우수할 경우 원장으로 승격하여 `Master v2.0`으로 확정.

---

## 5. AI Co-Producer Agent와의 협업 방법

스튜디오 콘솔 우측의 **AI Co-Producer 대화창**에서 자연어로 지시하세요:
* *"Verse 2 가사를 좀 더 은유적이고 시적으로 바꿔줘."*
* *"후렴(Chorus) 끝에 색소폰 솔로가 들어가는 버전으로 브랜치 하나 만들어줘."*
* *"드럼 비트를 좀 더 공격적인 락 스타일로 바꾼 믹스를 제안해줘."*

AI Agent가 지시를 반영하여 즉시 새 브랜치를 분기하고 튜닝된 프롬프트와 가사를 제공합니다.
