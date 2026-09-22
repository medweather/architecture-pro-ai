"""Query the Stellar Chronicles vector index.

Usage:
    python3 query_index.py "Who is Zarn Velkor?"
    python3 query_index.py            # runs the built-in demo queries
"""

import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "stellar_chronicles"
EMBED_MODEL = "BAAI/bge-m3"
TOP_K = 3

DEMO_QUERIES = [
    "Who is Zarn Velkor and what is his relationship to Dorin Venn?",
    "What is the Void Core and what can it do?",
    "What is Synth Flux and how do the Aether Guard use it?",
]


def main():
    queries = sys.argv[1:] if len(sys.argv) > 1 else DEMO_QUERIES

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    print(f"Index contains {collection.count()} chunks.\n")

    for query in queries:
        print("=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)
        vector = model.encode(query, normalize_embeddings=True).tolist()
        result = collection.query(
            query_embeddings=[vector],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )
        for rank, (doc, meta, dist) in enumerate(zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ), 1):
            score = 1 - dist
            print(f"\n[{rank}] score={score:.4f}  source={meta['source']} "
                  f"(chunk {meta['chunk_index']})")
            print(f"    {doc[:280]}{'...' if len(doc) > 280 else ''}")
        print()


if __name__ == "__main__":
    main()