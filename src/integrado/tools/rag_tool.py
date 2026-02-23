import logging
from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import os
import glob

logger = logging.getLogger(__name__)

class RagInput(BaseModel):
    query: str = Field(..., description="Query to retrieve relevant knowledge")
    top_k: int = Field(default=3, description="Number of top documents to return")

class RagRetrieverTool(BaseTool):
    name: str = "RAG Retriever Tool"
    description: str = (
        "Retrieve relevant pieces of knowledge from the local `knowledge/` folder. "
        "Useful for getting prices, treatments, schedules, and clinic information."
    )
    args_schema: Type[BaseModel] = RagInput
    _docs: List[Dict] = []  # Almacenamiento en memoria de los documentos

    def __init__(self):
        super().__init__()
        # OPTIMIZACIÓN PASO 3: Carga Eager (Inmediata)
        # Cargamos los documentos UNA sola vez al iniciar la herramienta.
        self._load_documents()

    def _load_documents(self):
        """Carga los documentos desde el disco a la memoria."""
        # Evitar recargar si ya existen (aunque con __init__ se garantiza una vez por instancia)
        if self._docs:
            return

        module_dir = os.path.dirname(os.path.abspath(__file__))
        base = os.path.normpath(os.path.join(module_dir, '..', '..', '..', 'knowledge'))
        
        docs = []
        if os.path.exists(base):
            for path in glob.glob(os.path.join(base, '*')):
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            text = f.read()
                            # Dividir en párrafos/chunks por doble salto de línea
                            chunks = [c.strip() for c in text.split('\n\n') if c.strip()]
                            for chunk in chunks:
                                docs.append({'source': os.path.basename(path), 'text': chunk})
                    except Exception as e:
                        logger.warning(f"Error loading {path}: {e}")
                        continue
        
        self._docs = docs
        logger.info(f"RAG Knowledge loaded: {len(self._docs)} chunks available.")

    def _score(self, query: str, doc_text: str) -> float:
        # Sistema simple de puntuación por superposición de tokens
        if not query or not doc_text:
            return 0.0
        q_tokens = set(t.lower() for t in query.split())
        d_tokens = set(t.lower() for t in doc_text.split())
        
        if not q_tokens:
            return 0.0
            
        # Puntuación básica: intersección de palabras
        return float(len(q_tokens.intersection(d_tokens)))

    def _run(self, query: str, top_k: int = 3) -> str:
        # Usamos los documentos ya cargados en memoria (self._docs)
        if not self._docs:
            return "No knowledge base available."

        scored = []
        for d in self._docs:
            s = self._score(query, d['text'])
            scored.append((s, d))
        
        # Ordenar por relevancia (score más alto primero)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Filtrar solo los que tengan alguna coincidencia (score > 0)
        top = [d for score, d in scored[:top_k] if score > 0]
        
        # Fallback: Si no hay coincidencia exacta, devolver los primeros N (contexto general)
        # o devolver un mensaje de que no se encontró info específica.
        if not top:
            # Opción A: Devolver contexto general (útil para saludos)
            top = [d for _, d in scored[:1]] 
            # Opción B: Devolver vacío para obligar al agente a preguntar más
            # return "" 
            
        out = []
        for d in top:
            out.append(f"[Source: {d['source']}]\n{d['text']}")
            
        return "\n\n".join(out)