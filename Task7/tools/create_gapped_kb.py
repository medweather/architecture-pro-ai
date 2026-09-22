"""Create a 'gapped' knowledge base by removing 3 key entities.

Removed entities (whole document + every mention elsewhere):
  - Zarn Velkor   (character)
  - Synth Flux    (concept)
  - Kaelos        (planet)

Reads ../Task6/docs and writes ./kb_gapped/.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parent / "Task6" / "docs"
DST_DIR = BASE_DIR / "kb_gapped"

# entity -> set of regex patterns that match the entity or its aliases
GAPS = {
    "Zarn Velkor": [r"\bZarn\s+Velkor\b", r"\bVelkor\b"],
    "Synth Flux": [r"\bSynth[\s-]?Flux\b"],
    "Kaelos": [r"\bKaelos\b"],
}

# documents dedicated to a removed entity (deleted entirely)
DROP_FILES = {"Darth_Vader.md", "The_Force.md", "Tatooine.md"}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def gap_pattern():
    parts = []
    for patterns in GAPS.values():
        parts.extend(patterns)
    return re.compile("(" + "|".join(parts) + ")", re.IGNORECASE)


def strip_entity(text, pattern):
    kept = [s for s in _SENTENCE_SPLIT.split(text) if s and not pattern.search(s)]
    return "\n".join(kept).strip()


def main():
    DST_DIR.mkdir(exist_ok=True)
    pattern = gap_pattern()
    removed_files = []
    rewritten = []
    untouched = []

    for src in sorted(SRC_DIR.glob("*.md")):
        if src.name in DROP_FILES:
            removed_files.append(src.name)
            continue
        text = src.read_text(encoding="utf-8")
        if pattern.search(text):
            new_text = strip_entity(text, pattern)
            (DST_DIR / src.name).write_text(new_text + "\n", encoding="utf-8")
            rewritten.append(src.name)
        else:
            (DST_DIR / src.name).write_text(text, encoding="utf-8")
            untouched.append(src.name)

    print("Removed documents:")
    for f in removed_files:
        print(f"  - {f}")
    print(f"\nRewritten (mentions stripped): {len(rewritten)}")
    for f in rewritten:
        print(f"  - {f}")
    print(f"\nUntouched: {len(untouched)}")
    print(f"\nGapped corpus written to {DST_DIR} ({len(list(DST_DIR.glob('*.md')))} files)")


if __name__ == "__main__":
    main()