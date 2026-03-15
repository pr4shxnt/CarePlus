import requests
import json

class LLMService:
    def __init__(self, model="llama3:8b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def generate_response(self, prompt, system_prompt=None):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def chat(self, messages, system_prompt=None):
        # Ollama /api/chat endpoint
        chat_url = self.base_url.replace("generate", "chat")
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if system_prompt:
            # Add system prompt as the first message if not already there
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": system_prompt})
        
        try:
            response = requests.post(chat_url, json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

llm_service = LLMService()
