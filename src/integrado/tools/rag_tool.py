from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import glob
import math


class RagInput(BaseModel):
    query: str = Field(..., description="Query to retrieve relevant knowledge")
    top_k: int = Field(default=3, description="Number of top documents to return")


class RagRetrieverTool(BaseTool):
    name: str = "RAG Retriever Tool"
    description: str = (
        "Retrieve relevant pieces of knowledge from the local `knowledge/` folder. "
        "This is a simple, dependency-free retriever that scores chunks by token overlap."
    )
    args_schema: Type[BaseModel] = RagInput

    def __init__(self):
        super().__init__()
        self._docs = None

    def _load_documents(self):
        if self._docs is not None:
            return self._docs
        # Get absolute path to knowledge folder relative to this file
        module_dir = os.path.dirname(os.path.abspath(__file__))
        base = os.path.normpath(os.path.join(module_dir, '..', '..', '..', 'knowledge'))
        docs = []
        if os.path.exists(base):
            for path in glob.glob(os.path.join(base, '*')):
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            text = f.read()
                            # split into paragraphs/chunks
                            chunks = [c.strip() for c in text.split('\n\n') if c.strip()]
                            for i, chunk in enumerate(chunks):
                                docs.append({'source': os.path.basename(path), 'text': chunk})
                    except Exception:
                        continue
        self._docs = docs
        return docs

    def _score(self, query: str, doc_text: str) -> float:
        # Pure token-overlap score (no hardcoded boosts)
        if not query or not doc_text:
            return 0.0
        q_tokens = set(t.lower() for t in query.split())
        d_tokens = set(t.lower() for t in doc_text.split())
        if not q_tokens:
            return 0.0
        return float(len(q_tokens.intersection(d_tokens)))

    def _run(self, query: str, top_k: int = 3) -> str:
        docs = self._load_documents()
        if not docs:
            return None
        scored = []
        for d in docs:
            s = self._score(query, d['text'])
            scored.append((s, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [d for score, d in scored[:top_k] if score > 0]
        if not top:
            # fallback: return first N docs
            top = [d for _, d in scored[:top_k]]
        out = []
        for d in top:
            out.append("[Source: " + d['source'] + "]\n" + d['text'])
        return "\n\n".join(out)
