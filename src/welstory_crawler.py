"""웰스토리 식단 데이터 크롤링 및 Markdown 변환 (welplan.pmh.codes API 사용)"""
import requests
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone


class WelstoryCrawler:
    """welplan.pmh.codes API를 통한 멀티캠퍼스 식단 데이터 크롤링 (인증 불필요)"""

    WELPLAN_BASE_URL = "https://welplan.pmh.codes"
    DEFAULT_RESTAURANT_QUERY = "멀티캠퍼스"
    FLOOR_10_COURSES = ["10F 공존 (도시락)", "10F 공존 (브런치)", "10F 공존 (샐러드)"]
    FLOOR_10_PLACEHOLDER = "준비중..."

    def __init__(self):
        self.restaurant_query = os.getenv(
            "WELSTORY_RESTAURANT_QUERY", self.DEFAULT_RESTAURANT_QUERY
        )

    def _search_restaurant(self) -> Optional[dict]:
        """식당 검색 후 식당 데이터 반환"""
        url = f"{self.WELPLAN_BASE_URL}/api/restaurants/search"
        try:
            response = requests.post(
                url,
                json={"searchQuery": self.restaurant_query},
                timeout=30,
            )
            if response.status_code == 200:
                restaurants = response.json().get("restaurants", [])
                if restaurants:
                    print(f"✓ 식당 검색 성공: {restaurants[0]['name']}")
                    return restaurants[0]
                print(f"✗ '{self.restaurant_query}' 식당을 찾을 수 없습니다.")
                return None
            else:
                print(f"✗ 식당 검색 실패: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ 식당 검색 오류: {str(e)}")
            return None

    def _get_lunch_meal_time_id(self, restaurant_data: dict) -> Optional[str]:
        """점심 식사 시간 ID 조회"""
        url = f"{self.WELPLAN_BASE_URL}/api/restaurants/meal-times"
        try:
            response = requests.post(
                url,
                json={"restaurantData": restaurant_data},
                timeout=30,
            )
            if response.status_code == 200:
                meal_times = response.json().get("mealTimes", [])
                for mt in meal_times:
                    name = mt.get("name", "")
                    if any(kw in name for kw in ["중식", "점심", "Lunch"]):
                        print(f"✓ 점심 식사 시간: {name} (ID: {mt['id']})")
                        return mt["id"]
                # 점심 키워드를 찾지 못하면 첫 번째 사용
                if meal_times:
                    first = meal_times[0]
                    print(f"⚠️  점심 식사 시간 미확인, 첫 번째 사용: {first['name']}")
                    return first["id"]
                print("✗ 식사 시간 정보가 없습니다.")
                return None
            else:
                print(f"✗ 식사 시간 조회 실패: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ 식사 시간 조회 오류: {str(e)}")
            return None

    def fetch_daily_meal_list(
        self, date: datetime, restaurant_data: dict, meal_time_id: str
    ) -> List[dict]:
        """특정 날짜의 점심 식단 목록 조회"""
        url = f"{self.WELPLAN_BASE_URL}/api/restaurants/meals"
        try:
            response = requests.post(
                url,
                json={
                    "restaurantData": restaurant_data,
                    "date": date.strftime("%Y%m%d"),
                    "mealTimeId": meal_time_id,
                },
                timeout=30,
            )
            if response.status_code == 200:
                return response.json().get("meals", [])
            else:
                print(
                    f"⚠️  {date.strftime('%Y-%m-%d')} 식단 조회 실패: HTTP {response.status_code}"
                )
                return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️  {date.strftime('%Y-%m-%d')} 식단 조회 오류: {str(e)}")
            return []

    def fetch_weekly_meal_data(
        self, reference_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, str]]:
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

        # 식당 검색
        restaurant_data = self._search_restaurant()
        if not restaurant_data:
            return {}

        # 점심 식사 시간 ID 조회
        meal_time_id = self._get_lunch_meal_time_id(restaurant_data)
        if not meal_time_id:
            return {}

        meal_data: Dict[str, Dict[str, str]] = {}

        for day_offset in range(5):  # 월~금
            day = monday + timedelta(days=day_offset)
            date_str = day.strftime("%Y-%m-%d")
            meal_data[date_str] = {}

            print(f"  📡 {date_str} 식단 조회 중...")
            meal_list = self.fetch_daily_meal_list(day, restaurant_data, meal_time_id)

            for meal in meal_list:
                # welplan API: menuCourseName = 코너명(courseTxt), name = 메뉴명(menuName)
                course_name = meal.get("menuCourseName", "").strip()
                if not course_name:
                    continue

                menu_name = meal.get("name", "").strip()
                sub_menu_txt = meal.get("subMenuTxt") or ""
                sub_menu_txt = sub_menu_txt.strip()

                meal_data[date_str][course_name] = self._merge_menu_parts(
                    menu_name,
                    sub_menu_txt,
                )

            # 10F 공존 코너는 API 미제공으로 '준비중...' 처리
            for course in self.FLOOR_10_COURSES:
                meal_data[date_str][course] = self.FLOOR_10_PLACEHOLDER

        return meal_data

    @staticmethod
    def _merge_menu_parts(menu_name: str, sub_menu_txt: str) -> str:
        """메뉴명과 서브메뉴를 순서대로 병합하고 중복 항목 제거"""
        parts: List[str] = []

        if menu_name:
            parts.append(menu_name)

        if sub_menu_txt:
            parts.extend(
                item.strip()
                for item in sub_menu_txt.split(",")
                if item.strip()
            )

        unique_parts: List[str] = []
        seen = set()
        for part in parts:
            if part not in seen:
                unique_parts.append(part)
                seen.add(part)

        return ", ".join(unique_parts)

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
        week_info = f"{start_dt.strftime('%m월 %d일')} ~ {end_dt.strftime('%m월 %d일')}"
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

    def merge_floor10_data(
        self,
        meal_data: Dict[str, Dict[str, str]],
        floor10_data: Dict[str, Dict[str, str]],
    ) -> None:
        """
        10층 파싱 결과를 meal_data에 병합 (성공한 날짜/코너만 덮어쓰기)

        Args:
            meal_data: 기존 주간 식단 데이터 (수정됨)
            floor10_data: 10층 파싱 결과
        """
        for date_str, courses in floor10_data.items():
            if date_str not in meal_data:
                continue
            for course, menu in courses.items():
                if menu and menu != self.FLOOR_10_PLACEHOLDER:
                    meal_data[date_str][course] = menu

    def process_and_save(self, db_path: str = "db") -> Tuple[str, str]:
        """
        welplan.pmh.codes API로 이번 주 식단 조회, Markdown 변환, 파일 저장

        Returns:
            (markdown_content, file_path) 튜플. 실패 시 ("", "")
        """
        # 1. 주간 식단 조회
        kst = timezone(timedelta(hours=9))
        today = datetime.now(kst)
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)

        meal_data = self.fetch_weekly_meal_data(today)

        if not any(meal_data[d] for d in meal_data):
            print("✗ 조회된 식단 데이터가 없습니다.")
            return "", ""

        print(f"✓ {len(meal_data)}개 날짜의 식단 조회 완료")

        # 2. Markdown 변환
        markdown = self.convert_to_markdown(meal_data)

        # 3. 월요일 날짜를 파일 이름으로 저장
        monday_str = monday.strftime("%Y-%m-%d")
        file_path = self.save_to_file(markdown, monday_str, db_path)

        return markdown, file_path
