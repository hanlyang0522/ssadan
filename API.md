# API Documentation

## Python Modules API

### `ocr_reader.py`

#### Class: `MealOCR`

식단표 이미지에서 OCR을 통해 식단 정보를 추출하는 클래스입니다.

```python
from ocr_reader import MealOCR

ocr = MealOCR(image_path="meal_schedule.jpg")
```

##### Methods

**`read_meal_schedule() -> Dict[str, Dict[str, str]]`**

이미지에서 1주일치 식단 정보를 읽어옵니다.

반환값:
```python
{
    '2026-01-15': {
        'breakfast': '밥, 국, 반찬...',
        'lunch': '밥, 국, 반찬...',
        'dinner': '밥, 국, 반찬...'
    },
    '2026-01-16': { ... }
}
```

**`get_weekly_meals() -> Dict[str, Dict[str, str]]`**

1주일치 식단을 반환합니다. 내부적으로 `read_meal_schedule()`을 호출합니다.

**`get_daily_meal(date: Optional[str] = None) -> Dict[str, str]`**

특정 날짜의 식단을 반환합니다.

파라미터:
- `date`: YYYY-MM-DD 형식의 날짜 문자열. None이면 오늘 날짜 사용.

반환값:
```python
{
    'breakfast': '밥, 국, 반찬...',
    'lunch': '밥, 국, 반찬...',
    'dinner': '밥, 국, 반찬...'
}
```

#### Functions

**`format_meal_info(meals: Dict[str, str], date: str) -> str`**

식단 정보를 사용자 친화적인 문자열로 포맷합니다.

**`format_weekly_meals(weekly_meals: Dict[str, Dict[str, str]]) -> str`**

1주일치 식단을 포맷합니다.

---

### `webhook_notifier.py`

#### Class: `WebhookNotifier`

범용 webhook으로 알림을 전송하는 클래스입니다.

```python
from webhook_notifier import WebhookNotifier

notifier = WebhookNotifier(webhook_url="https://example.com/webhook")
```

##### Methods

**`send_notification(message: str, title: Optional[str] = None) -> bool`**

webhook으로 알림을 전송합니다.

파라미터:
- `message`: 전송할 메시지 내용
- `title`: 선택적 제목

반환값: 성공 시 True, 실패 시 False

**`send_daily_meal(meal_message: str) -> bool`**

일일 식단 알림을 전송합니다.

**`send_weekly_meals(weekly_message: str) -> bool`**

주간 식단 알림을 전송합니다.

#### Class: `SlackWebhookNotifier`

Slack 전용 webhook notifier입니다. `WebhookNotifier`를 상속하며 Slack 메시지 형식을 사용합니다.

```python
from webhook_notifier import SlackWebhookNotifier

notifier = SlackWebhookNotifier(webhook_url="https://hooks.slack.com/services/...")
```

#### Class: `DiscordWebhookNotifier`

Discord 전용 webhook notifier입니다. Discord embed 형식을 사용합니다.

```python
from webhook_notifier import DiscordWebhookNotifier

notifier = DiscordWebhookNotifier(webhook_url="https://discord.com/api/webhooks/...")
```

---

### `scheduler.py`

#### Class: `MealNotificationScheduler`

자동화된 식단 알림 스케줄러입니다.

```python
from scheduler import MealNotificationScheduler

scheduler = MealNotificationScheduler()
scheduler.run()  # 스케줄러 실행
```

##### Methods

**`send_daily_notification()`**

오늘의 식단 알림을 즉시 전송합니다.

**`send_weekly_notification()`**

주간 식단 알림을 즉시 전송합니다.

**`setup_schedule()`**

`.env` 파일의 설정에 따라 스케줄을 설정합니다.

**`run()`**

스케줄러를 지속적으로 실행합니다 (blocking).

---

### `main.py`

#### CLI Commands

**`test-ocr`**

OCR 기능을 테스트합니다.

```bash
python main.py test-ocr --image meal_schedule.jpg
```

**`test-webhook`**

Webhook 전송을 테스트합니다.

```bash
python main.py test-webhook --url https://example.com/webhook
```

**`send-daily`**

일일 식단 알림을 즉시 전송합니다.

```bash
python main.py send-daily [--image IMAGE] [--url URL] [--date DATE]
```

**`send-weekly`**

주간 식단 알림을 즉시 전송합니다.

```bash
python main.py send-weekly [--image IMAGE] [--url URL]
```

**`run`**

스케줄러를 실행합니다.

```bash
python main.py run
```

---

## 환경 변수

### `.env` 파일 설정

**`WEBHOOK_URL`** (필수)

Webhook 엔드포인트 URL

예: `https://hooks.slack.com/services/...`

**`MEAL_IMAGE_PATH`** (기본값: `./meal_schedule.jpg`)

식단표 이미지 파일 경로

**`DAILY_NOTIFICATION_TIME`** (기본값: `08:00`)

일일 알림 시간 (HH:MM 형식, 24시간제)

**`WEEKLY_NOTIFICATION_DAY`** (기본값: `0`)

주간 알림 요일
- 0: 월요일
- 1: 화요일
- 2: 수요일
- 3: 목요일
- 4: 금요일
- 5: 토요일
- 6: 일요일

**`WEEKLY_NOTIFICATION_TIME`** (기본값: `09:00`)

주간 알림 시간 (HH:MM 형식, 24시간제)

---

## 코드 예제

### 기본 OCR 사용

```python
from ocr_reader import MealOCR, format_meal_info

# OCR 인스턴스 생성
ocr = MealOCR("meal_schedule.jpg")

# 식단 읽기
meals = ocr.read_meal_schedule()

# 오늘 식단 가져오기
today_meal = ocr.get_daily_meal()

# 포맷하기
formatted = format_meal_info(today_meal, "2026-01-15")
print(formatted)
```

### 기본 Webhook 사용

```python
from webhook_notifier import WebhookNotifier

# Notifier 생성
notifier = WebhookNotifier("https://example.com/webhook")

# 메시지 전송
success = notifier.send_notification(
    message="안녕하세요!",
    title="테스트 알림"
)

if success:
    print("전송 성공!")
```

### 완전한 워크플로우

```python
from ocr_reader import MealOCR, format_meal_info
from webhook_notifier import SlackWebhookNotifier
from datetime import datetime

# 1. OCR로 식단 읽기
ocr = MealOCR("meal_schedule.jpg")
meals = ocr.read_meal_schedule()

# 2. 오늘 날짜의 식단 가져오기
today = datetime.now().strftime('%Y-%m-%d')
today_meal = meals.get(today, {})

# 3. 포맷하기
message = format_meal_info(today_meal, today)

# 4. Slack으로 전송
notifier = SlackWebhookNotifier("https://hooks.slack.com/services/...")
notifier.send_daily_meal(message)
```

### 커스텀 스케줄러

```python
import schedule
import time
from ocr_reader import MealOCR, format_meal_info
from webhook_notifier import WebhookNotifier

def send_meal_notification():
    ocr = MealOCR("meal.jpg")
    meal = ocr.get_daily_meal()
    message = format_meal_info(meal, datetime.now().strftime('%Y-%m-%d'))
    
    notifier = WebhookNotifier("https://example.com/webhook")
    notifier.send_daily_meal(message)

# 매일 오전 8시에 실행
schedule.every().day.at("08:00").do(send_meal_notification)

# 월요일 오전 9시에 주간 알림
schedule.every().monday.at("09:00").do(send_weekly_notification)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 확장하기

### 새로운 Webhook 서비스 추가

```python
from webhook_notifier import WebhookNotifier

class CustomWebhookNotifier(WebhookNotifier):
    """커스텀 webhook 서비스"""
    
    def send_notification(self, message: str, title: Optional[str] = None) -> bool:
        try:
            # 커스텀 payload 형식
            payload = {
                "your_custom_field": message,
                "title": title
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False
```

### 커스텀 OCR 파서

식단표 형식이 다를 경우 `ocr_reader.py`의 `_parse_meal_text()` 메서드를 오버라이드:

```python
from ocr_reader import MealOCR

class CustomMealOCR(MealOCR):
    def _parse_meal_text(self, text: str):
        # 커스텀 파싱 로직
        meal_data = {}
        
        # 예: 다른 형식의 날짜/식사 파싱
        # ...
        
        return meal_data
```

---

## 테스트

유닛 테스트 실행:

```bash
python -m unittest test_bot.py -v
```

특정 테스트만 실행:

```bash
python -m unittest test_bot.TestMealOCR.test_parse_meal_text_basic
```
