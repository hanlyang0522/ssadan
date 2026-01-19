"""식단표 이미지 OCR 처리 및 Markdown 변환 (Google Document AI)"""
from google.cloud import documentai_v1 as documentai
import re
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import os


class OCRProcessor:
    """Google Document AI를 사용한 식단 이미지 OCR 처리"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.meal_data = {}
        
        # Google Cloud 인증 정보 확인
        self.credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
        if not self.credentials_json:
            raise ValueError("GOOGLE_CLOUD_CREDENTIALS 환경 변수가 설정되지 않았습니다.")
        
        # Document AI 설정
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')  # 기본값: us
        self.processor_id = os.getenv('GOOGLE_CLOUD_PROCESSOR_ID')
        
        if not self.project_id or not self.processor_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT_ID 및 GOOGLE_CLOUD_PROCESSOR_ID가 필요합니다.")
    
    def extract_meal_from_image(self) -> Dict[str, Dict[str, str]]:
        """
        Google Document AI로 이미지에서 테이블 추출
        
        Returns:
            Dict[날짜, Dict[카테고리, 메뉴]] 형식의 딕셔너리
        """
        try:
            # 인증 정보 설정
            credentials_dict = json.loads(self.credentials_json)
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            
            # Document AI 클라이언트 생성
            client = documentai.DocumentProcessorServiceClient(credentials=credentials)
            
            # 프로세서 이름 생성
            name = client.processor_path(self.project_id, self.location, self.processor_id)
            
            # 이미지 읽기
            with open(self.image_path, "rb") as image_file:
                image_content = image_file.read()
            
            # Document AI 요청
            raw_document = documentai.RawDocument(
                content=image_content,
                mime_type="image/jpeg"  # 또는 image/png
            )
            
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            
            print("📡 Google Document AI로 이미지 분석 중...")
            result = client.process_document(request=request)
            document = result.document
            
            # 테이블 추출 및 파싱
            self.meal_data = self._parse_document_tables(document)
            return self.meal_data
            
        except FileNotFoundError:
            print(f"✗ 이미지 파일을 찾을 수 없습니다: {self.image_path}")
            return {}
        except Exception as e:
            print(f"✗ Document AI 처리 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _parse_document_tables(self, document: documentai.Document) -> Dict[str, Dict[str, str]]:
        """
        Document AI의 테이블 결과를 파싱하여 구조화된 데이터로 변환
        
        Returns:
            Dict[날짜, Dict[카테고리, 메뉴]] 형식의 딕셔너리
        """
        meal_data = {}
        
        # 테이블 추출
        for page in document.pages:
            for table in page.tables:
                # 헤더 행에서 날짜 추출
                header_cells = table.header_rows[0].cells if table.header_rows else table.body_rows[0].cells
                dates = []
                
                for i, cell in enumerate(header_cells):
                    if i == 0:  # 첫 번째 셀은 "구분"
                        continue
                    
                    cell_text = self._get_table_cell_text(cell, document)
                    # 날짜 패턴 인식: "01월 12일 (월)"
                    date_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', cell_text)
                    if date_match:
                        month = date_match.group(1).zfill(2)
                        day = date_match.group(2).zfill(2)
                        date_str = f"{datetime.now().year}-{month}-{day}"
                        dates.append(date_str)
                        if date_str not in meal_data:
                            meal_data[date_str] = {}
                
                # 데이터 행 처리
                start_row = 1 if table.header_rows else 1
                for row in table.body_rows[start_row:]:
                    if len(row.cells) == 0:
                        continue
                    
                    # 첫 번째 셀은 카테고리
                    category = self._get_table_cell_text(row.cells[0], document).strip()
                    
                    if not category or category == "구분":
                        continue
                    
                    # 각 날짜별 메뉴 추출
                    for i, cell in enumerate(row.cells[1:]):
                        if i < len(dates):
                            menu = self._get_table_cell_text(cell, document).strip()
                            if menu:
                                date_str = dates[i]
                                meal_data[date_str][category] = menu
        
        print(f"✓ {len(meal_data)}개 날짜의 식단 추출 완료")
        return meal_data
    
    def _get_table_cell_text(self, cell, document: documentai.Document) -> str:
        """
        테이블 셀에서 텍스트 추출
        """
        text = ""
        # Layout을 사용하여 텍스트 추출
        if hasattr(cell, 'layout') and cell.layout:
            text = self._get_text_from_layout(cell.layout, document)
        return text.strip()
    
    def _get_text_from_layout(self, layout, document: documentai.Document) -> str:
        """
        Layout에서 텍스트 추출
        """
        text = ""
        if hasattr(layout, 'text_anchor') and layout.text_anchor:
            for segment in layout.text_anchor.text_segments:
                start_index = int(segment.start_index) if hasattr(segment, 'start_index') else 0
                end_index = int(segment.end_index) if hasattr(segment, 'end_index') else 0
                text += document.text[start_index:end_index]
        return text
    
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
