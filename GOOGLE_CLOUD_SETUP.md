# Google Cloud Document AI 설정 가이드

Google Cloud Document AI를 사용하여 식단표 이미지에서 테이블을 정확하게 추출하는 방법입니다.

## 📋 사전 준비

- Google 계정
- 신용카드 (무료 크레딧 사용, 월 4-5번 사용 시 무료 범위 내)

## 🚀 설정 단계

### 1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단 프로젝트 선택 > "새 프로젝트" 클릭
3. 프로젝트 이름 입력 (예: `ssadan-ocr`)
4. "만들기" 클릭

### 2. Document AI API 활성화

1. 좌측 메뉴 > "API 및 서비스" > "라이브러리"
2. "Document AI API" 검색
3. "사용 설정" 클릭

### 3. Document AI Processor 생성

1. 좌측 메뉴 > "Document AI" 선택
2. "프로세서 만들기" 또는 "Processors" 클릭
3. Processor 유형 선택:
   - **Form Parser** 선택 (테이블 인식에 최적)
4. Processor 이름 입력 (예: `meal-schedule-parser`)
5. 리전 선택 (예: `us`, `eu`, `asia`)
6. "만들기" 클릭
7. **Processor ID 복사** (예: `1234567890abcdef`)

### 4. 서비스 계정 생성 및 키 다운로드

1. 좌측 메뉴 > "IAM 및 관리자" > "서비스 계정"
2. "서비스 계정 만들기" 클릭
3. 서비스 계정 세부정보:
   - 이름: `ssadan-bot` (또는 원하는 이름)
   - ID: 자동 생성됨
4. "만들고 계속하기" 클릭
5. 역할 부여:
   - "역할 선택" > "Document AI API User" 검색 및 선택
6. "계속" 클릭
7. "완료" 클릭
8. 생성된 서비스 계정 클릭
9. "키" 탭 > "키 추가" > "새 키 만들기"
10. 키 유형: **JSON** 선택
11. "만들기" 클릭
12. **JSON 파일 다운로드** (안전한 곳에 보관)

### 5. 프로젝트 ID 확인

1. Google Cloud Console 상단 프로젝트 선택기 클릭
2. 프로젝트 ID 복사 (예: `ssadan-ocr-123456`)

## 🔐 GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 Secret 추가:

### 1. GOOGLE_CLOUD_CREDENTIALS
- 다운로드한 JSON 파일의 **전체 내용**을 복사
- 한 줄로 복사해도 되고, 여러 줄로 복사해도 됨
- 예시:
```json
{
  "type": "service_account",
  "project_id": "ssadan-ocr-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "ssadan-bot@ssadan-ocr-123456.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### 2. GOOGLE_CLOUD_PROJECT_ID
- 프로젝트 ID 입력 (예: `ssadan-ocr-123456`)

### 3. GOOGLE_CLOUD_PROCESSOR_ID
- Processor ID 입력 (예: `1234567890abcdef`)

### 4. GOOGLE_CLOUD_LOCATION
- Processor 생성 시 선택한 리전 (예: `us`, `eu`, `asia`)

## 💰 비용

- **무료 할당량**: 월 1,000페이지
- 월 4-5번 사용 시 완전 무료
- 추가 사용 시: 페이지당 $0.01 ~ $0.05

## ✅ 테스트

로컬에서 테스트:

```bash
# .env 파일 설정
cp .env.example .env
nano .env

# 환경 변수 설정 후 실행
cd src
python main.py ocr --image ../meal_schedule.jpg --db ../db
```

## 🔧 문제 해결

### "API not enabled" 오류
- Document AI API가 활성화되지 않음
- Google Cloud Console > API 및 서비스 > 라이브러리에서 활성화

### "Permission denied" 오류
- 서비스 계정에 "Document AI API User" 역할이 없음
- IAM 및 관리자 > 서비스 계정에서 역할 추가

### "Processor not found" 오류
- Processor ID가 잘못됨
- Document AI > Processors에서 ID 재확인

### JSON 파싱 오류
- JSON 키 형식이 잘못됨
- 다운로드한 JSON 파일 전체 내용을 그대로 복사

## 📚 참고 자료

- [Document AI 문서](https://cloud.google.com/document-ai/docs)
- [Form Parser 가이드](https://cloud.google.com/document-ai/docs/form-parser)
- [가격 정보](https://cloud.google.com/document-ai/pricing)
