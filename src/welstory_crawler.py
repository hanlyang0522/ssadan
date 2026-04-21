"""웰스토리 식단 데이터 크롤링 및 Markdown 변환 (Welstory Plus API 직접 사용)"""
import requests
import os
import uuid
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone


class WelstoryCrawler:
    """Welstory Plus API를 통한 멀티캠퍼스 식단 데이터 크롤링"""

    WELSTORY_BASE_URL = "https://welplus.welstory.com"
    DEFAULT_RESTAURANT_QUERY = "멀티캠퍼스"
    FLOOR_10_COURSES = ["10F 공존 (도시락)", "10F 공존 (브런치)", "10F 공존 (샐러드)"]
    FLOOR_10_PLACEHOLDER = "준비중..."

    # 메뉴 문자열 분리에 사용하는 공통 구분자
    MENU_SPLIT_PATTERN = re.compile(r"\s*<br\s*/?>\s*|\s*[,/\n]\s*", re.IGNORECASE)

    def __init__(self):
        self.restaurant_query = os.getenv(
            "WELSTORY_RESTAURANT_QUERY", self.DEFAULT_RESTAURANT_QUERY
        )
        self.username = os.getenv("WELSTORY_USERNAME", "")
        self.password = os.getenv("WELSTORY_PASSWORD", "")
        self.device_id = os.getenv("WELSTORY_DEVICE_ID", str(uuid.uuid4()))
        self._token: Optional[str] = None

    def _login(self) -> Optional[str]:
        """Welstory Plus 로그인 후 JWT 토큰 반환"""
        if not self.username or not self.password:
            print("✗ WELSTORY_USERNAME / WELSTORY_PASSWORD 환경변수가 설정되지 않았습니다.")
            return None
        url = f"{self.WELSTORY_BASE_URL}/login"
        try:
            response = requests.post(
                url,
                data={
                    "username": self.username,
                    "password": self.password,
                    "remember-me": "false",
                },
                headers={
                    "User-Agent": "Welplus",
                    "X-Device-Id": self.device_id,
                    "X-Autologin": "N",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=30,
                allow_redirects=False,
            )
            if response.status_code == 200:
                token = response.headers.get("Authorization")
                if token:
                    self._token = token
                    return token
                print("✗ 로그인 응답에 Authorization 헤더가 없습니다.")
                return None
            else:
                print(f"✗ 로그인 실패: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ 로그인 오류: {str(e)}")
            return None

    def _get_token(self) -> Optional[str]:
        """JWT 토큰 반환 (없으면 로그인)"""
        if self._token:
            return self._token
        return self._login()

    def _auth_headers(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        return {
            "User-Agent": "Welplus",
            "X-Device-Id": self.device_id,
            "Authorization": self._token or "",
        }

    def _search_restaurant(self) -> Optional[dict]:
        """식당 검색 후 식당 데이터 반환"""
        if not self._get_token():
            return None
        url = f"{self.WELSTORY_BASE_URL}/api/mypage/rest-list"
        try:
            response = requests.get(
                url,
                params={"restaurantName": self.restaurant_query},
                headers=self._auth_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(restaurants, list) and restaurants:
                    print(f"✓ 식당 검색 성공: {restaurants[0]['restaurantName']}")
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
        if not self._get_token():
            return None
        restaurant_id = restaurant_data.get("restaurantId", "")
        url = f"{self.WELSTORY_BASE_URL}/api/menu/getMealTimeList"
        try:
            headers = {**self._auth_headers(), "Cookie": f"cafeteriaActiveId={restaurant_id}"}
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                meal_times = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(meal_times, list):
                    for mt in meal_times:
                        name = mt.get("codeNm", "")
                        if any(kw in name for kw in ["중식", "점심", "Lunch"]):
                            print(f"✓ 점심 식사 시간: {name} (ID: {mt['code']})")
                            return mt["code"]
                    # 점심 키워드를 찾지 못하면 첫 번째 사용
                    if meal_times:
                        first = meal_times[0]
                        print(f"⚠️  점심 식사 시간 미확인, 첫 번째 사용: {first['codeNm']}")
                        return first["code"]
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
        if not self._get_token():
            return []
        restaurant_id = restaurant_data.get("restaurantId", "")
        url = f"{self.WELSTORY_BASE_URL}/api/meal"
        try:
            response = requests.get(
                url,
                params={
                    "menuDt": date.strftime("%Y%m%d"),
                    "menuMealType": meal_time_id,
                    "restaurantCode": restaurant_id,
                },
                headers=self._auth_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                wrapper = data.get("data", {}) if isinstance(data, dict) else {}
                return wrapper.get("mealList", [])
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

            # Welstory 응답 구조 변동(평면/중첩)에 대응해 코너별 메뉴를 수집
            # 기존 hallNo + menuCourseType 기준 필터링은 서브 메뉴를 누락시킬 수 있다.
            for dish in meal_list:
                course_name = self._extract_course_name(dish)
                if not course_name:
                    continue

                menu_names = self._extract_menu_names(dish)
                if not menu_names:
                    continue

                existing = meal_data[date_str].get(course_name, "")
                existing_names = [m.strip() for m in existing.split(",") if m.strip()]
                merged_names = self._merge_unique(existing_names, menu_names)
                meal_data[date_str][course_name] = ", ".join(merged_names)

            # 10F 공존 코너는 API 미제공으로 '준비중...' 처리
            for course in self.FLOOR_10_COURSES:
                meal_data[date_str][course] = self.FLOOR_10_PLACEHOLDER

        return meal_data

    def _extract_course_name(self, dish: dict) -> str:
        """Welstory 항목에서 코너명 후보를 순서대로 추출"""
        candidates = [
            dish.get("courseTxt", ""),
            dish.get("menuCourseNm", ""),
            dish.get("menuCourseName", ""),
            dish.get("cornerNm", ""),
            dish.get("cornerName", ""),
        ]
        for name in candidates:
            normalized = str(name).strip()
            if normalized:
                return normalized
        return ""

    def _extract_menu_names(self, dish: dict) -> List[str]:
        """Welstory 항목에서 메뉴명을 최대한 수집"""
        names: List[str] = []

        # 1) 대표/단일 메뉴 필드
        for key in ["menuName", "menuNm", "mainMenuName", "menu"]:
            value = dish.get(key)
            if isinstance(value, str):
                names.extend(self._split_menu_text(value))

        # 2) 문자열로 합쳐진 서브 메뉴 필드
        for key in ["subMenuTxt", "subMenuText", "menuText", "menuDesc", "menuDescription"]:
            value = dish.get(key)
            if isinstance(value, str):
                names.extend(self._split_menu_text(value))

        # 3) 중첩 리스트 필드 (응답 구조 변경 대응)
        list_keys = ["menuList", "subMenuList", "menuNmList", "menuInfoList", "items"]
        for list_key in list_keys:
            nested = dish.get(list_key)
            if not isinstance(nested, list):
                continue
            for item in nested:
                if isinstance(item, str):
                    names.extend(self._split_menu_text(item))
                    continue
                if not isinstance(item, dict):
                    continue
                for key in ["menuName", "menuNm", "name", "menu"]:
                    value = item.get(key)
                    if isinstance(value, str):
                        names.extend(self._split_menu_text(value))

        return self._merge_unique([], names)

    def _split_menu_text(self, text: str) -> List[str]:
        """합쳐진 메뉴 문자열을 개별 메뉴로 분리"""
        raw = text.strip()
        if not raw:
            return []
        parts = self.MENU_SPLIT_PATTERN.split(raw)
        return [p.strip() for p in parts if p and p.strip()]

    def _merge_unique(self, existing: List[str], incoming: List[str]) -> List[str]:
        """기존 순서를 유지하며 중복 없이 메뉴 병합"""
        merged: List[str] = []
        seen = set()
        for name in existing + incoming:
            normalized = name.strip()
            if not normalized or normalized in seen:
                continue
            merged.append(normalized)
            seen.add(normalized)
        return merged

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
        Welstory Plus API로 이번 주 식단 조회, Markdown 변환, 파일 저장

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
