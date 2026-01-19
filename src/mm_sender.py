"""Mattermost 웹훅 메시지 전송"""
import requests
import os
import time
from typing import Optional
from datetime import datetime, timedelta


class MattermostSender:
    """Mattermost 웹훅 메시지 전송"""
    
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
    
    def find_weekly_file(self, date: str, db_path: str = "db") -> Optional[str]:
        """
        주어진 날짜가 포함된 주간 식단 파일 찾기
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            db_path: 저장된 파일 경로
        
        Returns:
            파일 경로 또는 None
        """
        # 해당 날짜의 주 월요일 날짜 계산
        dt = datetime.strptime(date, '%Y-%m-%d')
        days_since_monday = dt.weekday()  # 월요일=0
        monday_date = dt - timedelta(days=days_since_monday)
        monday_str = monday_date.strftime('%Y-%m-%d')
        
        # 월요일 날짜로 파일 찾기
        file_path = os.path.join(db_path, f"{monday_str}.md")
        
        if os.path.exists(file_path):
            return file_path
        
        # 혹시 다른 날짜로 저장되어 있을 수 있으니 해당 주의 모든 날짜 시도
        for day_offset in range(7):
            check_date = monday_date + timedelta(days=day_offset)
            check_file = os.path.join(db_path, f"{check_date.strftime('%Y-%m-%d')}.md")
            if os.path.exists(check_file):
                return check_file
        
        return None
    
    def extract_daily_menu(self, markdown_content: str, target_date: str) -> Optional[str]:
        """
        주간 식단 마크다운에서 특정 날짜의 메뉴만 추출
        
        Args:
            markdown_content: 전체 주간 식단 마크다운
            target_date: 추출할 날짜 (YYYY-MM-DD)
        
        Returns:
            해당 날짜의 식단 문자열 (Markdown 테이블 형식)
        """
        try:
            # 날짜를 "MM월 DD일 (요일)" 형식으로 변환
            dt = datetime.strptime(target_date, '%Y-%m-%d')
            target_month = dt.strftime('%m월').lstrip('0')  # 01월 -> 1월
            target_day = dt.strftime('%d일').lstrip('0')  # 05일 -> 5일
            weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
            
            # 가능한 날짜 패턴들 ("01월 15일", "1월 15일", "01월 15일 (목)" 등)
            date_patterns = [
                f"{dt.strftime('%m월')} {dt.strftime('%d일')}",  # 01월 15일
                f"{target_month} {target_day}",  # 1월 15일
                f"{dt.strftime('%m월')} {target_day}",  # 01월 15일
                f"{target_month} {dt.strftime('%d일')}",  # 1월 15일
            ]
            
            lines = markdown_content.split('\n')
            header_line = None
            column_index = -1
            
            # 헤더 라인에서 날짜 컬럼 찾기
            for i, line in enumerate(lines):
                if '| 구분 |' in line or '|:---:|' in line or '| :--- |' in line:
                    if '| 구분 |' in line:
                        header_line = i
                        columns = [col.strip() for col in line.split('|')]
                        
                        # 날짜 패턴에 맞는 컬럼 찾기
                        for idx, col in enumerate(columns):
                            for pattern in date_patterns:
                                if pattern in col and weekday in col:
                                    column_index = idx
                                    break
                            if column_index != -1:
                                break
                        break
            
            if column_index == -1:
                print(f"✗ 날짜 컬럼을 찾을 수 없습니다: {target_date}")
                return None
            
            # 테이블 데이터 추출
            result_lines = []
            result_lines.append(f"| 구분 | 메뉴 |")
            result_lines.append(f"| :--- | :--- |")
            
            # 헤더 다음 줄부터 데이터 추출
            in_table = False
            for i in range(header_line + 1, len(lines)):
                line = lines[i].strip()
                
                if not line or not line.startswith('|'):
                    if in_table:
                        break  # 테이블 끝
                    continue
                
                if '|:---:|' in line or '| :--- |' in line:
                    in_table = True
                    continue
                
                columns = [col.strip() for col in line.split('|')]
                
                if len(columns) > column_index and columns[1]:  # 카테고리가 있는 행
                    category = columns[1]  # 구분 (카테고리)
                    menu = columns[column_index] if len(columns) > column_index else "-"
                    
                    if menu and menu != "-":
                        result_lines.append(f"| {category} | {menu} |")
            
            if len(result_lines) <= 2:  # 헤더만 있는 경우
                return None
            
            return "\n".join(result_lines)
        
        except Exception as e:
            print(f"✗ 메뉴 추출 중 오류 발생: {str(e)}")
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
        # 1. 해당 날짜가 포함된 주간 파일 찾기
        file_path = self.find_weekly_file(date, db_path)
        
        if not file_path:
            print(f"✗ 날짜 {date}에 해당하는 주간 식단 파일을 찾을 수 없습니다.")
            return False
        
        try:
            # 2. 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✓ 주간 파일 읽기 완료: {file_path}")
            
            # 3. 해당 날짜의 메뉴만 추출
            daily_menu = self.extract_daily_menu(content, date)
            
            if not daily_menu:
                print(f"✗ 날짜 {date}의 메뉴를 추출할 수 없습니다.")
                return False
            
            print(f"✓ {date} 메뉴 추출 완료")
            
            # 4. dry_run 모드면 출력만, 아니면 전송
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
