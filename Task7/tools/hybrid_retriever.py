"""Hybrid retriever: dense (bge-m3) + lexical reranking.

Short queries such as "Кто такой Zephyr?" are poorly served by dense
retrieval alone: many documents share generic phrasing, so the rare proper
name does not dominate the embedding. Adding a lexical overlap term makes
the proper name decisive.

final_score = (1 - alpha) * dense_score + alpha * lexical_overlap
"""

import re
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "stellar_chronicles_gapped"
EMBED_MODEL = "BAAI/bge-m3"

ALPHA = 0.4            # weight of the lexical component
STOPWORDS = {"кто", "такой", "такая", "что", "чем", "как", "какая", "какой",
             "где", "когда", "это", "the", "is", "a", "an", "of", "and", "for"}

_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]{3,}")


def _tokens(text):
    return {t for t in (m.group().lower() for m in _TOKEN_RE.finditer(text))
            if t not in STOPWORDS}


def lexical_overlap(query, text):
    q = _tokens(query)
    if not q:
        return 0.0
    t = _tokens(text)
    return len(q & t) / len(q)


class HybridRetriever:
    def __init__(self, alpha=ALPHA):
        self.alpha = alpha
        self.model = SentenceTransformer(EMBED_MODEL)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_collection(COLLECTION_NAME)

    def search(self, query, k=3):
        vector = self.model.encode(query, normalize_embeddings=True).tolist()
        n = max(self.collection.count(), k)
        result = self.collection.query(
            query_embeddings=[vector], n_results=n,
            include=["documents", "metadatas", "distances"])

        combined = []
        for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0],
                                   result["distances"][0]):
            dense = 1 - dist
            lex = lexical_overlap(query, doc)
            score = (1 - self.alpha) * dense + self.alpha * lex
            combined.append({
                "text": doc, "source": meta["source"], "title": meta["title"],
                "chunk": meta["chunk_index"],
                "dense_score": round(dense, 4),
                "lexical": round(lex, 4),
                "score": round(score, 4),
            })
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:k]