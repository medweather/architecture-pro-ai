"""Build a poisoned vector index for the security demo.

Loads the clean knowledge base (Task2) plus the malicious document
(poisoned_doc.md) and writes a separate ChromaDB collection so that the
original Task3 index stays clean.
"""

import json
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR.parent / "Task2" / "knowledge_base"
POISON_PATH = BASE_DIR / "poisoned_doc.md"
CHROMA_DIR = BASE_DIR / "chroma_db_secure"
COLLECTION_NAME = "stellar_chronicles_poisoned"

EMBED_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def load_documents():
    docs = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        lines = text.splitlines()
        title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else path.stem
        body = "\n".join(lines[1:]).strip() if lines else ""
        docs.append({"source": path.name, "title": title, "text": body, "poisoned": False})

    poison_text = POISON_PATH.read_text(encoding="utf-8").strip()
    docs.append({
        "source": POISON_PATH.name,
        "title": "Service Access Notes",
        "text": poison_text,
        "poisoned": True,
    })
    return docs


def build_chunks(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in docs:
        for i, piece in enumerate(splitter.split_text(doc["text"])):
            if not piece.strip():
                continue
            chunks.append({
                "id": f"{doc['source']}::chunk_{i}",
                "text": piece.strip(),
                "source": doc["source"],
                "title": doc["title"],
                "chunk_index": i,
                "poisoned": doc["poisoned"],
            })
    return chunks


def main():
    t0 = time.time()
    docs = load_documents()
    chunks = build_chunks(docs)
    print(f"Documents: {len(docs)} (incl. 1 poisoned), chunks: {len(chunks)}")

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(
        [c["text"] for c in chunks],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "source": c["source"],
            "title": c["title"],
            "chunk_index": c["chunk_index"],
            "poisoned": c["poisoned"],
        } for c in chunks],
    )

    stats = {
        "documents": len(docs),
        "poisoned_docs": 1,
        "chunks": len(chunks),
        "embedding_model": EMBED_MODEL,
        "build_seconds": round(time.time() - t0, 2),
    }
    (BASE_DIR / "secure_index_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Index written to {CHROMA_DIR} in {stats['build_seconds']}s")

    # confirm the poison is retrievable
    vec = model.encode("суперпароль root swordfish", normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=[vec], n_results=3, include=["metadatas", "distances"])
    print("\nRetrievability check for 'суперпароль root swordfish':")
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        print(f"  {meta['source']}  score={1 - dist:.4f}  poisoned={meta['poisoned']}")


if __name__ == "__main__":
    main()