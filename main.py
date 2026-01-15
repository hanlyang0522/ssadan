"""
Main application entry point
Provides CLI interface for the meal notification bot
"""
import argparse
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

from ocr_reader import MealOCR, format_meal_info, format_weekly_meals
from webhook_notifier import WebhookNotifier, SlackWebhookNotifier, DiscordWebhookNotifier
from scheduler import MealNotificationScheduler


def create_notifier(webhook_url: str) -> WebhookNotifier:
    """Create appropriate notifier based on webhook URL"""
    if 'slack.com' in webhook_url:
        return SlackWebhookNotifier(webhook_url)
    elif 'discord.com' in webhook_url or 'discordapp.com' in webhook_url:
        return DiscordWebhookNotifier(webhook_url)
    else:
        return WebhookNotifier(webhook_url)


def test_ocr(image_path: str):
    """Test OCR functionality"""
    print(f"Testing OCR with image: {image_path}")
    print("-" * 50)
    
    ocr = MealOCR(image_path)
    meals = ocr.read_meal_schedule()
    
    if meals:
        print("✓ OCR successful! Found meal data:")
        print(format_weekly_meals(meals))
    else:
        print("✗ No meal data found or OCR failed")
    
    return bool(meals)


def send_test_notification(webhook_url: str):
    """Send a test notification"""
    print(f"Sending test notification to: {webhook_url}")
    print("-" * 50)
    
    notifier = create_notifier(webhook_url)
    message = f"테스트 알림 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    success = notifier.send_notification(message, "테스트 알림 🔔")
    
    if success:
        print("✓ Test notification sent successfully")
    else:
        print("✗ Failed to send test notification")
    
    return success


def send_daily(image_path: str, webhook_url: str, date: str = None):
    """Send daily meal notification"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Sending daily notification for {date}")
    print("-" * 50)
    
    ocr = MealOCR(image_path)
    meal = ocr.get_daily_meal(date)
    
    if meal:
        message = format_meal_info(meal, date)
        notifier = create_notifier(webhook_url)
        success = notifier.send_daily_meal(message)
        
        if success:
            print("✓ Daily notification sent successfully")
        else:
            print("✗ Failed to send daily notification")
        
        return success
    else:
        print(f"✗ No meal data found for {date}")
        return False


def send_weekly(image_path: str, webhook_url: str):
    """Send weekly meal notification"""
    print("Sending weekly meal notification")
    print("-" * 50)
    
    ocr = MealOCR(image_path)
    meals = ocr.get_weekly_meals()
    
    if meals:
        message = format_weekly_meals(meals)
        notifier = create_notifier(webhook_url)
        success = notifier.send_weekly_meals(message)
        
        if success:
            print("✓ Weekly notification sent successfully")
        else:
            print("✗ Failed to send weekly notification")
        
        return success
    else:
        print("✗ No meal data found")
        return False


def main():
    """Main CLI interface"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='SSAFY 식단 알림 봇 - Meal notification bot with OCR and webhooks'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test OCR command
    test_parser = subparsers.add_parser('test-ocr', help='Test OCR functionality')
    test_parser.add_argument('--image', default=os.getenv('MEAL_IMAGE_PATH', './meal_schedule.jpg'),
                            help='Path to meal schedule image')
    
    # Test webhook command
    webhook_parser = subparsers.add_parser('test-webhook', help='Send test webhook notification')
    webhook_parser.add_argument('--url', default=os.getenv('WEBHOOK_URL'),
                               help='Webhook URL')
    
    # Send daily notification command
    daily_parser = subparsers.add_parser('send-daily', help='Send daily meal notification')
    daily_parser.add_argument('--image', default=os.getenv('MEAL_IMAGE_PATH', './meal_schedule.jpg'),
                             help='Path to meal schedule image')
    daily_parser.add_argument('--url', default=os.getenv('WEBHOOK_URL'),
                             help='Webhook URL')
    daily_parser.add_argument('--date', help='Date in YYYY-MM-DD format (default: today)')
    
    # Send weekly notification command
    weekly_parser = subparsers.add_parser('send-weekly', help='Send weekly meal notification')
    weekly_parser.add_argument('--image', default=os.getenv('MEAL_IMAGE_PATH', './meal_schedule.jpg'),
                              help='Path to meal schedule image')
    weekly_parser.add_argument('--url', default=os.getenv('WEBHOOK_URL'),
                              help='Webhook URL')
    
    # Run scheduler command
    scheduler_parser = subparsers.add_parser('run', help='Run the scheduler (continuous mode)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'test-ocr':
            success = test_ocr(args.image)
            return 0 if success else 1
        
        elif args.command == 'test-webhook':
            if not args.url:
                print("Error: Webhook URL not provided. Set WEBHOOK_URL in .env or use --url")
                return 1
            success = send_test_notification(args.url)
            return 0 if success else 1
        
        elif args.command == 'send-daily':
            if not args.url:
                print("Error: Webhook URL not provided. Set WEBHOOK_URL in .env or use --url")
                return 1
            success = send_daily(args.image, args.url, args.date)
            return 0 if success else 1
        
        elif args.command == 'send-weekly':
            if not args.url:
                print("Error: Webhook URL not provided. Set WEBHOOK_URL in .env or use --url")
                return 1
            success = send_weekly(args.image, args.url)
            return 0 if success else 1
        
        elif args.command == 'run':
            scheduler = MealNotificationScheduler()
            scheduler.run()
            return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
