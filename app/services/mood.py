from .llm import llm_service
from ..database import models
from sqlalchemy.orm import Session
import re

class MoodService:
    def analyze_sentiment(self, text):
        prompt = f"""
        Analyze the sentiment of this message: "{text}"
        Labels: positive, neutral, negative, distressed.
        Only return the label (one word).
        """
        response = llm_service.generate_response(prompt).strip().lower()
        # Clean up response to match labels
        for label in ["positive", "neutral", "negative", "distressed"]:
            if label in response:
                return label
        return "neutral"

    def log_mood(self, db: Session, sentiment):
        mood_log = models.MoodLog(sentiment=sentiment)
        db.add(mood_log)
        db.commit()
        return mood_log

    def check_for_distress(self, db: Session):
        from datetime import datetime, timedelta
        today = datetime.now().date()
        distressed_count = db.query(models.MoodLog).filter(
            models.MoodLog.sentiment == "distressed",
            models.MoodLog.timestamp >= today
        ).count()
        
        if distressed_count >= 3:
            return "नमस्ते, मैले याद गरेँ कि तपाईं आज अलि चिन्तित हुनुहुन्छ। कृपया आफ्नो ख्याल राख्नुहोला र आवश्यक परेमा कसैसँग कुरा गर्नुहोस्। (I noticed you might be feeling distressed today. Please take care of yourself and talk to someone if needed.)"
        return None

    def get_mood_summary(self, db: Session):
        # Implementation for summarizing mood over time
        recent_moods = db.query(models.MoodLog).order_by(models.MoodLog.timestamp.desc()).limit(10).all()
        if not recent_moods:
            return "No mood data available yet."
        
        sentiments = [m.sentiment for m in recent_moods]
        summary_prompt = f"The user's recent sentiments are: {', '.join(sentiments)}. Summarize their emotional trend briefly."
        return llm_service.generate_response(summary_prompt)

mood_service = MoodService()
