"""Incremental knowledge-base index updater.

Scans docs/ for new, modified and deleted documents, recomputes only what
changed, and updates the persistent ChromaDB index. Writes a human-readable
log and a structured JSONL log.

Usage:
    python3 update_index.py
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = BASE_DIR / "logs"
CHROMA_DIR = BASE_DIR / "chroma_db"
STATE_FILE = BASE_DIR / "state.json"
LOG_FILE = LOGS_DIR / "update.log"
JSONL_FILE = LOGS_DIR / "update_log.jsonl"

COLLECTION_NAME = "stellar_chronicles_live"
EMBED_MODEL = "BAAI/bge-m3"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


# --- logging -----------------------------------------------------------------

def log(message, level="INFO", log_lines=None):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{stamp} [{level}] {message}"
    print(line)
    LOGS_DIR.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if log_lines is not None:
        log_lines.append(line)


def write_jsonl(record):
    LOGS_DIR.mkdir(exist_ok=True)
    with JSONL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# --- helpers -----------------------------------------------------------------

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_source():
    """Return {relative_path: sha256} for all markdown docs."""
    result = {}
    for path in sorted(DOCS_DIR.rglob("*.md")):
        result[str(path.relative_to(DOCS_DIR))] = file_hash(path)
    return result


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_run": None, "files": {}}


def save_state(state):
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [c.strip() for c in splitter.split_text(text) if c.strip()]


# --- main update -------------------------------------------------------------

def main():
    started = time.time()
    log_lines = []
    log("=== update_index.py started ===", log_lines=log_lines)

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    state = load_state()
    prev_files = state.get("files", {})
    current = scan_source()

    added = sorted(set(current) - set(prev_files))
    removed = sorted(set(prev_files) - set(current))
    modified = sorted(p for p in set(current) & set(prev_files)
                      if current[p] != prev_files[p]["hash"])

    log(f"Scanned {len(current)} files: "
        f"{len(added)} added, {len(modified)} modified, {len(removed)} removed.",
        log_lines=log_lines)

    errors = 0

    # delete stale chunks first
    for rel in removed + modified:
        try:
            collection.delete(where={"source": rel})
        except Exception as exc:
            errors += 1
            log(f"ERROR deleting old chunks for {rel}: {exc}", "ERROR", log_lines)

    added_chunks = 0
    touched = added + modified

    for rel in touched:
        try:
            text = (DOCS_DIR / rel).read_text(encoding="utf-8").strip()
            lines = text.splitlines()
            title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else Path(rel).stem
            body = "\n".join(lines[1:]).strip() if lines else ""
            pieces = split_text(body)

            embeddings = model.encode(pieces, normalize_embeddings=True,
                                      show_progress_bar=False)
            collection.add(
                ids=[f"{rel}::chunk_{i}" for i in range(len(pieces))],
                embeddings=[e.tolist() for e in embeddings],
                documents=pieces,
                metadatas=[{"source": rel, "title": title, "chunk_index": i}
                           for i in range(len(pieces))],
            )
            added_chunks += len(pieces)
        except Exception as exc:
            errors += 1
            log(f"ERROR indexing {rel}: {exc}", "ERROR", log_lines)

    # persist new state
    new_files = {}
    for rel, digest in current.items():
        if rel in prev_files and prev_files[rel]["hash"] == digest:
            new_files[rel] = prev_files[rel]          # unchanged, keep chunk count
        else:
            new_files[rel] = {
                "hash": digest,
                "chunks": sum(
                    1 for c in collection.get(where={"source": rel})["ids"]
                ),
            }
    save_state({"last_run": state.get("last_run"), "files": new_files})

    total_chunks = collection.count()
    elapsed = round(time.time() - started, 2)

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "files_added": len(added),
        "files_modified": len(modified),
        "files_removed": len(removed),
        "new_chunks": added_chunks,
        "index_size_chunks": total_chunks,
        "errors": errors,
        "duration_seconds": elapsed,
    }
    write_jsonl(summary)

    log(f"index updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, "
        f"{len(touched)} files changed, {added_chunks} chunks added, "
        f"{errors} errors, index size {total_chunks} chunks, {elapsed}s.",
        log_lines=log_lines)
    log("=== update_index.py finished ===", log_lines=log_lines)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())