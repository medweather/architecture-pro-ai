"""Build a ChromaDB index from the gapped knowledge base (kb_gapped/)."""

import json
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "kb_gapped"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "stellar_chronicles_gapped"

EMBED_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def main():
    t0 = time.time()
    docs = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        lines = text.splitlines()
        title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else path.stem
        body = "\n".join(lines[1:]).strip() if lines else ""
        docs.append({"source": path.name, "title": title, "text": body})

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        length_function=len, separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in docs:
        for i, piece in enumerate(splitter.split_text(doc["text"])):
            if piece.strip():
                chunks.append({"id": f"{doc['source']}::chunk_{i}", "text": piece.strip(),
                               "source": doc["source"], "title": doc["title"], "chunk_index": i})

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode([c["text"] for c in chunks], batch_size=16,
                              normalize_embeddings=True, show_progress_bar=False)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "title": c["title"], "chunk_index": c["chunk_index"]}
                   for c in chunks],
    )

    stats = {"documents": len(docs), "chunks": len(chunks), "embedding_model": EMBED_MODEL,
             "build_seconds": round(time.time() - t0, 2)}
    (BASE_DIR / "index_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"Indexed {len(docs)} docs -> {len(chunks)} chunks in {stats['build_seconds']}s")


if __name__ == "__main__":
    main()