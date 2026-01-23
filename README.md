# SSADAN - SSAFY 식단 알림 봇 🍽️

매주, 매일 Mattermost와 Discord webhook으로 식단을 알려주는 자동화 봇입니다.

## 프로젝트 구조

```
.
├── .github/
│   └── workflows/          # GitHub Actions를 활용한 자동화 스케줄러
│       ├── daily_notify.yml   # 매일 오전 9시 10분 점심 알림
│       └── weekly_notify.yml  # 주간 식단표 처리 및 알림
├── db/                     # 추출된 식단 Markdown 파일 저장소 (yyyy-mm-dd.md)
│   └── .gitkeep
├── src/                    # 핵심 실행 로직 (Python)
│   ├── main.py             # 전체 프로세스 제어 (Entry point)
│   ├── ocr_processor.py    # 이미지 인식 및 Markdown 변환
│   ├── mm_sender.py        # Mattermost 웹훅 발송 로직
│   ├── discord_sender.py   # Discord 웹훅 발송 로직
│   └── notification_sender.py  # 통합 알림 발송 (Mattermost + Discord)
├── requirements.txt        # 필요 라이브러리
├── README.md               # 프로젝트 설명
└── .env.example            # 환경변수 샘플
```

## 작동 방법

1. **이미지 처리 (OCR)**: 식단표를 찍은 이미지에서 식단을 추출해 Markdown 테이블로 변환하고 `db/yyyy-mm-dd.md` 파일로 저장
2. **파일 확인 및 수정**: OCR 정확도가 완벽하지 않을 수 있으므로 생성된 Markdown 파일을 확인하고 필요시 수정
3. **주간 알림**: 확인/수정된 파일을 Mattermost와 Discord webhook으로 1주일치 식단 전송
4. **일일 알림**: 매일 오전 9시 10분에 그 날 점심 식단을 Mattermost와 Discord로 전송

## 설치

### 1. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt
```

### 2. Google Cloud 설정

#### 2.1. Google Cloud 프로젝트 생성 및 Document AI 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Document AI API 활성화
3. Document AI > Processors에서 **Form Parser** 프로세서 생성
4. Processor ID 복사 (예: `1234567890abcdef`)

#### 2.2. 서비스 계정 생성
1. IAM & Admin > Service Accounts에서 서비스 계정 생성
2. 역할: **Document AI API User** 추가
3. 키 생성 (JSON 형식) 및 다운로드

### 3. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일 설정:
```bash
# Mattermost Webhook URL
MATTERMOST_WEBHOOK_URL=https://your-mattermost-server.com/hooks/xxx

# Discord Webhook URL (선택사항)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy

# Google Cloud Document AI 설정
GOOGLE_CLOUD_CREDENTIALS={"type":"service_account","project_id":"your-project",...}
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_PROCESSOR_ID=your-processor-id
GOOGLE_CLOUD_LOCATION=us  # 또는 eu, asia 등
```

**주의**: 
- `GOOGLE_CLOUD_CREDENTIALS`는 다운로드한 JSON 파일의 내용을 한 줄로 작성합니다.
- Mattermost 또는 Discord 중 최소 하나의 webhook URL은 설정되어야 합니다.
- 두 개를 모두 설정하면 양쪽에 동시에 메시지가 전송됩니다.

## 사용법

### 로컬 실행

#### 1. 이미지 처리 및 주간 식단표 전송 (통합)
```bash
cd src
python main.py process --image ../meal_schedule.jpg --db ../db
```

#### 2. 이미지 OCR 처리만 수행 (웹훅 전송 없음)
```bash
cd src
python main.py ocr --image ../meal_schedule.jpg --db ../db
```
OCR 처리 후 생성된 `db/yyyy-mm-dd.md` 파일을 확인하고 필요시 수정할 수 있습니다.

#### 3. 저장된 파일로 주간 식단표 전송
```bash
cd src
python main.py notify --date 2026-01-15 --db ../db
```

#### 4. 오늘 점심 식단 전송
```bash
cd src
python main.py daily --db ../db
```

#### 5. 특정 날짜 점심 식단 전송
```bash
cd src
python main.py daily --date 2026-01-15 --db ../db
```

#### 6. 오늘의 노래 추천 요청
```bash
cd src
python main.py song
```

### GitHub Actions 자동화

#### 1. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 Secret 추가:
- `MATTERMOST_WEBHOOK_URL`: Mattermost Incoming Webhook URL (식단 알림용, 선택사항)
- `DISCORD_WEBHOOK_URL`: Discord Webhook URL (식단 알림용, 선택사항)
- `MATTERMOST_TODAY_SONG_URL`: Mattermost Incoming Webhook URL (오늘의 노래 추천용)
- `GOOGLE_CLOUD_CREDENTIALS`: Google Cloud 서비스 계정 JSON 키 (전체 내용)
- `GOOGLE_CLOUD_PROJECT_ID`: Google Cloud 프로젝트 ID
- `GOOGLE_CLOUD_PROCESSOR_ID`: Document AI Processor ID
- `GOOGLE_CLOUD_LOCATION`: Processor 위치 (예: `us`, `eu`, `asia`)

**참고**: `MATTERMOST_WEBHOOK_URL` 또는 `DISCORD_WEBHOOK_URL` 중 최소 하나는 설정되어야 합니다.

#### 2. 주간 식단표 처리

**2단계 프로세스로 분리되어 있습니다:**

**Step 1: OCR 처리 (Google Document AI)**
1. 식단표 이미지를 저장소에 커밋 (예: `meal_schedule.jpg`)
2. GitHub Actions > "Weekly Menu Notification" 선택
3. "Run workflow" 클릭
4. 이미지 경로 입력
5. step 선택: **"ocr"** 선택
6. Google Document AI가 테이블 구조를 인식하여 `db/yyyy-mm-dd.md` 파일 생성
7. 자동으로 파일이 커밋됩니다

**Step 2: 파일 확인 및 전송**
1. 생성된 `db/yyyy-mm-dd.md` 파일을 확인하고 필요시 수정
2. GitHub Actions > "Weekly Menu Notification" 선택
3. "Run workflow" 클릭
4. step 선택: **"notify"** 선택
5. 실행하면 저장된 파일 내용이 Mattermost로 전송됩니다

#### 3. 일일 알림

매일 오전 9시 10분(KST)에 자동으로 실행됩니다.
수동 실행: Actions > "Daily Lunch Notification" > "Run workflow"

#### 4. 오늘의 노래 추천

매일 오전 7시(KST)에 자동으로 실행됩니다.
수동 실행: Actions > "Today Song Recommendation" > "Run workflow"

## 출력 형식 예시

```markdown
## 🍴 SSAFY 주간메뉴표 (01/12 ~ 01/16)

| 구분 | 01월 12일 (월) | 01월 13일 (화) | 01월 14일 (수) | 01월 15일 (목) | 01월 16일 (금) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **20F 일반식 (A. 한식)** | 부대찌개<br>현미밥&쌀밥<br>... | ... | ... | ... | ... |
| **20F 일반식 (B. 일품)** | 카레라이스<br>... | ... | ... | ... | ... |
| **도시락** | 매콤돈사태찜<br>... | ... | ... | ... | ... |
```

## Mattermost Webhook 설정

1. Mattermost > Integrations > Incoming Webhooks
2. "Add Incoming Webhook" 클릭
3. 채널 선택 및 설정
4. Webhook URL 복사
5. `.env` 파일 또는 GitHub Secrets에 추가

## Discord Webhook 설정

1. Discord 서버에서 알림을 받을 채널 선택
2. 채널 설정(⚙️) > 연동 > 웹후크
3. "새 웹후크" 클릭
4. 웹후크 이름 설정 (예: "식단봇")
5. "웹후크 URL 복사" 클릭
6. `.env` 파일 또는 GitHub Secrets에 추가

## 커스터마이징

실제 식단표 형식에 맞게 `src/ocr_processor.py`의 `_parse_ocr_text()` 메서드를 수정하세요.

## 라이선스

MIT License
