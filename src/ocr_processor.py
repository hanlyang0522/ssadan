"""
OCR Processor - 이미지에서 식단을 추출하여 Markdown 테이블로 변환
"""
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os


class OCRProcessor:
    """이미지에서 식단을 추출하고 Markdown으로 변환하는 클래스"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.meal_data = {}
    
    def extract_meal_from_image(self) -> Dict[str, Dict[str, str]]:
        """
        이미지에서 식단 추출
        
        Returns:
            Dict[날짜, Dict[카테고리, 메뉴]] 형식의 딕셔너리
        """
        try:
            image = Image.open(self.image_path)
            text = pytesseract.image_to_string(image, lang='kor+eng')
            self.meal_data = self._parse_ocr_text(text)
            return self.meal_data
        except FileNotFoundError:
            print(f"Error: 이미지 파일을 찾을 수 없습니다 - {self.image_path}")
            return {}
        except Exception as e:
            print(f"Error: OCR 처리 중 오류 발생 - {str(e)}")
            return {}
    
    def _parse_ocr_text(self, text: str) -> Dict[str, Dict[str, str]]:
        """
        OCR 텍스트를 파싱하여 구조화된 데이터로 변환
        
        실제 식단표 형식에 맞게 파싱 로직을 구현해야 합니다.
        """
        meal_data = {}
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_date = None
        current_category = None
        
        for line in lines:
            # 날짜 패턴 인식
            date_match = re.search(r'(\d{1,2})[월/][\s]*(\d{1,2})[일]', line)
            if date_match:
                month = date_match.group(1).zfill(2)
                day = date_match.group(2).zfill(2)
                current_date = f"{datetime.now().year}-{month}-{day}"
                if current_date not in meal_data:
                    meal_data[current_date] = {}
                continue
            
            # 카테고리 인식 (20F 일반식, 10F 공존, 도시락 등)
            if any(keyword in line for keyword in ['20F', '10F', '도시락', '일반식', '공존', '브런치', '샐러드']):
                current_category = line
                if current_date and current_category not in meal_data[current_date]:
                    meal_data[current_date][current_category] = []
                continue
            
            # 메뉴 내용 추가
            if current_date and current_category:
                meal_data[current_date][current_category].append(line)
        
        return meal_data
    
    def convert_to_markdown(self, meal_data: Optional[Dict] = None) -> str:
        """
        식단 데이터를 Markdown 테이블 형식으로 변환
        
        Args:
            meal_data: 변환할 식단 데이터 (None이면 self.meal_data 사용)
        
        Returns:
            Markdown 형식의 문자열
        """
        if meal_data is None:
            meal_data = self.meal_data
        
        if not meal_data:
            return "식단 데이터가 없습니다."
        
        # 날짜 정렬
        dates = sorted(meal_data.keys())
        if not dates:
            return "식단 데이터가 없습니다."
        
        # 주차 정보 생성
        start_date = datetime.strptime(dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        week_info = f"{start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')}"
        
        # Markdown 테이블 생성
        markdown = f"## 🍴 SSAFY 주간메뉴표 ({week_info})\n\n"
        
        # 테이블 헤더
        header = "| 구분 |"
        separator = "| :--- |"
        
        for date in dates:
            dt = datetime.strptime(date, '%Y-%m-%d')
            weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
            header += f" {dt.strftime('%m월 %d일')} ({weekday}) |"
            separator += " :--- |"
        
        markdown += header + "\n" + separator + "\n"
        
        # 카테고리별 행 생성
        all_categories = set()
        for date in dates:
            all_categories.update(meal_data[date].keys())
        
        for category in sorted(all_categories):
            row = f"| **{category}** |"
            
            for date in dates:
                if category in meal_data[date]:
                    menus = meal_data[date][category]
                    menu_text = '<br>'.join(menus) if isinstance(menus, list) else menus
                else:
                    menu_text = "-"
                row += f" {menu_text} |"
            
            markdown += row + "\n"
        
        return markdown
    
    def save_to_file(self, markdown_content: str, date: str, db_path: str = "db") -> str:
        """
        Markdown 내용을 파일로 저장
        
        Args:
            markdown_content: 저장할 Markdown 내용
            date: 날짜 (YYYY-MM-DD 형식)
            db_path: 저장할 디렉토리 경로
        
        Returns:
            저장된 파일 경로
        """
        os.makedirs(db_path, exist_ok=True)
        file_path = os.path.join(db_path, f"{date}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Markdown 파일 저장 완료: {file_path}")
        return file_path
    
    def process_and_save(self, db_path: str = "db") -> Tuple[str, str]:
        """
        이미지 처리 및 저장 통합 메서드
        
        Returns:
            (markdown_content, file_path) 튜플
        """
        # 1. OCR 추출
        meal_data = self.extract_meal_from_image()
        
        if not meal_data:
            return "", ""
        
        # 2. Markdown 변환
        markdown = self.convert_to_markdown(meal_data)
        
        # 3. 파일 저장 (해당 주의 월요일 날짜 기준)
        today = datetime.now()
        # 월요일(0)을 기준으로 해당 주의 월요일 날짜 계산
        days_since_monday = today.weekday()  # 월요일=0, 화요일=1, ..., 일요일=6
        monday_date = today - timedelta(days=days_since_monday)
        monday_str = monday_date.strftime('%Y-%m-%d')
        
        file_path = self.save_to_file(markdown, monday_str, db_path)
        
        return markdown, file_path
