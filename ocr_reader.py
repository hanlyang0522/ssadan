"""
OCR module for reading meal schedules from images
"""
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MealOCR:
    """Class for extracting meal information from images using OCR"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.meal_data = {}
    
    def read_meal_schedule(self) -> Dict[str, Dict[str, str]]:
        """
        Read meal schedule from image using OCR
        
        Returns:
            Dictionary with date as key and meal info as value
            Example: {
                '2026-01-15': {
                    'breakfast': '밥, 국, 반찬...',
                    'lunch': '밥, 국, 반찬...',
                    'dinner': '밥, 국, 반찬...'
                }
            }
        """
        try:
            # Open and process image
            image = Image.open(self.image_path)
            
            # Perform OCR with Korean language support
            # Using both Korean and English for better recognition
            text = pytesseract.image_to_string(image, lang='kor+eng')
            
            # Parse the extracted text
            self.meal_data = self._parse_meal_text(text)
            
            return self.meal_data
        
        except FileNotFoundError:
            print(f"Error: Image file not found at {self.image_path}")
            return {}
        except Exception as e:
            print(f"Error reading meal schedule: {str(e)}")
            return {}
    
    def _parse_meal_text(self, text: str) -> Dict[str, Dict[str, str]]:
        """
        Parse OCR text to extract meal information
        
        This is a simple parser that assumes a structured format.
        In production, you would need to adjust this based on 
        the actual format of your meal schedule images.
        """
        meal_data = {}
        
        # Split text into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Simple parsing logic - adjust based on actual image format
        # This example assumes format like:
        # 날짜: 2026-01-15
        # 조식: 밥, 국, 반찬
        # 중식: 밥, 국, 반찬
        # 석식: 밥, 국, 반찬
        
        current_date = None
        current_meals = {}
        
        for line in lines:
            # Check for date pattern
            date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})', line)
            if date_match:
                # Save previous date's meals if exists
                if current_date and current_meals:
                    meal_data[current_date] = current_meals.copy()
                
                current_date = date_match.group(1).replace('.', '-').replace('/', '-')
                current_meals = {}
                continue
            
            # Check for meal types (breakfast, lunch, dinner)
            if '조식' in line or '아침' in line or 'breakfast' in line.lower():
                meal_content = re.sub(r'^[^:：]*[:：]\s*', '', line)
                current_meals['breakfast'] = meal_content
            elif '중식' in line or '점심' in line or 'lunch' in line.lower():
                meal_content = re.sub(r'^[^:：]*[:：]\s*', '', line)
                current_meals['lunch'] = meal_content
            elif '석식' in line or '저녁' in line or 'dinner' in line.lower():
                meal_content = re.sub(r'^[^:：]*[:：]\s*', '', line)
                current_meals['dinner'] = meal_content
        
        # Save last date's meals
        if current_date and current_meals:
            meal_data[current_date] = current_meals
        
        return meal_data
    
    def get_weekly_meals(self) -> Dict[str, Dict[str, str]]:
        """Get meals for the entire week"""
        if not self.meal_data:
            self.read_meal_schedule()
        return self.meal_data
    
    def get_daily_meal(self, date: Optional[str] = None) -> Dict[str, str]:
        """
        Get meals for a specific date
        
        Args:
            date: Date string in YYYY-MM-DD format. If None, uses today's date.
        
        Returns:
            Dictionary with meal types as keys
        """
        if not self.meal_data:
            self.read_meal_schedule()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return self.meal_data.get(date, {})


def format_meal_info(meals: Dict[str, str], date: str) -> str:
    """
    Format meal information for display
    
    Args:
        meals: Dictionary with meal types and content
        date: Date string
    
    Returns:
        Formatted string for notification
    """
    if not meals:
        return f"📅 {date}\n식단 정보가 없습니다."
    
    message = f"📅 {date}\n\n"
    
    if 'breakfast' in meals:
        message += f"🌅 조식\n{meals['breakfast']}\n\n"
    
    if 'lunch' in meals:
        message += f"🌞 중식\n{meals['lunch']}\n\n"
    
    if 'dinner' in meals:
        message += f"🌙 석식\n{meals['dinner']}\n\n"
    
    return message.strip()


def format_weekly_meals(weekly_meals: Dict[str, Dict[str, str]]) -> str:
    """
    Format weekly meal information for display
    
    Args:
        weekly_meals: Dictionary with dates and meal information
    
    Returns:
        Formatted string for notification
    """
    if not weekly_meals:
        return "주간 식단 정보가 없습니다."
    
    message = "📋 주간 식단표\n" + "="*30 + "\n\n"
    
    # Sort by date
    sorted_dates = sorted(weekly_meals.keys())
    
    for date in sorted_dates:
        meals = weekly_meals[date]
        message += format_meal_info(meals, date) + "\n\n" + "-"*30 + "\n\n"
    
    return message.strip()
