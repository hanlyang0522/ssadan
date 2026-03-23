# SSADAN - SSAFY 식단 알림 봇 🍽️

매일 Mattermost와 Discord webhook으로 점심 식단을 알려주는 자동화 봇입니다.

## 프로젝트 구조

```
.
├── .github/
│   └── workflows/          # GitHub Actions를 활용한 자동화 스케줄러
│       ├── daily_notify.yml   # 매일 오전 9시 10분 점심 알림
│       └── weekly_crawl.yml   # 매주 월요일 웰스토리 API 식단 자동 크롤링
├── db/                     # 식단 Markdown 파일 저장소 (yyyy-mm-dd.md)
│   └── .gitkeep
├── src/                    # 핵심 실행 로직 (Python)
│   ├── main.py             # 전체 프로세스 제어 (Entry point)
│   ├── welstory_crawler.py # 웰스토리 API 식단 크롤링 및 Markdown 변환
│   ├── mm_sender.py        # Mattermost 웹훅 발송 로직
│   ├── discord_sender.py   # Discord 웹훅 발송 로직
│   └── notification_sender.py  # 통합 알림 발송 (Mattermost + Discord)
├── requirements.txt        # 필요 라이브러리
├── README.md               # 프로젝트 설명
└── .env.example            # 환경변수 샘플
```

## 작동 방법

1. **식단 크롤링**: 매주 월요일 [welplan.pmh.codes](https://welplan.pmh.codes)에서 멀티캠퍼스 한 주(월~금) 식단을 가져와 `db/yyyy-mm-dd.md` 파일로 저장
2. **일일 알림**: 매일 오전 9시 10분~9시 40분(KST)에 그 날 점심 식단을 Mattermost와 Discord로 전송 (GitHub Actions 스케줄링 지연 최대 30분 발생 가능)

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
cp .env.example .env
```

`.env` 파일 설정:
```bash
# Mattermost Webhook URL (식단 알림용)
MATTERMOST_WEBHOOK_URL=https://your-mattermost-server.com/hooks/xxx

# Discord Webhook URL (식단 알림용, 선택사항)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy

# 식당 검색어 (기본값: 멀티캠퍼스, 변경 필요 시만 설정)
# WELSTORY_RESTAURANT_QUERY=멀티캠퍼스
```

**참고**: `MATTERMOST_WEBHOOK_URL` 또는 `DISCORD_WEBHOOK_URL` 중 최소 하나는 설정되어야 합니다.

## 사용법

### 로컬 실행

#### 1. 웰스토리 API로 이번 주 식단 크롤링
```bash
cd src
python main.py crawl --db ../db
```

#### 2. 오늘 점심 식단 전송
```bash
cd src
python main.py daily --db ../db
```

#### 3. 특정 날짜 점심 식단 전송
```bash
cd src
python main.py daily --date 2026-01-15 --db ../db
```

### GitHub Actions 자동화

#### 1. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 Secret 추가:
- `MATTERMOST_WEBHOOK_URL`: Mattermost Incoming Webhook URL (식단 알림용, 선택사항)
- `DISCORD_WEBHOOK_URL`: Discord Webhook URL (식단 알림용, 선택사항)

> **참고**: 식단 크롤링은 [welplan.pmh.codes](https://welplan.pmh.codes)를 통해 인증 없이 진행됩니다.

#### 2. 주간 식단 크롤링

매주 월요일 오전 8시(KST)에 자동으로 실행됩니다.
수동 실행: Actions > "Weekly Menu Crawl (Wellstory API)" > "Run workflow"

#### 3. 일일 알림

매일 오전 9시 10분~9시 40분(KST)에 자동으로 실행됩니다 (GitHub Actions 지연 발생 가능).
수동 실행: Actions > "Daily Lunch Notification" > "Run workflow"

## 출력 형식 예시

```markdown
## 🍴 SSAFY 주간메뉴표 (03월 02일 ~ 03월 06일)

| 구분 | 03월 02일 (월) | 03월 03일 (화) | 03월 04일 (수) | 03월 05일 (목) | 03월 06일 (금) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **20F 일반식 (A. 한식)** | 부대찌개, 현미밥, ... | ... | ... | ... | ... |
| **20F 일반식 (B. 일품)** | 카레라이스 | ... | ... | ... | ... |
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

다른 식당의 식단을 사용하려면 `WELSTORY_RESTAURANT_QUERY` 환경변수를 설정하세요 (기본값: `멀티캠퍼스`).

welplan.pmh.codes API 응답의 코너명(`menuCourseName`)이 원하는 형식과 다를 경우, `src/welstory_crawler.py`의 `fetch_weekly_meal_data()` 메서드에서 처리 부분을 수정하세요.

## 라이선스

MIT License
