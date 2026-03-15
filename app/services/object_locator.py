from .llm import llm_service
from ..database import models
from sqlalchemy.orm import Session
import json
import re

class ObjectLocatorService:
    def parse_intent(self, text):
        prompt = f"""
        Extract object location information from: "{text}"
        Return JSON object with:
        - action: "save", "find", or "none"
        - object: object name
        - location: location description (for 'save')
        
        Example: "I put my keys on the table" -> {{"action": "save", "object": "keys", "location": "on the table"}}
        Example: "Where are my keys?" -> {{"action": "find", "object": "keys"}}
        
        Only return the JSON.
        """
        response = llm_service.generate_response(prompt)
        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group(0)
            return json.loads(json_str)
        except:
            return {"action": "none"}

    def save_location(self, db: Session, object_name, location):
        new_loc = models.ObjectLocation(object_name=object_name, location=location)
        db.add(new_loc)
        db.commit()
        return new_loc

    def find_location(self, db: Session, object_name):
        return db.query(models.ObjectLocation).filter(
            models.ObjectLocation.object_name.ilike(f"%{object_name}%")
        ).order_by(models.ObjectLocation.timestamp.desc()).first()

object_locator_service = ObjectLocatorService()
