from .llm import llm_service
from ..database import models
from sqlalchemy.orm import Session
import json
import re

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
        
        If the user is asking about their medicines, action should be "query".
        Example: "Add Metformin 500mg twice a day after meals" 
        -> {{"action": "add", "name": "Metformin", "dosage": "500mg", "frequency": "twice a day", "timing": "after meals"}}
        
        Example: "What medicines should I take?" 
        -> {{"action": "query"}}
        
        Only return the JSON.
        """
        response = llm_service.generate_response(prompt)
        try:
            # Simple clean up of response to get JSON
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group(0)
            return json.loads(json_str)
        except:
            return {"action": "none"}

    def add_medicine(self, db: Session, data):
        new_med = models.Medicine(
            name=data.get("name"),
            dosage=data.get("dosage"),
            frequency=data.get("frequency"),
            timing=data.get("timing")
        )
        db.add(new_med)
        db.commit()
        db.refresh(new_med)
        return new_med

    def list_medicines(self, db: Session):
        return db.query(models.Medicine).filter(models.Medicine.is_active == 1).all()

medicine_service = MedicineService()
