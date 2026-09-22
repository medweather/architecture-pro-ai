"""RAG-bot for the Stellar Chronicles knowledge base.

Pipeline:
    query -> embedding (BAAI/bge-m3) -> search (ChromaDB)
          -> prompt (few-shot + Chain-of-Thought) -> LLM (gpt-4o-mini) -> answer

Run:
    python3 rag_bot.py                 # REPL
    python3 rag_bot.py "Кто такой Zarn Velkor?"
"""

import os
import sys
from pathlib import Path

import requests
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR.parent / "Task3" / "chroma_db"
COLLECTION_NAME = "stellar_chronicles"
EMBED_MODEL = "BAAI/bge-m3"
TOP_K = 3

LLM_BASE_URL = "https://api.aitunnel.ru/v1"
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 700

SYSTEM_PROMPT = """Ты — ассистент по корпоративной базе знаний вымышленной вселенной Stellar Chronicles.

Правила:
1. Отвечай ТОЛЬКО на основе фрагментов контекста, приведённых ниже.
2. Если в контексте нет ответа — напиши ровно: "Я не знаю". Не выдумывай факты.
3. Сначала размышляй по шагам, потом дай финальный ответ.
4. Отвечай на языке пользователя, кратко и по делу.

Формат ответа строго такой:

Шаги:
- <шаг 1>
- <шаг 2>
- <шаг 3>

Ответ:
<финальный ответ>"""

# Few-shot примеры собраны из реальных документов базы знаний (Darth_Vader.md, Death_Star.md)
FEW_SHOT = [
    {
        "q": "Кто такой Zarn Velkor?",
        "a": (
            "Шаги:\n"
            "- Ищу в контексте упоминание Zarn Velkor.\n"
            "- В документе Darth_Vader сказано: Zarn Velkor — лидер Stellar Dominion, "
            "бывший Aether Warden Kaelor Venn.\n"
            "- Он перешёл на теневой путь Synth Flux после дуэли с Torin Mellis.\n"
            "\nОтвет:\n"
            "Zarn Velkor — лидер Stellar Dominion. Ранее он был Aether Warden по имени "
            "Kaelor Venn, но перешёл на теневой путь Synth Flux и стал Void Master."
        ),
    },
    {
        "q": "Что такое Void Core и чем он опасен?",
        "a": (
            "Шаги:\n"
            "- Ищу в контексте упоминание Void Core.\n"
            "- В документе Death_Star указано: Void Core — космическая станция-супероружие, "
            "построенная Stellar Dominion.\n"
            "- Она способна уничтожать целые планеты.\n"
            "\nОтвет:\n"
            "Void Core — гигантская боевая станция Stellar Dominion размером с луну. "
            "Она способна полностью уничтожать планеты и служит инструментом террора."
        ),
    },
]


class Retriever:
    """Embedding + vector search over the ChromaDB index."""

    def __init__(self, chroma_dir=CHROMA_DIR, collection=COLLECTION_NAME, model_name=EMBED_MODEL):
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.client.get_collection(collection)

    def search(self, query, k=TOP_K):
        vector = self.model.encode(query, normalize_embeddings=True).tolist()
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            hits.append({
                "text": doc,
                "source": meta["source"],
                "title": meta["title"],
                "chunk": meta["chunk_index"],
                "score": round(1 - dist, 4),
            })
        return hits


def build_context(hits):
    parts = []
    for i, hit in enumerate(hits, 1):
        parts.append(f"[Фрагмент {i} | источник: {hit['source']}]\n{hit['text']}")
    return "\n\n".join(parts)


def build_messages(query, hits):
    context = build_context(hits)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Few-shot: example question + ideal answer (with CoT steps)
    for example in FEW_SHOT:
        messages.append({"role": "user", "content": example["q"]})
        messages.append({"role": "assistant", "content": example["a"]})

    # Real request with retrieved context
    user_message = (
        f"Контекст:\n{context}\n\n"
        f"Вопрос: {query}"
    )
    messages.append({"role": "user", "content": user_message})
    return messages


class RAGBot:
    def __init__(self, api_key=None, base_url=LLM_BASE_URL, model=LLM_MODEL):
        self.retriever = Retriever()
        self.api_key = api_key or os.environ.get("AITUNNEL_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model
        if not self.api_key:
            raise RuntimeError("Не задан AITUNNEL_API_KEY")

    def _call_llm(self, messages):
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    def answer(self, query, k=TOP_K):
        hits = self.retriever.search(query, k=k)
        messages = build_messages(query, hits)
        answer = self._call_llm(messages)
        return {"query": query, "answer": answer, "sources": hits}


def repl():
    print("=" * 70)
    print("RAG-бот базы знаний Stellar Chronicles")
    print("Команды: /exit — выход, /sources — показать источники последнего ответа")
    print("=" * 70)
    bot = None
    last = None
    while True:
        try:
            query = input("\nВопрос> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break
        if not query:
            continue
        if query in ("/exit", "/quit"):
            print("Выход.")
            break
        if query == "/sources":
            if not last:
                print("Пока нет ответов.")
            else:
                for i, s in enumerate(last["sources"], 1):
                    print(f"  [{i}] {s['source']} (chunk {s['chunk']}, score={s['score']})")
            continue

        if bot is None:
            print("Загружаю модель и индекс...")
            bot = RAGBot()
        result = bot.answer(query)
        last = result
        print("\n" + result["answer"])
        srcs = ", ".join(sorted({s["source"] for s in result["sources"]}))
        print(f"\nИсточники: {srcs}")


def main():
    if len(sys.argv) > 1:
        bot = RAGBot()
        result = bot.answer(" ".join(sys.argv[1:]))
        print(result["answer"])
        print("\nИсточники: " + ", ".join(s["source"] for s in result["sources"]))
    else:
        repl()


if __name__ == "__main__":
    main()