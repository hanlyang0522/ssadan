"""Gemini API를 이용한 10층 식단 이미지 파싱 모듈"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict

from google import genai
from google.genai import types


FLOOR_10_COURSES = ["10F 공존 (도시락)", "10F 공존 (브런치)", "10F 공존 (샐러드)"]
KST = timezone(timedelta(hours=9))

_WEEKDAY_NAMES = ["월", "화", "수", "목", "금"]


def _build_prompt(reference_date: datetime = None) -> str:
    """이번 주 날짜를 포함한 Markdown 테이블 템플릿 프롬프트 생성"""
    monday = _get_monday(reference_date)
    dates = [monday + timedelta(days=i) for i in range(5)]

    header_dates = " | ".join(
        f"{d.strftime('%m월 %d일')} ({_WEEKDAY_NAMES[i]})" for i, d in enumerate(dates)
    )
    template = (
        f"| 구분 | {header_dates} |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| **10F 공존 (도시락)** | ? | ? | ? | ? | ? |\n"
        "| **10F 공존 (브런치)** | ? | ? | ? | ? | ? |\n"
        "| **10F 공존 (샐러드)** | ? | ? | ? | ? | ? |"
    )

    return (
        "제공된 이미지에서 식단표에서 메뉴 추출해서 아래 테이블표 형식에 맞춰 이번주 식단표 만들어줘.\n\n"
        f"{template}\n\n"
        "출력 규칙:\n"
        "- 위 테이블에서 ? 부분만 실제 메뉴로 채워서 동일한 Markdown 테이블 형식으로 출력하세요.\n"
        "- 도시락 메뉴 항목은 쉼표(,)로 구분하세요.\n"
        "- 브런치/샐러드 메뉴 항목은 & 로 구분하세요.\n"
        "- 이미지에서 해당 날짜/코너의 메뉴가 없으면 - 로 표시하세요.\n"
        "- 다른 설명 없이 Markdown 테이블만 출력하세요."
    )


_MAX_RETRIES = 10


def parse_floor10_image(image_path: str, reference_date: datetime = None) -> Dict[str, Dict[str, str]]:
    """
    Gemini API로 10층 식단 이미지를 파싱.
    파싱 결과에 미완성 항목이 있으면 최대 10회까지 재시도하며 성공 항목을 누적.

    Args:
        image_path: 이미지 파일 경로
        reference_date: 해당 주의 임의 날짜 (KST). None이면 오늘 기준 계산

    Returns:
        Dict[날짜 문자열 (YYYY-MM-DD), Dict[코너명, 메뉴 내용]]

    Raises:
        Exception: 파싱 실패 시
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    with open(image_path, "rb") as f:
        image_data = f.read()

    ext = image_path.rsplit(".", 1)[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    mime_type = mime_map.get(ext, "image/jpeg")

    prompt = _build_prompt(reference_date)
    monday = _get_monday(reference_date)
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    # 파싱 성공 기준: 모든 날짜 × 모든 코너가 채워진 경우
    total_expected = len(week_dates) * len(FLOOR_10_COURSES)

    accumulated: Dict[str, Dict[str, str]] = {}

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=image_data, mime_type=mime_type),
                    prompt,
                ],
            )
            text = response.text.strip()
            parsed = _parse_response(text, reference_date)

            # 새로 파싱된 결과를 누적 (기존 성공 항목은 유지)
            for date_str, courses in parsed.items():
                if date_str not in accumulated:
                    accumulated[date_str] = {}
                for course, menu in courses.items():
                    if course not in accumulated[date_str]:
                        accumulated[date_str][course] = menu

        except ValueError:
            pass  # 파싱 실패 시 누적 결과 그대로 유지

        # 모든 항목이 채워졌는지 확인
        filled = sum(
            len(accumulated.get(d, {})) for d in week_dates
        )
        remaining = total_expected - filled
        if remaining == 0:
            if attempt > 1:
                print(f"✓ {attempt}회 시도 후 모든 10층 식단 파싱 완료")
            break

        if attempt < _MAX_RETRIES:
            print(f"⚠️  미완성 항목 {remaining}개, retry {attempt}/{_MAX_RETRIES}...")

    if not accumulated:
        raise ValueError("Gemini 파싱 실패: 최대 재시도 횟수 초과 후에도 유효한 데이터 없음")

    return accumulated


def _get_monday(reference: datetime = None) -> datetime:
    """해당 주 월요일 반환 (KST)"""
    if reference is None:
        reference = datetime.now(KST)
    days_since_monday = reference.weekday()
    return reference - timedelta(days=days_since_monday)


def _parse_response(text: str, reference_date: datetime = None) -> Dict[str, Dict[str, str]]:
    """Gemini Markdown 테이블 응답을 파싱하여 구조화된 데이터 반환"""
    monday = _get_monday(reference_date)
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

    result: Dict[str, Dict[str, str]] = {}

    for line in text.splitlines():
        line = line.strip()
        # 구분자 행 또는 헤더 행 건너뜀
        if not line.startswith("|") or ":---" in line or "구분" in line:
            continue

        cols = [c.strip() for c in line.split("|")]
        # 앞뒤 빈 요소 제거 (split 결과 양끝 "")
        cols = [c for c in cols if c != ""]

        if len(cols) < 6:
            continue

        # 첫 번째 컬럼에서 코너명 추출 (**...** 마커 제거)
        course = cols[0].replace("**", "").strip()
        if course not in FLOOR_10_COURSES:
            continue

        # 날짜별 메뉴 매핑
        for i, date_str in enumerate(week_dates):
            if i + 1 >= len(cols):
                break
            menu = cols[i + 1].strip()
            if menu and menu != "-":
                if date_str not in result:
                    result[date_str] = {}
                result[date_str][course] = menu

    if not result:
        raise ValueError(
            f"Gemini 응답에서 유효한 식단 데이터를 파싱할 수 없습니다.\n응답: {text[:200]}{'...' if len(text) > 200 else ''}"
        )

    return result
