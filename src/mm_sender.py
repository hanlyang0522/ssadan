"""
Mattermost Sender - Mattermost 웹훅으로 메시지 전송
"""
import requests
import os
import time
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
    
    def send_message(self, text: str, username: str = "식단봇", max_retries: int = 3) -> bool:
        """
        Mattermost로 메시지 전송 (재시도 로직 포함)
        
        Args:
            text: 전송할 메시지 내용 (Markdown 형식 지원)
            username: 봇 이름
            max_retries: 최대 재시도 횟수
        
        Returns:
            성공 여부
        """
        payload = {
            "text": text,
            "username": username
        }
        
        for attempt in range(max_retries):
            try:
                # GitHub Actions 환경에서 안정적인 30초 타임아웃 사용
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"✓ Mattermost 메시지 전송 성공")
                    return True
                else:
                    print(f"✗ Mattermost 메시지 전송 실패: {response.status_code}")
                    print(f"  응답: {response.text}")
                    return False
            
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 지수 백오프: 1초(2^0), 2초(2^1), 4초(2^2)
                    print(f"⚠️  타임아웃 발생 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"   {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"✗ 네트워크 오류: {str(e)}")
                    print(f"   {max_retries}번 시도 후에도 실패했습니다.")
                    return False
            
            except requests.exceptions.RequestException as e:
                # 타임아웃 외의 오류(DNS 실패, SSL 오류 등)는 재시도하지 않음
                # 이러한 오류는 일시적이지 않고 재시도해도 해결되지 않는 경우가 많음
                print(f"✗ 네트워크 오류: {str(e)}")
                return False
        
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
