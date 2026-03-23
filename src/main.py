"""SSAFY 식단 알림 봇 - CLI 진입점"""
import argparse
import sys
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from mm_sender import MattermostSender
from notification_sender import NotificationSender
from welstory_crawler import WelstoryCrawler


# 요일 이름 상수
WEEKDAY_NAMES_KR = ['월', '화', '수', '목', '금', '토', '일']


def crawl_weekly(db_path: str = "db") -> bool:
    """
    welplan.pmh.codes API에서 이번 주 식단 데이터를 가져와 Markdown 파일로 저장

    Args:
        db_path: Markdown 파일 저장 경로

    Returns:
        성공 여부
    """
    print("=" * 60)
    print("🔄 welplan.pmh.codes API 식단 크롤링 시작")
    print("=" * 60)

    crawler = WelstoryCrawler()

    print("\n1️⃣  주간 식단 조회 중...")
    markdown, file_path = crawler.process_and_save(db_path)

    if not markdown:
        print("✗ 식단 크롤링 실패")
        return False

    print(f"✓ 식단 크롤링 완료")
    print(f"✓ 파일 저장: {file_path}")
    return True


def send_today_song() -> bool:
    """
    오늘의 노래 추천 요청 메시지 전송
    
    Returns:
        성공 여부
    """
    print("=" * 60)
    print("🎵 오늘의 노래 추천 요청")
    print("=" * 60)
    
    webhook_url = os.getenv('MATTERMOST_TODAY_SONG_URL')
    if not webhook_url:
        print("✗ 오류: MATTERMOST_TODAY_SONG_URL 환경변수가 설정되지 않았습니다.")
        return False
    
    print("\n📤 메시지 전송 중...")
    sender = MattermostSender(webhook_url=webhook_url)
    success = sender.send_today_song_request()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 오늘의 노래 추천 요청 완료")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 오늘의 노래 추천 요청 실패")
        print("=" * 60)
    
    return success


def send_daily_lunch(date: str = None, db_path: str = "db", dry_run: bool = False) -> bool:
    """
    해당 날짜의 점심 식단 전송
    
    Args:
        date: 날짜 (YYYY-MM-DD), None이면 오늘
        db_path: Markdown 파일 저장 경로
        dry_run: True이면 웹훅 전송 없이 결과만 출력
    
    Returns:
        성공 여부
    """
    kst = timezone(timedelta(hours=9))
    
    if date is None:
        now_kst = datetime.now(kst)
        date = now_kst.strftime('%Y-%m-%d')
    else:
        now_kst = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=kst)
    
    # 주말 체크 (월~금만 식단 전송)
    if now_kst.weekday() >= 5:
        print("=" * 60)
        print(f"ℹ️  주말에는 점심 식단을 전송하지 않습니다: {date} ({WEEKDAY_NAMES_KR[now_kst.weekday()]}요일)")
        print("=" * 60)
        return True
    
    print("=" * 60)
    if dry_run:
        print(f"🔍 일일 점심 식단 확인 (테스트 모드): {date}")
    else:
        print(f"🍽️ 일일 점심 식단 전송: {date}")
    print("=" * 60)
    
    try:
        sender = NotificationSender(skip_validation=dry_run)
        success = sender.load_and_send_daily(date, db_path, dry_run)
        
        if not dry_run:
            if success:
                print("✓ 일일 식단 전송 완료")
            else:
                print("✗ 일일 식단 전송 실패")
        
        return success
    
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI 진입점"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='SSAFY 식단 알림 봇',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 웰스토리 API로 이번 주 식단 크롤링
  python main.py crawl

  # 오늘 점심 식단 전송
  python main.py daily

  # 특정 날짜 점심 식단 전송
  python main.py daily --date 2026-01-15

  # 오늘의 노래 추천 요청
  python main.py song
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')
    
    # crawl 명령
    crawl_parser = subparsers.add_parser('crawl', help='웰스토리 API로 이번 주 식단 크롤링')
    crawl_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    
    # daily 명령
    daily_parser = subparsers.add_parser('daily', help='일일 점심 식단 전송')
    daily_parser.add_argument('--date', help='날짜 (YYYY-MM-DD), 미지정 시 오늘')
    daily_parser.add_argument('--db', default='db', help='Markdown 파일 저장 경로 (기본값: db)')
    daily_parser.add_argument('--dry-run', action='store_true', help='웹훅 전송 없이 결과만 확인')
    
    # song 명령
    song_parser = subparsers.add_parser('song', help='오늘의 노래 추천 요청')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'crawl':
            success = crawl_weekly(args.db)
            return 0 if success else 1
        
        elif args.command == 'daily':
            dry_run = getattr(args, 'dry_run', False)
            success = send_daily_lunch(args.date, args.db, dry_run)
            return 0 if success else 1
        
        elif args.command == 'song':
            success = send_today_song()
            return 0 if success else 1
    
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
