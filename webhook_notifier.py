"""
Webhook notification module for sending meal information
"""
import requests
from typing import Dict, Optional
import json


class WebhookNotifier:
    """Class for sending notifications via webhook"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize webhook notifier
        
        Args:
            webhook_url: The webhook URL to send notifications to
        """
        self.webhook_url = webhook_url
    
    def send_notification(self, message: str, title: Optional[str] = None) -> bool:
        """
        Send a notification via webhook
        
        Args:
            message: The message content to send
            title: Optional title for the notification
        
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Prepare payload - adjust format based on your webhook service
            # This is a generic format that works with many services
            payload = {
                "text": message
            }
            
            if title:
                payload["title"] = title
            
            # Send POST request to webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Check if request was successful
            if response.status_code in [200, 201, 204]:
                print(f"Notification sent successfully: {title if title else 'Message'}")
                return True
            else:
                print(f"Failed to send notification. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"Error sending webhook notification: {str(e)}")
            return False
    
    def send_daily_meal(self, meal_message: str) -> bool:
        """
        Send daily meal notification
        
        Args:
            meal_message: Formatted meal information for the day
        
        Returns:
            True if successful, False otherwise
        """
        title = "오늘의 식단 🍽️"
        return self.send_notification(meal_message, title)
    
    def send_weekly_meals(self, weekly_message: str) -> bool:
        """
        Send weekly meal schedule notification
        
        Args:
            weekly_message: Formatted weekly meal information
        
        Returns:
            True if successful, False otherwise
        """
        title = "주간 식단표 📅"
        return self.send_notification(weekly_message, title)


# For services like Slack, Discord, or Microsoft Teams, you might need custom formatters
class SlackWebhookNotifier(WebhookNotifier):
    """Slack-specific webhook notifier"""
    
    def send_notification(self, message: str, title: Optional[str] = None) -> bool:
        """Send notification in Slack format"""
        try:
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title if title else "알림"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200 and response.text == "ok":
                print(f"Slack notification sent successfully")
                return True
            else:
                print(f"Failed to send Slack notification: {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"Error sending Slack webhook: {str(e)}")
            return False


class DiscordWebhookNotifier(WebhookNotifier):
    """Discord-specific webhook notifier"""
    
    def send_notification(self, message: str, title: Optional[str] = None) -> bool:
        """Send notification in Discord format"""
        try:
            payload = {
                "embeds": [
                    {
                        "title": title if title else "알림",
                        "description": message,
                        "color": 5814783  # Blue color
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                print(f"Discord notification sent successfully")
                return True
            else:
                print(f"Failed to send Discord notification: {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord webhook: {str(e)}")
            return False
