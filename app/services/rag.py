import os
import re

class RAGService:
    def __init__(self, kb_dir="data/kb"):
        self.kb_dir = kb_dir
        self.chunks = []
        self._load_chunks()

    def _load_chunks(self):
        if not os.path.exists(self.kb_dir):
            return
            
        for filename in os.listdir(self.kb_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(self.kb_dir, filename), "r", encoding="utf-8") as f:
                    content = f.read()
                    # Simple chunking by paragraph or fixed length
                    # For now, split by double newlines or 500 characters
                    file_chunks = re.split(r'\n\s*\n', content)
                    for chunk in file_chunks:
                        if chunk.strip():
                            self.chunks.append({
                                "content": chunk.strip(),
                                "source": filename
                            })

    def retrieve(self, query, top_k=3):
        # Simple keyword matching as a fallback for BM25
        # In a real offline app, BM25 would be better
        # Let's do basic score based on keyword overlap
        keywords = re.findall(r'\w+', query.lower())
        scored_chunks = []
        
        for chunk in self.chunks:
            score = 0
            content_lower = chunk["content"].lower()
            for kw in keywords:
                if kw in content_lower:
                    score += 1
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k]]

rag_service = RAGService()
