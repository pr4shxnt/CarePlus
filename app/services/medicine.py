from .llm import llm_service
from ..database import models
from sqlalchemy.orm import Session
import json
import re
import os

MEDICINE_FILE = "data/medicines.txt"

class MedicineService:
    def parse_medicine_intent(self, text):
        prompt = f"""
        Extract medicine information from the following text: "{text}"
        Return a JSON object with:
        - action: "add", "query", or "none"
        - name: medicine name (if adding)
        - dosage: dosage (if adding)
        - frequency: frequency (if adding)
        - timing: timing (if adding)
        
        Rules:
        1. Only return "add" if the user explicitly mentions adding, taking, or starting a new medicine.
        2. If the user is asking about their mood, feelings, or history of emotions, return "none".
        3. Only return "query" if the user asks list, show, or check their medicines.

        Example: "Add Metformin 500mg twice a day after meals" 
        -> {{"action": "add", "name": "Metformin", "dosage": "500mg", "frequency": "twice a day", "timing": "after meals"}}
        
        Example: "how have i been feeling" 
        -> {{"action": "none"}}
        
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

    def add_medicine(self, data):
        line = f"Name: {data.get('name', 'N/A')}, Dosage: {data.get('dosage', 'N/A')}, Frequency: {data.get('frequency', 'N/A')}, Timing: {data.get('timing', 'N/A')}\n"
        with open(MEDICINE_FILE, "a") as f:
            f.write(line)
        return data

    def list_medicines(self):
        if not os.path.exists(MEDICINE_FILE):
            return []
        with open(MEDICINE_FILE, "r") as f:
            return f.readlines()

medicine_service = MedicineService()
