"""RAG-bot with query logging for the gapped knowledge base.

Logs every request to logs.jsonl with:
  query, timestamp, found_chunks, answer_length, success, sources, answer
"""

import json
import os
from datetime import datetime
from pathlib import Path

import requests
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
LOG_FILE = BASE_DIR / "logs.jsonl"
COLLECTION_NAME = "stellar_chronicles_gapped"
EMBED_MODEL = "BAAI/bge-m3"
TOP_K = 3

LLM_BASE_URL = "https://api.aitunnel.ru/v1"
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 600

REFUSAL = "я не знаю"

SYSTEM_PROMPT = """Ты — ассистент по базе знаний вымышленной вселенной Stellar Chronicles.
Отвечай ТОЛЬКО на основе фрагментов контекста ниже.
Если в контексте нет ответа — напиши ровно: "Я не знаю". Не выдумывай факты.
Сначала размышляй по шагам, потом дай финальный ответ.

Формат:

Шаги:
- <шаг>

Ответ:
<финальный ответ>"""

# few-shot examples use only entities PRESENT in the gapped base
FEW_SHOT = [
    {
        "q": "Что такое Void Core и чем он опасен?",
        "a": ("Шаги:\n- Ищу Void Core в контексте.\n"
              "- В документе Death_Star сказано: это станция-супероружие, уничтожающая планеты.\n"
              "\nОтвет:\nVoid Core — боевая станция Stellar Dominion, способная уничтожать планеты."),
    },
    {
        "q": "Чем питается HyperRelay?",
        "a": ("Шаги:\n- Ищу HyperRelay в контексте.\n"
              "- В документе HyperRelay сказано: сеть питается энергоячейкой Void Core.\n"
              "\nОтвет:\nHyperRelay питается энергоячейкой Void Core."),
    },
]


class Retriever:
    def __init__(self):
        self.model = SentenceTransformer(EMBED_MODEL)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_collection(COLLECTION_NAME)

    def search(self, query, k=TOP_K):
        vector = self.model.encode(query, normalize_embeddings=True).tolist()
        result = self.collection.query(query_embeddings=[vector], n_results=k,
                                       include=["documents", "metadatas", "distances"])
        return [{
            "text": doc, "source": meta["source"], "title": meta["title"],
            "chunk": meta["chunk_index"], "score": round(1 - dist, 4),
        } for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0],
                                     result["distances"][0])]


def is_refusal(answer):
    return REFUSAL in answer.lower()


class RAGBot:
    def __init__(self, api_key=None, retriever=None, log_file=None):
        self.retriever = retriever or Retriever()
        self.api_key = api_key or os.environ.get("AITUNNEL_API_KEY")
        self.log_file = Path(log_file) if log_file else LOG_FILE
        if not self.api_key:
            raise RuntimeError("Не задан AITUNNEL_API_KEY")

    def _call_llm(self, messages):
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={"model": LLM_MODEL, "messages": messages,
                  "temperature": LLM_TEMPERATURE, "max_tokens": LLM_MAX_TOKENS},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def answer(self, query, log=True):
        hits = self.retriever.search(query)
        context = "\n\n".join(f"[Фрагмент {i} | источник: {h['source']}]\n{h['text']}"
                              for i, h in enumerate(hits, 1))
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for ex in FEW_SHOT:
            messages.append({"role": "user", "content": ex["q"]})
            messages.append({"role": "assistant", "content": ex["a"]})
        messages.append({"role": "user",
                         "content": f"Контекст:\n{context}\n\nВопрос: {query}"})

        answer = self._call_llm(messages)

        refusal = is_refusal(answer)
        if not hits:
            status = "no_context"
        elif refusal:
            status = "refused"
        elif len(answer) >= 40:
            status = "ok"
        else:
            status = "short_answer"

        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": query,                 # запрос
            "result": answer,               # результат (ответ бота)
            "sources": [h["source"] for h in hits],   # источники
            "length": len(answer),          # длина ответа
            "status": status,               # статус: ok | refused | no_context | short_answer
            "found_chunks": len(hits) > 0,
            "n_chunks": len(hits),
            "refusal": refusal,
            "top_scores": [h["score"] for h in hits],
        }
        if log:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"answer": answer, "sources": hits, "record": record}