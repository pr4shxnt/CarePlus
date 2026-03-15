from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import db, models
from .services.llm import llm_service
from .services.rag import rag_service
from .services.medicine import medicine_service
from .services.object_locator import object_locator_service
from .services.mood import mood_service
import os

# Create tables
models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(title="Swastha Sathi (Health Companion)")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/chat")
async def chat_endpoint(request: Request, db: Session = Depends(db.get_db)):
    data = await request.json()
    user_message = data.get("message")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    # 1. Passive Sentiment Analysis (Mood Tracking) - Database
    sentiment = mood_service.analyze_sentiment(user_message)
    mood_service.log_mood(db, sentiment)

    # 2. Save user message history
    db_message = models.Message(role="user", content=user_message, sentiment=sentiment)
    db.add(db_message)
    db.commit()

    # 3. Intent Routing
    response_content = ""
    
    # Check for Mood Summary Intent first to fix bug
    if any(kw in user_message.lower() for kw in ["mood", "how have i been", "emotional", "feeling"]):
        response_content = mood_service.get_mood_summary(db)

    # Medicine Intent (.txt storage)
    if not response_content:
        med_intent = medicine_service.parse_medicine_intent(user_message)
        if med_intent["action"] == "add":
            medicine_service.add_medicine(med_intent)
            response_content = f"I've added {med_intent.get('name')} to your reminders (saved in file)."
        elif med_intent["action"] == "query":
            meds = medicine_service.list_medicines()
            if meds:
                med_list = "".join(meds)
                response_content = f"Here are your medicine records:\n{med_list}"
            else:
                response_content = "I couldn't find any medicine records in your file."

    # Object Locator Intent (.txt storage)
    if not response_content:
        obj_intent = object_locator_service.parse_intent(user_message)
        if obj_intent["action"] == "save":
            object_locator_service.save_location(obj_intent["object"], obj_intent["location"])
            response_content = f"Noted. I've saved that your {obj_intent['object']} is {obj_intent['location']}."
        elif obj_intent["action"] == "find":
            loc_entry = object_locator_service.find_location(obj_intent["object"])
            if loc_entry:
                response_content = f"I found this in my records: {loc_entry}"
            else:
                response_content = f"I don't have a record of your {obj_intent['object']}."

    # 4. Fallback to Health Q&A (RAG)
    if not response_content:
        relevant_chunks = rag_service.retrieve(user_message)
        context = "\n\n".join([c["content"] for c in relevant_chunks])
        
        system_prompt = "You are Swastha Sathi, a health companion. Answer health questions grounded in the provided context. Use English ONLY. Always include a disclaimer that you are not a doctor."
        
        if context:
            prompt = f"Context from health knowledge base:\n{context}\n\nUser Question: {user_message}\n\nAnswer based ONLY on the context. If not found, say you don't know based on available records. Add a medical disclaimer."
        else:
            prompt = user_message

        history = db.query(models.Message).order_by(models.Message.id.desc()).limit(6).all()
        history = history[::-1]
        chat_messages = [{"role": m.role, "content": m.content} for m in history]
        if context:
            chat_messages[-1]["content"] = prompt
            
        response_content = llm_service.chat(chat_messages, system_prompt=system_prompt)

    # 5. Check for Distress Nudge (English)
    nudge = mood_service.check_for_distress(db)
    if nudge:
        response_content += f"\n\n---\n{nudge}"

    # Save assistant response
    db_assistant_message = models.Message(role="assistant", content=response_content)
    db.add(db_assistant_message)
    db.commit()

    return {"response": response_content, "sentiment": sentiment}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
