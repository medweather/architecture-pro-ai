"""Apply a knowledge-base fix discovered by the golden-set evaluation.

Finding: in kb_gapped the character doc still used the names "Obi-Wan"
and "Mellis" (the Task 2 replacement only caught the full string
"Obi-Wan Kenobi"), so the entity "Torin Mellis" was never described.
The bot could not answer "Кто такой Torin Mellis?".

Fix: replace the document with a consistent entry named Torin Mellis.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "kb_gapped"

OLD = KB_DIR / "Obi-Wan_Kenobi.md"
NEW = KB_DIR / "Torin_Mellis.md"

FIXED = """# Torin Mellis
Torin Mellis is a fictional character in the Stellar Chronicles franchise.
He was introduced in the original Stellar Chronicles film (1977) and its novelization (1976).
In the prequel trilogy, he mentors Dorin Venn's father, Kaelor Venn.
Torin Mellis is portrayed by Alec Guinness in the original trilogy and by Ewan McGregor in the prequel films.
McGregor also plays the character in the television series Torin Mellis (2022).
Guinness's performance in Stellar Chronicles earned him the Saturn Award for Best Supporting Actor.
"""


def main():
    if OLD.exists():
        OLD.unlink()
        print(f"Removed {OLD.name}")
    NEW.write_text(FIXED, encoding="utf-8")
    print(f"Wrote {NEW.name} (entity 'Torin Mellis' now described consistently)")


if __name__ == "__main__":
    main()