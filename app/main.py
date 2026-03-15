from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import db, models
from .services.llm import llm_service
from .services.rag import rag_service
import os

# Create tables
models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(title="Swastha Sathi (स्वस्थ साथी)")

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

    # Save user message
    db_message = models.Message(role="user", content=user_message)
    db.add(db_message)
    db.commit()

    # RAG Retrieval
    relevant_chunks = rag_service.retrieve(user_message)
    context = "\n\n".join([c["content"] for c in relevant_chunks])
    
    if context:
        prompt = f"Context from health knowledge base:\n{context}\n\nUser Question: {user_message}\n\nAnswer the question based ONLY on the context provided above. If the context doesn't contain the answer, say you don't know based on available records. Always include a medical disclaimer."
    else:
        prompt = user_message

    # Get last 5 messages for context
    history = db.query(models.Message).order_by(models.Message.id.desc()).limit(6).all()
    history = history[::-1] # Reverse to get chronological order
    
    chat_messages = [{"role": m.role, "content": m.content} for m in history]
    # Replace the last user message with the RAG-augmented prompt if context exists
    if context:
        chat_messages[-1]["content"] = prompt
    
    system_prompt = "You are Swastha Sathi, a health companion for Nepal. Use Nepali or English as requested. Always include a disclaimer that you are not a doctor and this is for information only."
    
    response_content = llm_service.chat(chat_messages, system_prompt=system_prompt)
    
    # Save assistant response
    db_assistant_message = models.Message(role="assistant", content=response_content)
    db.add(db_assistant_message)
    db.commit()

    return {"response": response_content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
