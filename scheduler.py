"""
Scheduler for meal notifications
"""
import schedule
import time
from datetime import datetime
from typing import Callable
import os
from dotenv import load_dotenv

from ocr_reader import MealOCR, format_meal_info, format_weekly_meals
from webhook_notifier import WebhookNotifier, SlackWebhookNotifier, DiscordWebhookNotifier


class MealNotificationScheduler:
    """Scheduler for automated meal notifications"""
    
    def __init__(self):
        """Initialize the scheduler with configuration from environment"""
        load_dotenv()
        
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.meal_image_path = os.getenv('MEAL_IMAGE_PATH', './meal_schedule.jpg')
        self.daily_time = os.getenv('DAILY_NOTIFICATION_TIME', '08:00')
        self.weekly_day = int(os.getenv('WEEKLY_NOTIFICATION_DAY', '0'))  # 0 = Monday
        self.weekly_time = os.getenv('WEEKLY_NOTIFICATION_TIME', '09:00')
        
        # Determine webhook type based on URL
        self.notifier = self._create_notifier()
        self.ocr = MealOCR(self.meal_image_path)
    
    def _create_notifier(self) -> WebhookNotifier:
        """Create appropriate notifier based on webhook URL"""
        if not self.webhook_url:
            raise ValueError("WEBHOOK_URL not set in environment")
        
        if 'slack.com' in self.webhook_url:
            return SlackWebhookNotifier(self.webhook_url)
        elif 'discord.com' in self.webhook_url or 'discordapp.com' in self.webhook_url:
            return DiscordWebhookNotifier(self.webhook_url)
        else:
            return WebhookNotifier(self.webhook_url)
    
    def send_daily_notification(self):
        """Send daily meal notification"""
        print(f"[{datetime.now()}] Sending daily meal notification...")
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Read meal schedule
        daily_meal = self.ocr.get_daily_meal(today)
        
        if daily_meal:
            message = format_meal_info(daily_meal, today)
            success = self.notifier.send_daily_meal(message)
            
            if success:
                print(f"Daily notification sent successfully for {today}")
            else:
                print(f"Failed to send daily notification for {today}")
        else:
            print(f"No meal information found for {today}")
    
    def send_weekly_notification(self):
        """Send weekly meal schedule notification"""
        print(f"[{datetime.now()}] Sending weekly meal notification...")
        
        # Read full week's meal schedule
        weekly_meals = self.ocr.get_weekly_meals()
        
        if weekly_meals:
            message = format_weekly_meals(weekly_meals)
            success = self.notifier.send_weekly_meals(message)
            
            if success:
                print(f"Weekly notification sent successfully")
            else:
                print(f"Failed to send weekly notification")
        else:
            print("No meal information found for the week")
    
    def setup_schedule(self):
        """Set up the notification schedule"""
        # Schedule daily notification
        schedule.every().day.at(self.daily_time).do(self.send_daily_notification)
        print(f"Daily notification scheduled at {self.daily_time}")
        
        # Schedule weekly notification
        # Map day number to schedule day name
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_name = days[self.weekly_day % 7]
        
        schedule_func = getattr(schedule.every(), day_name)
        schedule_func.at(self.weekly_time).do(self.send_weekly_notification)
        print(f"Weekly notification scheduled on {day_name.capitalize()} at {self.weekly_time}")
    
    def run(self):
        """Run the scheduler continuously"""
        print("Meal notification scheduler started")
        print(f"Webhook URL: {self.webhook_url}")
        print(f"Image path: {self.meal_image_path}")
        print("-" * 50)
        
        self.setup_schedule()
        
        # Keep the script running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")


def run_scheduler():
    """Main function to run the scheduler"""
    try:
        scheduler = MealNotificationScheduler()
        scheduler.run()
    except Exception as e:
        print(f"Error running scheduler: {str(e)}")
        raise


if __name__ == "__main__":
    run_scheduler()
