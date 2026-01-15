# Quick Start Guide - 빠른 시작 가이드

## 5분 안에 시작하기

### 1. 의존성 설치 (Installation)

```bash
# 저장소 클론
git clone https://github.com/hanlyang0522/ssadan.git
cd ssadan

# 설치 스크립트 실행 (Linux/macOS)
bash setup.sh

# 또는 수동으로 설치
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

### 3. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 vim, code 등 원하는 에디터 사용
```

`.env`에서 최소한 `WEBHOOK_URL`을 설정하세요:
```bash
WEBHOOK_URL=https://your-webhook-url.com
```

### 4. 식단표 이미지 준비

식단표 이미지를 프로젝트 디렉토리에 저장하세요. 예: `meal_schedule.jpg`

**권장 형식:**
- 명확한 텍스트
- 날짜와 식사 유형 (조식/중식/석식)이 명확히 표시
- 해상도 800x600 이상

### 5. 테스트

#### OCR 테스트
```bash
python main.py test-ocr --image meal_schedule.jpg
```

성공하면 파싱된 식단이 출력됩니다.

#### Webhook 테스트
```bash
python main.py test-webhook --url https://your-webhook-url.com
```

성공하면 webhook 엔드포인트로 테스트 메시지가 전송됩니다.

### 6. 수동으로 알림 보내기

#### 오늘의 식단 보내기
```bash
python main.py send-daily
```

#### 주간 식단 보내기
```bash
python main.py send-weekly
```

### 7. 자동 스케줄러 실행

```bash
python main.py run
```

이제 봇이 매일/매주 자동으로 알림을 보냅니다!

중지하려면 `Ctrl+C`를 누르세요.

---

## Slack 연동 예제

### 1. Slack Webhook 생성

1. https://api.slack.com/apps 접속
2. "Create New App" 클릭
3. "From scratch" 선택
4. 앱 이름 입력 (예: "SSADAN")
5. 워크스페이스 선택
6. "Incoming Webhooks" 활성화
7. "Add New Webhook to Workspace" 클릭
8. 채널 선택
9. Webhook URL 복사

### 2. 설정

`.env` 파일에 Slack Webhook URL 추가:
```bash
WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

### 3. 테스트

```bash
python main.py test-webhook
python main.py send-daily
```

---

## Discord 연동 예제

### 1. Discord Webhook 생성

1. Discord 서버 설정 열기
2. "연동" (Integrations) 메뉴 선택
3. "웹후크" (Webhooks) 선택
4. "새 웹후크" (New Webhook) 클릭
5. 웹후크 이름 설정 (예: "SSADAN")
6. 채널 선택
7. "웹후크 URL 복사" 클릭

### 2. 설정

`.env` 파일에 Discord Webhook URL 추가:
```bash
WEBHOOK_URL=https://discord.com/api/webhooks/000000000000000000/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 테스트

```bash
python main.py test-webhook
python main.py send-daily
```

---

## 문제 해결 (Troubleshooting)

### "No module named 'pytesseract'"
```bash
pip install -r requirements.txt
```

### "tesseract is not installed"
Tesseract OCR을 설치하세요 (위의 2단계 참조)

### "WEBHOOK_URL not set"
`.env` 파일을 생성하고 WEBHOOK_URL을 설정하세요

### OCR이 텍스트를 인식하지 못함
- 이미지가 명확한지 확인
- 한국어 언어팩 설치 확인: `tesseract --list-langs | grep kor`
- 이미지 형식 확인 (IMAGE_FORMAT.md 참조)

---

## 다음 단계

- 시스템 서비스로 설정 (README.md 참조)
- 식단표 형식에 맞게 파서 커스터마이징
- 다른 webhook 서비스 연동

질문이 있으시면 이슈를 생성해주세요!
