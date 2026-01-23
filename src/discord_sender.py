"""Discord 웹훅 메시지 전송"""
import requests
import os
import time
from typing import Optional
from datetime import datetime, timedelta, timezone


class DiscordSender:
    """Discord 웹훅 메시지 전송"""
    
    def __init__(self, webhook_url: Optional[str] = None, skip_validation: bool = False):
        """
        Args:
            webhook_url: Discord incoming webhook URL
            skip_validation: True이면 webhook URL 검증 생략 (dry_run용)
        """
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        
        if not skip_validation and not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
    
    def send_message(self, content: str, username: str = "식단봇", max_retries: int = 3) -> bool:
        """
        Discord로 메시지 전송 (재시도 로직 포함)
        
        Args:
            content: 전송할 메시지 내용 (Markdown 형식 지원)
            username: 봇 이름
            max_retries: 최대 재시도 횟수
        
        Returns:
            성공 여부
        """
        payload = {
            "content": content,
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
                
                if response.status_code == 204:  # Discord는 성공시 204 반환
                    print(f"✓ Discord 메시지 전송 성공")
                    return True
                else:
                    print(f"✗ Discord 메시지 전송 실패: {response.status_code}")
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
    
    def send_today_song_request(self) -> bool:
        """
        오늘의 노래 추천 요청 메시지 전송
        
        Returns:
            성공 여부
        """
        # 한국 시간대(KST, UTC+9) 사용
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][now.weekday()]
        date_str = now.strftime(f'%Y년 %m월 %d일 ({weekday_kr})')
        
        message = f"""### 🎵 오늘의 노래 추천        
**{date_str}**

안녕하세요! 오늘 하루를 함께할 노래를 추천해주세요~ 🎧✨
 🎼 음악과 함께하는 즐거운 하루 되세요!"""
        return self.send_message(message, username="노래봇")
    
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
