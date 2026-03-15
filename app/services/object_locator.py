from .llm import llm_service
from ..database import models
from sqlalchemy.orm import Session
import json
import re
import os
import datetime

OBJECTS_FILE = "data/objects.txt"

class ObjectLocatorService:
    def parse_intent(self, text):
        prompt = f"""
        Extract object location information from: "{text}"
        Return JSON object with:
        - action: "save", "find", or "none"
        - object: object name
        - location: location description (for 'save')
        
        Rules:
        1. Only return "save" if the user is explicitly stating where they placed or kept an object (must include an object and a location).
        2. Only return "find" if the user is asking "Where" or "Have you seen" an item.
        3. If the user is asking about health, wounds, feelings, greetings (hello/hi), or small talk, ALWAYS return "none".

        Example: "I put my keys on the table" -> {{"action": "save", "object": "keys", "location": "on the table"}}
        Example: "Where are my keys?" -> {{"action": "find", "object": "keys"}}
        Example: "hello" -> {{"action": "none"}}
        Example: "how to treat a wound?" -> {{"action": "none"}}
        
        Only return the JSON.
        """
        response = llm_service.generate_response(prompt)
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if "action" in data:
                    return data
            return {"action": "none"}
        except:
            return {"action": "none"}

    def save_location(self, object_name, location):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} | {object_name} | {location}\n"
        with open(OBJECTS_FILE, "a") as f:
            f.write(line)

    def find_location(self, object_name):
        if not os.path.exists(OBJECTS_FILE):
            return None
        with open(OBJECTS_FILE, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if object_name.lower() in line.lower():
                    return line.strip()
        return None

object_locator_service = ObjectLocatorService()
