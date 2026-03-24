"""Gemini API를 이용한 10층 식단 이미지 파싱 모듈"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict

from google import genai
from google.genai import types


FLOOR_10_COURSES = ["10F 공존 (도시락)", "10F 공존 (브런치)", "10F 공존 (샐러드)"]
KST = timezone(timedelta(hours=9))

_PARSE_PROMPT = """이 이미지는 SSAFY 멀티캠퍼스 10층 공존 식당의 주간 식단표입니다.
아래 형식으로 월요일부터 금요일까지 각 날짜의 메뉴를 추출해 주세요.

출력 형식 (각 줄):
날짜(YYYY-MM-DD)|코너|메뉴내용

코너는 반드시 다음 세 가지 중 하나:
- 10F 공존 (도시락)
- 10F 공존 (브런치)
- 10F 공존 (샐러드)

메뉴 항목은 " & " 또는 ", "로 구분하세요.
이미지에서 날짜를 확인할 수 없는 경우 날짜를 비워 두세요(|코너|메뉴).
다른 설명 없이 위 형식의 텍스트만 출력하세요."""


def parse_floor10_image(image_path: str, reference_date: datetime = None) -> Dict[str, Dict[str, str]]:
    """
    Gemini API로 10층 식단 이미지를 파싱

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

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
            _PARSE_PROMPT,
        ],
    )

    text = response.text.strip()
    return _parse_response(text, reference_date)


def _get_monday(reference: datetime = None) -> datetime:
    """해당 주 월요일 반환 (KST)"""
    if reference is None:
        reference = datetime.now(KST)
    days_since_monday = reference.weekday()
    return reference - timedelta(days=days_since_monday)


def _parse_response(text: str, reference_date: datetime = None) -> Dict[str, Dict[str, str]]:
    """Gemini 응답 텍스트를 파싱하여 구조화된 데이터 반환"""
    monday = _get_monday(reference_date)
    # 월~금 날짜 목록
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

    result: Dict[str, Dict[str, str]] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) < 3:
            continue

        date_str, course, menu = parts[0].strip(), parts[1].strip(), parts[2].strip()

        # 날짜가 없으면 스킵 (매핑 불가)
        if not date_str or not course or not menu:
            continue

        # 날짜 형식 검증
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        if date_str not in week_dates:
            continue

        if course not in FLOOR_10_COURSES:
            continue

        if date_str not in result:
            result[date_str] = {}
        result[date_str][course] = menu

    if not result:
        raise ValueError(
            f"Gemini 응답에서 유효한 식단 데이터를 파싱할 수 없습니다.\n응답: {text[:200]}{'...' if len(text) > 200 else ''}"
        )

    return result
