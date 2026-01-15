"""
Main Entry Point - 전체 프로세스 제어
"""
import argparse
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

from ocr_processor import OCRProcessor
from mm_sender import MattermostSender


def ocr_only(image_path: str, db_path: str = "db") -> bool:
    """
    이미지를 OCR 처리하고 Markdown 파일로 저장 (웹훅 전송 없음)
    
    Args:
        image_path: 식단표 이미지 경로
        db_path: Markdown 파일 저장 경로
    
    Returns:
        성공 여부
    """
    print("=" * 60)
    print("🔄 식단표 이미지 OCR 처리 시작")
    print("=" * 60)
    
    # OCR 처리 및 Markdown 변환
    print(f"\n1️⃣ 이미지 OCR 처리: {image_path}")
    processor = OCRProcessor(image_path)
    markdown, file_path = processor.process_and_save(db_path)
    
    if not markdown:
        print("✗ OCR 처리 실패")
        return False
    
    print(f"✓ OCR 처리 완료")
    print(f"✓ 파일 저장: {file_path}")
    print(f"\n💡 파일을 확인하고 필요시 수정한 후, 'notify' 명령으로 전송하세요.")
    
    return True


def notify_weekly(date: str = None, db_path: str = "db") -> bool:
    """
    저장된 Markdown 파일을 읽어서 주간 식단표 전송
    
    Args:
        date: 날짜 (YYYY-MM-DD), None이면 오늘
        db_path: Markdown 파일 저장 경로
    
    Returns:
        성공 여부
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 60)
    print(f"📤 주간 식단표 전송: {date}")
    print("=" * 60)
    
    file_path = os.path.join(db_path, f"{date}.md")
    
    if not os.path.exists(file_path):
        print(f"✗ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown = f.read()
        
        print(f"\n1️⃣ 파일 읽기 완료: {file_path}")
        
        # Mattermost로 주간 식단표 전송
        print(f"\n2️⃣ 주간 식단표 전송")
        sender = MattermostSender()
        success = sender.send_weekly_menu(markdown)
        
        if success:
            print("✓ 주간 식단표 전송 완료")
        else:
            print("✗ 주간 식단표 전송 실패")
        
        return success
    
    except ValueError as e:
        print(f"✗ 설정 오류: {str(e)}")
        return False
    except FileNotFoundError as e:
        print(f"✗ 파일을 찾을 수 없습니다: {str(e)}")
        return False
    except UnicodeDecodeError as e:
        print(f"✗ 파일 인코딩 오류: {str(e)}")
        return False
    except PermissionError as e:
        print(f"✗ 파일 접근 권한 오류: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ 파일 읽기 오류: {str(e)}")
        return False


def process_image(image_path: str, db_path: str = "db") -> bool:
    """
    이미지를 처리하고 주간 식단표를 전송
    
    Args:
        image_path: 식단표 이미지 경로
        db_path: Markdown 파일 저장 경로
    
    Returns:
        성공 여부
    """
    print("=" * 60)
    print("🔄 식단표 이미지 처리 시작")
    print("=" * 60)
    
    # 1. OCR 처리 및 Markdown 변환
    print(f"\n1️⃣ 이미지 OCR 처리: {image_path}")
    processor = OCRProcessor(image_path)
    markdown, file_path = processor.process_and_save(db_path)
    
    if not markdown:
        print("✗ OCR 처리 실패")
        return False
    
    print(f"✓ OCR 처리 완료")
    print(f"✓ 파일 저장: {file_path}")
    
    # 2. Mattermost로 주간 식단표 전송
    print(f"\n2️⃣ 주간 식단표 전송")
    try:
        sender = MattermostSender()
        success = sender.send_weekly_menu(markdown)
        
        if success:
            print("✓ 주간 식단표 전송 완료")
        else:
            print("✗ 주간 식단표 전송 실패")
        
        return success
    
    except ValueError as e:
        print(f"✗ 설정 오류: {str(e)}")
        return False


def send_daily_lunch(date: str = None, db_path: str = "db") -> bool:
    """
    해당 날짜의 점심 식단 전송
    
    Args:
        date: 날짜 (YYYY-MM-DD), None이면 오늘
        db_path: Markdown 파일 저장 경로
    
    Returns:
        성공 여부
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 60)
    print(f"🍽️ 일일 점심 식단 전송: {date}")
    print("=" * 60)
    
    try:
        sender = MattermostSender()
        success = sender.load_and_send_daily(date, db_path)
        
        if success:
            print("✓ 일일 식단 전송 완료")
        else:
            print("✗ 일일 식단 전송 실패")
        
        return success
    
    except ValueError as e:
        print(f"✗ 설정 오류: {str(e)}")
        return False


def main():
    """CLI 진입점"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='SSAFY 식단 알림 봇',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 이미지 처리 및 주간 식단표 전송 (통합)
  python main.py process --image meal.jpg
  
  # 이미지 OCR 처리만 수행 (웹훅 전송 없음)
  python main.py ocr --image meal.jpg
  
  # 저장된 파일로 주간 식단표 전송
  python main.py notify --date 2026-01-15
  
  # 오늘 점심 식단 전송
  python main.py daily
  
  # 특정 날짜 점심 식단 전송
  python main.py daily --date 2026-01-15
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')
    
    # process 명령
    process_parser = subparsers.add_parser('process', help='이미지 처리 및 주간 식단표 전송 (통합)')
    process_parser.add_argument('--image', required=True, help='식단표 이미지 파일 경로')
    process_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    
    # ocr 명령 (새로 추가)
    ocr_parser = subparsers.add_parser('ocr', help='이미지 OCR 처리만 수행 (웹훅 전송 없음)')
    ocr_parser.add_argument('--image', required=True, help='식단표 이미지 파일 경로')
    ocr_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    
    # notify 명령 (새로 추가)
    notify_parser = subparsers.add_parser('notify', help='저장된 파일로 주간 식단표 전송')
    notify_parser.add_argument('--date', help='날짜 (YYYY-MM-DD), 미지정 시 오늘')
    notify_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    
    # daily 명령
    daily_parser = subparsers.add_parser('daily', help='일일 점심 식단 전송')
    daily_parser.add_argument('--date', help='날짜 (YYYY-MM-DD), 미지정 시 오늘')
    daily_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'process':
            success = process_image(args.image, args.db)
            return 0 if success else 1
        
        elif args.command == 'ocr':
            success = ocr_only(args.image, args.db)
            return 0 if success else 1
        
        elif args.command == 'notify':
            success = notify_weekly(args.date, args.db)
            return 0 if success else 1
        
        elif args.command == 'daily':
            success = send_daily_lunch(args.date, args.db)
            return 0 if success else 1
    
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
