# SSADAN - SSAFY 식단 알림 봇 🍽️

매주, 매일 Mattermost webhook으로 식단을 알려주는 자동화 봇입니다.

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
│   └── mm_sender.py        # Mattermost 웹훅 발송 로직
├── requirements.txt        # 필요 라이브러리
├── README.md               # 프로젝트 설명
└── .env.example            # 환경변수 샘플
```

## 작동 방법

1. **이미지 처리 (OCR)**: 식단표를 찍은 이미지에서 식단을 추출해 Markdown 테이블로 변환하고 `db/yyyy-mm-dd.md` 파일로 저장
2. **파일 확인 및 수정**: OCR 정확도가 완벽하지 않을 수 있으므로 생성된 Markdown 파일을 확인하고 필요시 수정
3. **주간 알림**: 확인/수정된 파일을 Mattermost webhook으로 1주일치 식단 전송
4. **일일 알림**: 매일 오전 9시 10분에 그 날 점심 식단을 Mattermost로 전송

## 설치

### 1. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# Tesseract OCR 설치 (로컬 환경)
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# macOS
brew install tesseract tesseract-lang
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env`에서 Mattermost Webhook URL 설정:
```bash
MATTERMOST_WEBHOOK_URL=https://your-mattermost-server.com/hooks/xxx
```

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

### GitHub Actions 자동화

#### 1. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 Secret 추가:
- `MATTERMOST_WEBHOOK_URL`: Mattermost Incoming Webhook URL

#### 2. 주간 식단표 처리

**2단계 프로세스로 분리되어 있습니다:**

**Step 1: OCR 처리**
1. 식단표 이미지를 저장소에 커밋 (예: `meal_schedule.jpg`)
2. GitHub Actions > "Weekly Menu Notification" 선택
3. "Run workflow" 클릭
4. 이미지 경로 입력
5. step 선택: **"ocr"** 선택
6. 실행 후 자동으로 `db/yyyy-mm-dd.md` 파일이 생성되고 커밋됩니다

**Step 2: 파일 확인 및 전송**
1. 생성된 `db/yyyy-mm-dd.md` 파일을 확인하고 필요시 수정
2. GitHub Actions > "Weekly Menu Notification" 선택
3. "Run workflow" 클릭
4. step 선택: **"notify"** 선택
5. 실행하면 저장된 파일 내용이 Mattermost로 전송됩니다

#### 3. 일일 알림

매일 오전 9시 10분(KST)에 자동으로 실행됩니다.
수동 실행: Actions > "Daily Lunch Notification" > "Run workflow"

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

## 커스터마이징

실제 식단표 형식에 맞게 `src/ocr_processor.py`의 `_parse_ocr_text()` 메서드를 수정하세요.

## 라이선스

MIT License
