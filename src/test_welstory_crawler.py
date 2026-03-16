"""welplan.pmh.codes API 크롤러 테스트 (mock 사용)"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from welstory_crawler import WelstoryCrawler


# welplan API 가 반환하는 형식의 샘플 응답 데이터
MOCK_RESTAURANT_RESPONSE = {
    "success": True,
    "restaurants": [
        {
            "id": "REST000595",
            "name": "멀티캠퍼스",
            "description": "멀티캠퍼스 20층 구내식당"
        }
    ],
    "count": 1
}

MOCK_MEAL_TIMES_RESPONSE = {
    "success": True,
    "mealTimes": [
        {"id": "1", "name": "조식"},
        {"id": "2", "name": "중식"},
        {"id": "3", "name": "석식"}
    ]
}

MOCK_MEALS_RESPONSE = {
    "success": True,
    "meals": [
        {
            "hallNo": "1",
            "date": 20260302,
            "mealTimeId": "2",
            "name": "부대찌개",
            "menuCourseName": "20F 일반식 (A. 한식)",
            "menuCourseType": "A",
            "setName": "부대찌개세트",
            "subMenuTxt": "현미밥, 배추김치, 계란말이",
            "photoUrl": ""
        },
        {
            "hallNo": "1",
            "date": 20260302,
            "mealTimeId": "2",
            "name": "카레라이스",
            "menuCourseName": "20F 일반식 (B. 일품)",
            "menuCourseType": "B",
            "setName": None,
            "subMenuTxt": None,
            "photoUrl": ""
        }
    ],
    "cached": False
}

MOCK_MEALS_RESPONSE_WITH_DUPLICATE_FIRST_ITEM = {
    "success": True,
    "meals": [
        {
            "hallNo": "1",
            "date": 20260302,
            "mealTimeId": "2",
            "name": "부대찌개",
            "menuCourseName": "20F 일반식 (A. 한식)",
            "menuCourseType": "A",
            "setName": "부대찌개세트",
            "subMenuTxt": "부대찌개, 현미밥, 배추김치, 계란말이",
            "photoUrl": ""
        }
    ],
    "cached": False
}


def make_mock_response(data, status_code=200):
    """requests.Response 모의 객체 생성"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    return mock_resp


class TestWelstoryCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = WelstoryCrawler()

    def test_init_default_restaurant_query(self):
        """기본 식당 검색어가 '멀티캠퍼스'인지 확인"""
        self.assertEqual(self.crawler.restaurant_query, "멀티캠퍼스")

    def test_init_custom_restaurant_query(self):
        """환경변수로 식당 검색어 변경 확인"""
        with patch.dict("os.environ", {"WELSTORY_RESTAURANT_QUERY": "삼성본관"}):
            crawler = WelstoryCrawler()
            self.assertEqual(crawler.restaurant_query, "삼성본관")

    @patch("welstory_crawler.requests.post")
    def test_search_restaurant_success(self, mock_post):
        """식당 검색 성공 시 첫 번째 식당 반환"""
        mock_post.return_value = make_mock_response(MOCK_RESTAURANT_RESPONSE)
        result = self.crawler._search_restaurant()
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "REST000595")
        self.assertEqual(result["name"], "멀티캠퍼스")

    @patch("welstory_crawler.requests.post")
    def test_search_restaurant_not_found(self, mock_post):
        """식당 검색 결과 없을 때 None 반환"""
        mock_post.return_value = make_mock_response({"success": True, "restaurants": [], "count": 0})
        result = self.crawler._search_restaurant()
        self.assertIsNone(result)

    @patch("welstory_crawler.requests.post")
    def test_search_restaurant_http_error(self, mock_post):
        """HTTP 오류 시 None 반환"""
        mock_post.return_value = make_mock_response({}, status_code=500)
        result = self.crawler._search_restaurant()
        self.assertIsNone(result)

    @patch("welstory_crawler.requests.post")
    def test_get_lunch_meal_time_id(self, mock_post):
        """'중식' 식사 시간 ID 조회"""
        mock_post.return_value = make_mock_response(MOCK_MEAL_TIMES_RESPONSE)
        result = self.crawler._get_lunch_meal_time_id(MOCK_RESTAURANT_RESPONSE["restaurants"][0])
        self.assertEqual(result, "2")

    @patch("welstory_crawler.requests.post")
    def test_get_lunch_meal_time_id_fallback(self, mock_post):
        """점심 키워드 없을 때 첫 번째 식사 시간 반환"""
        mock_post.return_value = make_mock_response({
            "success": True,
            "mealTimes": [{"id": "X", "name": "런치"}, {"id": "Y", "name": "디너"}]
        })
        result = self.crawler._get_lunch_meal_time_id(MOCK_RESTAURANT_RESPONSE["restaurants"][0])
        self.assertEqual(result, "X")

    @patch("welstory_crawler.requests.post")
    def test_fetch_daily_meal_list(self, mock_post):
        """일별 식단 목록 조회"""
        mock_post.return_value = make_mock_response(MOCK_MEALS_RESPONSE)
        date = datetime(2026, 3, 2)
        restaurant_data = MOCK_RESTAURANT_RESPONSE["restaurants"][0]
        result = self.crawler.fetch_daily_meal_list(date, restaurant_data, "2")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "부대찌개")
        self.assertEqual(result[0]["menuCourseName"], "20F 일반식 (A. 한식)")

    @patch("welstory_crawler.requests.post")
    def test_fetch_weekly_meal_data(self, mock_post):
        """주간 식단 데이터 조회 (월~금 5일)"""
        def side_effect(url, **kwargs):
            if "search" in url:
                return make_mock_response(MOCK_RESTAURANT_RESPONSE)
            elif "meal-times" in url:
                return make_mock_response(MOCK_MEAL_TIMES_RESPONSE)
            else:
                return make_mock_response(MOCK_MEALS_RESPONSE)

        mock_post.side_effect = side_effect

        kst = timezone(timedelta(hours=9))
        ref_date = datetime(2026, 3, 2, tzinfo=kst)  # 월요일
        result = self.crawler.fetch_weekly_meal_data(ref_date)

        self.assertEqual(len(result), 5)  # 월~금 5일
        # 첫 번째 날짜 확인
        self.assertIn("2026-03-02", result)
        # 코너명 및 메뉴 확인
        self.assertIn("20F 일반식 (A. 한식)", result["2026-03-02"])
        self.assertEqual(result["2026-03-02"]["20F 일반식 (A. 한식)"], "부대찌개, 현미밥, 배추김치, 계란말이")

    @patch("welstory_crawler.requests.post")
    def test_fetch_weekly_meal_data_remove_duplicate_first_item(self, mock_post):
        """menu name과 subMenuTxt 첫 항목이 같을 때 중복 제거"""

        def side_effect(url, **kwargs):
            if "search" in url:
                return make_mock_response(MOCK_RESTAURANT_RESPONSE)
            elif "meal-times" in url:
                return make_mock_response(MOCK_MEAL_TIMES_RESPONSE)
            else:
                return make_mock_response(MOCK_MEALS_RESPONSE_WITH_DUPLICATE_FIRST_ITEM)

        mock_post.side_effect = side_effect

        kst = timezone(timedelta(hours=9))
        ref_date = datetime(2026, 3, 2, tzinfo=kst)
        result = self.crawler.fetch_weekly_meal_data(ref_date)

        self.assertEqual(
            result["2026-03-02"]["20F 일반식 (A. 한식)"],
            "부대찌개, 현미밥, 배추김치, 계란말이"
        )

    @patch("welstory_crawler.requests.post")
    def test_fetch_weekly_meal_data_no_restaurant(self, mock_post):
        """식당을 찾지 못하면 빈 딕셔너리 반환"""
        mock_post.return_value = make_mock_response({"success": True, "restaurants": [], "count": 0})
        result = self.crawler.fetch_weekly_meal_data()
        self.assertEqual(result, {})

    def test_convert_to_markdown_format(self):
        """Markdown 변환 시 주간 제목 헤더 포함 확인"""
        meal_data = {
            "2026-03-02": {"20F 일반식 (A. 한식)": "부대찌개, 현미밥"},
            "2026-03-03": {"20F 일반식 (A. 한식)": "김치찌개"},
            "2026-03-04": {"20F 일반식 (A. 한식)": "된장찌개"},
            "2026-03-05": {"20F 일반식 (A. 한식)": "순두부찌개"},
            "2026-03-06": {"20F 일반식 (A. 한식)": "육개장"},
        }
        md = self.crawler.convert_to_markdown(meal_data)

        # 주간 제목 포함 여부
        self.assertIn("## 🍴 SSAFY 주간메뉴표", md)
        self.assertIn("03월 02일 ~ 03월 06일", md)
        # 헤더 행 포함 여부
        self.assertIn("| 구분 |", md)
        self.assertIn("03월 02일 (월)", md)
        self.assertIn("03월 06일 (금)", md)
        # 데이터 행 확인
        self.assertIn("**20F 일반식 (A. 한식)**", md)
        self.assertIn("부대찌개, 현미밥", md)

    def test_convert_to_markdown_empty(self):
        """빈 데이터 입력 시 안내 메시지 반환"""
        result = self.crawler.convert_to_markdown({})
        self.assertEqual(result, "식단 데이터가 없습니다.")

    def test_convert_to_markdown_weekday_names(self):
        """한글 요일명 정확성 확인"""
        meal_data = {
            "2026-03-02": {"코너": "메뉴1"},  # 월
            "2026-03-03": {"코너": "메뉴2"},  # 화
            "2026-03-04": {"코너": "메뉴3"},  # 수
            "2026-03-05": {"코너": "메뉴4"},  # 목
            "2026-03-06": {"코너": "메뉴5"},  # 금
        }
        md = self.crawler.convert_to_markdown(meal_data)
        self.assertIn("(월)", md)
        self.assertIn("(화)", md)
        self.assertIn("(수)", md)
        self.assertIn("(목)", md)
        self.assertIn("(금)", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
