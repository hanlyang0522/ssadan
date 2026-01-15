"""
Mattermost Sender - Mattermost 웹훅으로 메시지 전송
"""
import requests
import os
from typing import Optional
from datetime import datetime


class MattermostSender:
    """Mattermost 웹훅으로 식단 정보를 전송하는 클래스"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Args:
            webhook_url: Mattermost incoming webhook URL
        """
        self.webhook_url = webhook_url or os.getenv('MATTERMOST_WEBHOOK_URL')
        
        if not self.webhook_url:
            raise ValueError("MATTERMOST_WEBHOOK_URL이 설정되지 않았습니다.")
    
    def send_message(self, text: str, username: str = "식단봇") -> bool:
        """
        Mattermost로 메시지 전송
        
        Args:
            text: 전송할 메시지 내용 (Markdown 형식 지원)
            username: 봇 이름
        
        Returns:
            성공 여부
        """
        try:
            payload = {
                "text": text,
                "username": username
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ Mattermost 메시지 전송 성공")
                return True
            else:
                print(f"✗ Mattermost 메시지 전송 실패: {response.status_code}")
                print(f"  응답: {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"✗ 네트워크 오류: {str(e)}")
            return False
    
    def send_weekly_menu(self, markdown_content: str) -> bool:
        """
        주간 식단표 전송
        
        Args:
            markdown_content: Markdown 형식의 주간 식단표
        
        Returns:
            성공 여부
        """
        message = f"📅 **주간 식단표**\n\n{markdown_content}"
        return self.send_message(message)
    
    def send_daily_menu(self, date: str, menu_content: str) -> bool:
        """
        일일 식단 전송
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            menu_content: 식단 내용
        
        Returns:
            성공 여부
        """
        dt = datetime.strptime(date, '%Y-%m-%d')
        weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
        
        message = f"🍽️ **오늘의 점심 메뉴** ({dt.strftime('%m월 %d일')} {weekday}요일)\n\n{menu_content}"
        return self.send_message(message)
    
    def load_and_send_daily(self, date: str, db_path: str = "db") -> bool:
        """
        저장된 파일에서 해당 날짜의 식단을 읽어서 전송
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            db_path: 저장된 파일 경로
        
        Returns:
            성공 여부
        """
        file_path = os.path.join(db_path, f"{date}.md")
        
        if not os.path.exists(file_path):
            print(f"✗ 파일을 찾을 수 없습니다: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.send_daily_menu(date, content)
        
        except Exception as e:
            print(f"✗ 파일 읽기 오류: {str(e)}")
            return False
