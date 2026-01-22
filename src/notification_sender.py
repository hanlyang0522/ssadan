"""Mattermost와 Discord 통합 알림 발송"""
import os
from typing import Optional
from datetime import datetime, timedelta, timezone

from mm_sender import MattermostSender
from discord_sender import DiscordSender


class NotificationSender:
    """Mattermost와 Discord에 동시에 알림 발송"""
    
    def __init__(self, 
                 mattermost_webhook_url: Optional[str] = None,
                 discord_webhook_url: Optional[str] = None,
                 skip_validation: bool = False):
        """
        Args:
            mattermost_webhook_url: Mattermost webhook URL
            discord_webhook_url: Discord webhook URL
            skip_validation: True이면 webhook URL 검증 생략 (dry_run용)
        """
        # Mattermost sender 초기화
        self.mattermost_sender = None
        mm_url = mattermost_webhook_url or os.getenv('MATTERMOST_WEBHOOK_URL')
        if mm_url:
            try:
                self.mattermost_sender = MattermostSender(webhook_url=mm_url, skip_validation=skip_validation)
            except ValueError:
                if not skip_validation:
                    print("⚠️  Mattermost webhook URL이 설정되지 않았습니다.")
        
        # Discord sender 초기화
        self.discord_sender = None
        discord_url = discord_webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        if discord_url:
            try:
                self.discord_sender = DiscordSender(webhook_url=discord_url, skip_validation=skip_validation)
            except ValueError:
                if not skip_validation:
                    print("⚠️  Discord webhook URL이 설정되지 않았습니다.")
        
        # 최소 하나의 sender는 필요
        if not skip_validation and not self.mattermost_sender and not self.discord_sender:
            raise ValueError("Mattermost 또는 Discord webhook URL 중 최소 하나는 설정되어야 합니다.")
    
    def send_message(self, text: str, username: str = "식단봇") -> bool:
        """
        Mattermost와 Discord에 메시지 전송
        
        Args:
            text: 전송할 메시지 내용
            username: 봇 이름
        
        Returns:
            성공 여부 (최소 하나라도 성공하면 True)
        """
        results = []
        
        # Mattermost로 전송
        if self.mattermost_sender:
            result = self.mattermost_sender.send_message(text, username)
            results.append(result)
        
        # Discord로 전송
        if self.discord_sender:
            result = self.discord_sender.send_message(text, username)
            results.append(result)
        
        # 최소 하나라도 성공하면 True
        return any(results) if results else False
    
    def send_weekly_menu(self, markdown_content: str) -> bool:
        """
        주간 식단표 전송
        
        Args:
            markdown_content: Markdown 형식의 주간 식단표
        
        Returns:
            성공 여부
        """
        results = []
        
        if self.mattermost_sender:
            result = self.mattermost_sender.send_weekly_menu(markdown_content)
            results.append(result)
        
        if self.discord_sender:
            result = self.discord_sender.send_weekly_menu(markdown_content)
            results.append(result)
        
        return any(results) if results else False
    
    def send_today_song_request(self) -> bool:
        """
        오늘의 노래 추천 요청 메시지 전송
        
        Returns:
            성공 여부
        """
        results = []
        
        if self.mattermost_sender:
            result = self.mattermost_sender.send_today_song_request()
            results.append(result)
        
        if self.discord_sender:
            result = self.discord_sender.send_today_song_request()
            results.append(result)
        
        return any(results) if results else False
    
    def send_daily_menu(self, date: str, menu_content: str) -> bool:
        """
        일일 식단 전송
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            menu_content: 식단 내용
        
        Returns:
            성공 여부
        """
        results = []
        
        if self.mattermost_sender:
            result = self.mattermost_sender.send_daily_menu(date, menu_content)
            results.append(result)
        
        if self.discord_sender:
            result = self.discord_sender.send_daily_menu(date, menu_content)
            results.append(result)
        
        return any(results) if results else False
    
    def find_weekly_file(self, date: str, db_path: str = "db") -> Optional[str]:
        """
        주어진 날짜가 포함된 주간 식단 파일 찾기
        (MattermostSender의 메서드를 재사용)
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            db_path: 저장된 파일 경로
        
        Returns:
            파일 경로 또는 None
        """
        if self.mattermost_sender:
            return self.mattermost_sender.find_weekly_file(date, db_path)
        return None
    
    def extract_daily_menu(self, markdown_content: str, target_date: str) -> Optional[str]:
        """
        주간 식단 마크다운에서 특정 날짜의 메뉴만 추출
        (MattermostSender의 메서드를 재사용)
        
        Args:
            markdown_content: 전체 주간 식단 마크다운
            target_date: 추출할 날짜 (YYYY-MM-DD)
        
        Returns:
            해당 날짜의 식단 문자열
        """
        if self.mattermost_sender:
            return self.mattermost_sender.extract_daily_menu(markdown_content, target_date)
        return None
    
    def load_and_send_daily(self, date: str, db_path: str = "db", dry_run: bool = False) -> bool:
        """
        저장된 주간 파일에서 해당 날짜의 식단만 추출하여 전송
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            db_path: 저장된 파일 경로
            dry_run: True이면 웹훅 전송 없이 결과만 출력
        
        Returns:
            성공 여부
        """
        # MattermostSender의 로직을 재사용하되, 전송은 통합 sender 사용
        if not self.mattermost_sender:
            # Mattermost sender가 없으면 임시로 생성 (파일 찾기/파싱용)
            temp_sender = MattermostSender(skip_validation=True)
            file_path = temp_sender.find_weekly_file(date, db_path)
        else:
            file_path = self.mattermost_sender.find_weekly_file(date, db_path)
        
        if not file_path:
            print(f"✗ 날짜 {date}에 해당하는 주간 식단 파일을 찾을 수 없습니다.")
            return False
        
        try:
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✓ 주간 파일 읽기 완료: {file_path}")
            
            # 해당 날짜의 메뉴만 추출
            if not self.mattermost_sender:
                temp_sender = MattermostSender(skip_validation=True)
                daily_menu = temp_sender.extract_daily_menu(content, date)
            else:
                daily_menu = self.mattermost_sender.extract_daily_menu(content, date)
            
            if not daily_menu:
                print(f"✗ 날짜 {date}의 메뉴를 추출할 수 없습니다.")
                return False
            
            print(f"✓ {date} 메뉴 추출 완료")
            
            # dry_run 모드면 출력만, 아니면 전송
            if dry_run:
                dt = datetime.strptime(date, '%Y-%m-%d')
                weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
                print("\n" + "=" * 60)
                print(f"📋 추출된 메뉴 (웹훅 전송 없이 확인만)")
                print("=" * 60)
                print(f"\n🍽️ **오늘의 점심 메뉴** ({dt.strftime('%m월 %d일')} {weekday}요일)\n")
                print(daily_menu)
                print("\n" + "=" * 60)
                print("💡 실제 전송을 원하시면 --dry-run 옵션 없이 실행하세요.")
                print("=" * 60)
                return True
            else:
                return self.send_daily_menu(date, daily_menu)
        
        except Exception as e:
            print(f"✗ 파일 읽기 또는 메뉴 추출 오류: {str(e)}")
            return False
