"""웰스토리 API를 통한 식단 데이터 크롤링 및 Markdown 변환"""
import requests
import os
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone


class WelstoryCrawler:
    """웰스토리 모바일 API를 사용한 식단 데이터 크롤링"""

    BASE_URL = "https://welplus.welstory.com"
    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Welplus/1.01.08"
    )

    def __init__(self):
        self.username = os.getenv("WELSTORY_USERNAME")
        self.password = os.getenv("WELSTORY_PASSWORD")
        self.restaurant_code = os.getenv("WELSTORY_RESTAURANT_CODE")
        self.token = None
        # 요청마다 고유한 디바이스 ID 생성
        self.base_headers = {
            "X-Device-Id": str(uuid.uuid4()).upper(),
            "X-Autologin": "Y",
            "User-Agent": self.USER_AGENT,
        }

        if not self.username or not self.password:
            raise ValueError(
                "WELSTORY_USERNAME과 WELSTORY_PASSWORD 환경 변수가 필요합니다."
            )
        if not self.restaurant_code:
            raise ValueError(
                "WELSTORY_RESTAURANT_CODE 환경 변수가 필요합니다."
            )

    def login(self) -> bool:
        """웰스토리 API 로그인 후 토큰 획득"""
        url = f"{self.BASE_URL}/login"
        headers = self.base_headers.copy()
        headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                "Authorization": "Bearer null",
            }
        )
        data = {
            "username": self.username,
            "password": self.password,
            "remember-me": "true",
        }

        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            if response.status_code == 200:
                self.token = response.headers.get("Authorization")
                print("✓ 웰스토리 로그인 성공")
                return True
            else:
                print(f"✗ 웰스토리 로그인 실패: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ 웰스토리 로그인 오류: {str(e)}")
            return False

    def fetch_daily_meal_list(self, date: datetime) -> List[dict]:
        """특정 날짜의 점심 식단 목록 조회"""
        if not self.token:
            raise ValueError("로그인이 필요합니다.")

        url = f"{self.BASE_URL}/api/meal"
        headers = self.base_headers.copy()
        headers["Authorization"] = self.token

        params = {
            "menuDt": date.strftime("%Y%m%d"),
            "menuMealType": "2",  # 2=점심
            "restaurantCode": self.restaurant_code,
            "sortingFlag": "",
            "mainDivRestaurantCode": self.restaurant_code,
            "activeRestaurantCode": self.restaurant_code,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("mealList", [])
            else:
                print(f"⚠️  {date.strftime('%Y-%m-%d')} 식단 조회 실패: HTTP {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️  {date.strftime('%Y-%m-%d')} 식단 조회 오류: {str(e)}")
            return []

    def fetch_weekly_meal_data(self, reference_date: Optional[datetime] = None) -> Dict[str, Dict[str, str]]:
        """
        한 주(월~금)의 식단 데이터 조회

        Args:
            reference_date: 기준 날짜 (KST). None이면 오늘 기준

        Returns:
            Dict[날짜 문자열 (YYYY-MM-DD), Dict[코너명, 메뉴 내용]]
        """
        kst = timezone(timedelta(hours=9))
        if reference_date is None:
            reference_date = datetime.now(kst)

        # 해당 주 월요일 계산
        days_since_monday = reference_date.weekday()
        monday = reference_date - timedelta(days=days_since_monday)

        meal_data: Dict[str, Dict[str, str]] = {}

        for day_offset in range(5):  # 월~금
            day = monday + timedelta(days=day_offset)
            date_str = day.strftime("%Y-%m-%d")
            meal_data[date_str] = {}

            print(f"  📡 {date_str} 식단 조회 중...")
            meal_list = self.fetch_daily_meal_list(day)

            for meal in meal_list:
                course_txt = meal.get("courseTxt", "").strip()
                if not course_txt:
                    continue

                menu_name = meal.get("menuName", "").strip()
                sub_menu_txt = meal.get("subMenuTxt", "").strip()

                # 메뉴명과 구성 항목 합치기
                parts = []
                if menu_name:
                    parts.append(menu_name)
                if sub_menu_txt:
                    parts.extend(
                        item.strip()
                        for item in sub_menu_txt.split(",")
                        if item.strip()
                    )

                meal_data[date_str][course_txt] = ", ".join(parts)

        return meal_data

    def convert_to_markdown(self, meal_data: Dict[str, Dict[str, str]]) -> str:
        """
        식단 데이터를 Markdown 테이블 형식으로 변환

        Args:
            meal_data: Dict[날짜 (YYYY-MM-DD), Dict[코너명, 메뉴 내용]]

        Returns:
            Markdown 테이블 문자열
        """
        if not meal_data:
            return "식단 데이터가 없습니다."

        dates = sorted(meal_data.keys())
        if not dates:
            return "식단 데이터가 없습니다."

        weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

        # 주간 제목 생성
        start_dt = datetime.strptime(dates[0], "%Y-%m-%d")
        end_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
        week_info = f"{start_dt.strftime('%m/%d')} ~ {end_dt.strftime('%m/%d')}"
        title = f"## 🍴 SSAFY 주간메뉴표 ({week_info})\n\n"

        # 헤더 행
        header = "| 구분 |"
        separator = "| :--- |"
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = weekday_names[dt.weekday()]
            header += f" {dt.strftime('%m월 %d일')} ({weekday}) |"
            separator += " :--- |"

        # 전체 코너 목록 수집 (순서 유지)
        all_courses: List[str] = []
        seen = set()
        for date_str in dates:
            for course in meal_data[date_str]:
                if course not in seen:
                    all_courses.append(course)
                    seen.add(course)

        # 데이터 행 생성
        rows = []
        for course in all_courses:
            row = f"| **{course}** |"
            for date_str in dates:
                menu_text = meal_data[date_str].get(course, "-")
                row += f" {menu_text} |"
            rows.append(row)

        lines = [header, separator] + rows
        return title + "\n".join(lines) + "\n"

    def save_to_file(self, markdown_content: str, date_str: str, db_path: str = "db") -> str:
        """
        Markdown 내용을 파일로 저장

        Args:
            markdown_content: 저장할 Markdown 내용
            date_str: 파일 이름에 사용할 날짜 (YYYY-MM-DD)
            db_path: 저장 디렉토리 경로

        Returns:
            저장된 파일 경로
        """
        os.makedirs(db_path, exist_ok=True)
        file_path = os.path.join(db_path, f"{date_str}.md")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✓ Markdown 파일 저장: {file_path}")
        return file_path

    def process_and_save(self, db_path: str = "db") -> Tuple[str, str]:
        """
        웰스토리 API로 이번 주 식단 조회, Markdown 변환, 파일 저장

        Returns:
            (markdown_content, file_path) 튜플. 실패 시 ("", "")
        """
        # 1. 로그인
        if not self.login():
            return "", ""

        # 2. 주간 식단 조회
        kst = timezone(timedelta(hours=9))
        today = datetime.now(kst)
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)

        meal_data = self.fetch_weekly_meal_data(today)

        if not any(meal_data[d] for d in meal_data):
            print("✗ 조회된 식단 데이터가 없습니다.")
            return "", ""

        print(f"✓ {len(meal_data)}개 날짜의 식단 조회 완료")

        # 3. Markdown 변환
        markdown = self.convert_to_markdown(meal_data)

        # 4. 월요일 날짜를 파일 이름으로 저장
        monday_str = monday.strftime("%Y-%m-%d")
        file_path = self.save_to_file(markdown, monday_str, db_path)

        return markdown, file_path
