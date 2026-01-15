"""
Simple tests for the meal notification bot
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import os

from ocr_reader import MealOCR, format_meal_info, format_weekly_meals
from webhook_notifier import WebhookNotifier, SlackWebhookNotifier, DiscordWebhookNotifier


class TestMealOCR(unittest.TestCase):
    """Test OCR and meal parsing functionality"""
    
    def test_parse_meal_text_basic(self):
        """Test basic meal text parsing"""
        ocr = MealOCR("dummy.jpg")
        
        text = """
        날짜: 2026-01-15
        조식: 밥, 국, 김치
        중식: 밥, 찌개, 반찬
        석식: 밥, 국, 김치
        """
        
        result = ocr._parse_meal_text(text)
        
        self.assertIn('2026-01-15', result)
        self.assertIn('breakfast', result['2026-01-15'])
        self.assertIn('lunch', result['2026-01-15'])
        self.assertIn('dinner', result['2026-01-15'])
    
    def test_parse_meal_text_multiple_dates(self):
        """Test parsing multiple dates"""
        ocr = MealOCR("dummy.jpg")
        
        text = """
        날짜: 2026-01-15
        조식: 밥, 국, 김치
        
        날짜: 2026-01-16
        중식: 밥, 찌개, 반찬
        """
        
        result = ocr._parse_meal_text(text)
        
        self.assertIn('2026-01-15', result)
        self.assertIn('2026-01-16', result)
    
    def test_parse_meal_text_date_formats(self):
        """Test different date formats"""
        ocr = MealOCR("dummy.jpg")
        
        # Test with dots
        text1 = "날짜: 2026.01.15\n조식: 밥"
        result1 = ocr._parse_meal_text(text1)
        self.assertIn('2026-01-15', result1)
        
        # Test with slashes
        text2 = "날짜: 2026/01/15\n중식: 밥"
        result2 = ocr._parse_meal_text(text2)
        self.assertIn('2026-01-15', result2)
    
    def test_format_meal_info(self):
        """Test meal info formatting"""
        meals = {
            'breakfast': '밥, 국, 김치',
            'lunch': '밥, 찌개, 반찬',
            'dinner': '밥, 국, 김치'
        }
        
        result = format_meal_info(meals, '2026-01-15')
        
        self.assertIn('2026-01-15', result)
        self.assertIn('조식', result)
        self.assertIn('중식', result)
        self.assertIn('석식', result)
    
    def test_format_meal_info_empty(self):
        """Test formatting with no meals"""
        result = format_meal_info({}, '2026-01-15')
        
        self.assertIn('2026-01-15', result)
        self.assertIn('식단 정보가 없습니다', result)
    
    def test_format_weekly_meals(self):
        """Test weekly meals formatting"""
        weekly = {
            '2026-01-15': {
                'breakfast': '밥, 국',
                'lunch': '밥, 찌개'
            },
            '2026-01-16': {
                'dinner': '밥, 국'
            }
        }
        
        result = format_weekly_meals(weekly)
        
        self.assertIn('주간 식단표', result)
        self.assertIn('2026-01-15', result)
        self.assertIn('2026-01-16', result)


class TestWebhookNotifier(unittest.TestCase):
    """Test webhook notification functionality"""
    
    @patch('webhook_notifier.requests.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = WebhookNotifier('http://example.com/webhook')
        result = notifier.send_notification('Test message')
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('webhook_notifier.requests.post')
    def test_send_notification_failure(self, mock_post):
        """Test failed notification sending"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Error'
        mock_post.return_value = mock_response
        
        notifier = WebhookNotifier('http://example.com/webhook')
        result = notifier.send_notification('Test message')
        
        self.assertFalse(result)
    
    @patch('webhook_notifier.requests.post')
    def test_send_daily_meal(self, mock_post):
        """Test daily meal notification"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = WebhookNotifier('http://example.com/webhook')
        result = notifier.send_daily_meal('오늘의 식단')
        
        self.assertTrue(result)
        # Verify title was included
        call_args = mock_post.call_args
        self.assertIn('title', call_args.kwargs['json'])
    
    @patch('webhook_notifier.requests.post')
    def test_send_weekly_meals(self, mock_post):
        """Test weekly meals notification"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = WebhookNotifier('http://example.com/webhook')
        result = notifier.send_weekly_meals('주간 식단')
        
        self.assertTrue(result)
    
    @patch('webhook_notifier.requests.post')
    def test_slack_notifier(self, mock_post):
        """Test Slack-specific notifier"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'ok'
        mock_post.return_value = mock_response
        
        notifier = SlackWebhookNotifier('https://hooks.slack.com/services/xxx')
        result = notifier.send_notification('Test', 'Title')
        
        self.assertTrue(result)
        # Verify Slack-specific format
        call_args = mock_post.call_args
        self.assertIn('blocks', call_args.kwargs['json'])
    
    @patch('webhook_notifier.requests.post')
    def test_discord_notifier(self, mock_post):
        """Test Discord-specific notifier"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        notifier = DiscordWebhookNotifier('https://discord.com/api/webhooks/xxx')
        result = notifier.send_notification('Test', 'Title')
        
        self.assertTrue(result)
        # Verify Discord-specific format
        call_args = mock_post.call_args
        self.assertIn('embeds', call_args.kwargs['json'])


if __name__ == '__main__':
    unittest.main()
