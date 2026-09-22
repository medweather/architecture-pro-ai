"""Build a vector index for the Stellar Chronicles knowledge base (Tab 2).

Embedding model: BAAI/bge-m3 (chosen in Task 1)
Vector store:    ChromaDB (persistent, cosine distance)

The script chunks the markdown documents, computes embeddings and writes a
persistent Chroma collection to Task3/chroma_db/.
"""

import json
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR.parent / "Task2" / "knowledge_base"
OUT_DIR = BASE_DIR
CHROMA_DIR = OUT_DIR / "chroma_db"
COLLECTION_NAME = "stellar_chronicles"

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
        docs.append({"source": path.name, "title": title, "text": body})
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
        pieces = splitter.split_text(doc["text"])
        for i, piece in enumerate(pieces):
            if not piece.strip():
                continue
            chunks.append({
                "id": f"{doc['source']}::chunk_{i}",
                "text": piece.strip(),
                "source": doc["source"],
                "title": doc["title"],
                "chunk_index": i,
            })
    return chunks


def main():
    t0 = time.time()

    print(f"[1/5] Loading documents from {KB_DIR} ...")
    docs = load_documents()
    print(f"      Loaded {len(docs)} documents.")

    print("[2/5] Splitting into chunks ...")
    chunks = build_chunks(docs)
    total_words = sum(len(c["text"].split()) for c in chunks)
    print(f"      Created {len(chunks)} chunks "
          f"(~{total_words} words, avg {total_words // max(len(chunks), 1)} words/chunk).")

    print(f"[3/5] Loading embedding model {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)
    dim = model.get_sentence_embedding_dimension()
    print(f"      Embedding dimension: {dim}.")

    print("[4/5] Computing embeddings ...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    print(f"      Computed {len(embeddings)} vectors in {time.time() - t0:.1f}s so far.")

    print(f"[5/5] Writing persistent ChromaDB collection to {CHROMA_DIR} ...")
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
        } for c in chunks],
    )

    elapsed = time.time() - t0
    stats = {
        "embedding_model": EMBED_MODEL,
        "embedding_dimension": dim,
        "vector_store": "ChromaDB (cosine)",
        "documents": len(docs),
        "chunks": len(chunks),
        "total_words": total_words,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "build_seconds": round(elapsed, 2),
    }
    (OUT_DIR / "index_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print(f"  Documents : {len(docs)}")
    print(f"  Chunks    : {len(chunks)}")
    print(f"  Dimension : {dim}")
    print(f"  Time      : {elapsed:.1f}s")
    print(f"  Index     : {CHROMA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()