# SSADAN - SSAFY 식단 알림 봇 🍽️

매주, 매일 webhook으로 식단을 알려주는 자동화 봇입니다.

## 기능 (Features)

1. **OCR 식단 읽기**: 이미지에서 OCR로 1주일치 식단을 자동으로 읽어옵니다
2. **주간 알림**: OCR 성공 시 1주일치 식단을 webhook으로 전송합니다
3. **일일 알림**: 매일 지정된 시간에 그날의 식단을 webhook으로 전송합니다

## 프로젝트 구조

```
ssadan/
├── main.py              # CLI 진입점
├── ocr_reader.py        # OCR 및 식단 파싱 모듈
├── webhook_notifier.py  # Webhook 알림 전송 모듈
├── scheduler.py         # 스케줄러 (자동 알림)
├── requirements.txt     # Python 의존성
├── .env.example        # 환경 변수 예제
└── README.md           # 문서
```

## 설치 (Installation)

### 1. Python 설치
Python 3.8 이상이 필요합니다.

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. Tesseract OCR 설치

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

#### Windows
[Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)에서 설치 파일을 다운로드하세요.

### 4. 환경 설정

`.env.example`을 `.env`로 복사하고 설정을 변경하세요:

```bash
cp .env.example .env
```

`.env` 파일 수정:
```bash
WEBHOOK_URL=https://your-webhook-url.com/webhook
MEAL_IMAGE_PATH=./meal_schedule.jpg
DAILY_NOTIFICATION_TIME=08:00
WEEKLY_NOTIFICATION_DAY=0
WEEKLY_NOTIFICATION_TIME=09:00
```

**설정 설명:**
- `WEBHOOK_URL`: 알림을 받을 webhook URL (Slack, Discord 등)
- `MEAL_IMAGE_PATH`: 식단표 이미지 파일 경로
- `DAILY_NOTIFICATION_TIME`: 일일 알림 시간 (HH:MM 형식, 24시간)
- `WEEKLY_NOTIFICATION_DAY`: 주간 알림 요일 (0=월요일, 6=일요일)
- `WEEKLY_NOTIFICATION_TIME`: 주간 알림 시간 (HH:MM 형식)

## 사용법 (Usage)

### 1. OCR 테스트

식단 이미지를 올바르게 읽는지 테스트:

```bash
python main.py test-ocr --image ./meal_schedule.jpg
```

### 2. Webhook 테스트

Webhook이 정상 작동하는지 테스트:

```bash
python main.py test-webhook --url https://your-webhook-url.com
```

### 3. 일일 식단 전송

오늘 날짜의 식단을 즉시 전송:

```bash
python main.py send-daily
```

특정 날짜의 식단 전송:

```bash
python main.py send-daily --date 2026-01-15
```

### 4. 주간 식단 전송

1주일치 식단을 즉시 전송:

```bash
python main.py send-weekly
```

### 5. 스케줄러 실행

자동으로 매일/매주 알림을 보내는 스케줄러 실행:

```bash
python main.py run
```

스케줄러는 백그라운드에서 계속 실행되며, 설정된 시간에 자동으로 알림을 전송합니다.

## Webhook 지원

### 지원되는 서비스

- **Generic Webhook**: 일반 JSON 형식
- **Slack**: Slack의 Incoming Webhook
- **Discord**: Discord Webhook

봇은 URL을 기반으로 자동으로 적절한 형식을 감지합니다.

### Slack Webhook 설정

1. Slack 워크스페이스에서 앱 추가
2. Incoming Webhooks 활성화
3. Webhook URL을 `.env`의 `WEBHOOK_URL`에 설정

### Discord Webhook 설정

1. Discord 서버 설정 > 연동 > 웹후크
2. 새 웹후크 생성
3. Webhook URL을 `.env`의 `WEBHOOK_URL`에 설정

## 식단 이미지 형식

OCR이 올바르게 작동하려면 식단 이미지가 다음 형식을 따라야 합니다:

```
날짜: 2026-01-15
조식: 밥, 국, 김치, 반찬1, 반찬2
중식: 밥, 찌개, 김치, 반찬1, 반찬2, 반찬3
석식: 밥, 국, 김치, 반찬1, 반찬2

날짜: 2026-01-16
...
```

**팁:**
- 깨끗하고 명확한 이미지를 사용하세요
- 한글과 날짜가 잘 보이도록 하세요
- 이미지 형식에 맞게 `ocr_reader.py`의 `_parse_meal_text` 함수를 수정할 수 있습니다

## 시스템 서비스로 실행 (Linux)

스케줄러를 백그라운드 서비스로 실행하려면:

### systemd 서비스 파일 생성

`/etc/systemd/system/ssadan.service`:

```ini
[Unit]
Description=SSADAN Meal Notification Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ssadan
ExecStart=/usr/bin/python3 /path/to/ssadan/main.py run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 서비스 활성화 및 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable ssadan
sudo systemctl start ssadan
sudo systemctl status ssadan
```

## 개발 (Development)

### 코드 구조

- `ocr_reader.py`: OCR 엔진과 텍스트 파싱 로직
- `webhook_notifier.py`: 다양한 webhook 서비스에 대한 알림 전송
- `scheduler.py`: 자동화된 스케줄링 로직
- `main.py`: CLI 인터페이스

### 커스터마이징

1. **다른 이미지 형식**: `ocr_reader.py`의 `_parse_meal_text()` 수정
2. **다른 webhook 서비스**: `webhook_notifier.py`에 새 클래스 추가
3. **알림 형식**: `format_meal_info()` 및 `format_weekly_meals()` 수정

## 문제 해결 (Troubleshooting)

### OCR이 작동하지 않음

- Tesseract가 올바르게 설치되었는지 확인: `tesseract --version`
- 한국어 언어팩 설치: `tesseract --list-langs`에서 'kor' 확인
- 이미지 품질과 형식 확인

### Webhook이 작동하지 않음

- Webhook URL이 올바른지 확인
- 네트워크 연결 확인
- Webhook 서비스의 로그 확인

### 스케줄러가 알림을 보내지 않음

- `.env` 파일의 시간 형식이 올바른지 확인 (HH:MM)
- 시스템 시간대 확인
- 로그에서 에러 메시지 확인

## 라이선스 (License)

MIT License

## 기여 (Contributing)

Pull Request를 환영합니다!
