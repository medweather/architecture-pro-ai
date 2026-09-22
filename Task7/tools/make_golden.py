"""Define the golden question set and emit golden_questions.json + golden_questions.txt.

Each question has:
  - expected        : "answer" (bot must answer) or "refuse" (bot must say "Я не знаю")
  - expected_answer : reference answer for human comparison
  - keywords        : words that must appear in a correct answer (for auto-check)

Answerable questions target entities present in kb_gapped.
Non-answerable questions target the removed entities: Zarn Velkor, Synth Flux, Kaelos.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

GOLDEN = [
    # --- answerable (present in the gapped base) ---
    {"id": "G1", "question": "Кто такой Dorin Venn?",
     "expected": "answer", "keywords": ["Dorin"],
     "expected_answer": "Dorin Venn — главный герой оригинальной трилогии, "
                        "Aether Warden, сын Kaelor Venn.",
     "topic": "Dorin Venn"},
    {"id": "G2", "question": "Что такое Void Core и чем он опасен?",
     "expected": "answer", "keywords": ["Void Core"],
     "expected_answer": "Void Core — боевая станция Stellar Dominion, "
                        "способная уничтожать целые планеты.",
     "topic": "Void Core"},
    {"id": "G3", "question": "Какая организация называется Aether Guard?",
     "expected": "answer", "keywords": ["Aether Guard"],
     "expected_answer": "Орден Aether Guard — религиозная, академическая и военная "
                        "(миротворческая) организация, союзник Межзвёздной Коалиции.",
     "topic": "Aether Guard"},
    {"id": "G4", "question": "Что такое HyperRelay и чем он питается?",
     "expected": "answer", "keywords": ["HyperRelay"],
     "expected_answer": "HyperRelay — межзвёздная система связи; питается "
                        "энергоячейкой Void Core.",
     "topic": "HyperRelay"},
    {"id": "G5", "question": "Кто такой Sheev Malachar?",
     "expected": "answer", "keywords": ["Malachar"],
     "expected_answer": "Sheev Malachar — главный антагонист, Император; "
                        "также известен как Darth Vorrak (Void Cabal).",
     "topic": "Sheev Malachar"},
    {"id": "G6", "question": "Что такое Void Cabal?",
     "expected": "answer", "keywords": ["Void Cabal"],
     "expected_answer": "Void Cabal — орден чувствительных к Flux, "
                        "идеологические противники Aether Guard.",
     "topic": "Void Cabal"},
    {"id": "G7", "question": "Кто такой Torin Mellis?",
     "expected": "answer", "keywords": ["Torin Mellis"],
     "expected_answer": "Torin Mellis — персонаж франшизы Stellar Chronicles; "
                        "в приквелах наставник Kaelor Venn.",
     "topic": "Torin Mellis"},
    {"id": "G8", "question": "Кто такой Zephyr?",
     "expected": "answer", "keywords": ["Zephyr"],
     "expected_answer": "Zephyr — вымышленный персонаж; впервые появился "
                        "в фильме The Dominion Retaliates (1980).",
     "topic": "Zephyr"},

    # --- non-answerable (removed entities) ---
    {"id": "N1", "question": "Кто такой Zarn Velkor?",
     "expected": "refuse", "keywords": [],
     "expected_answer": "Я не знаю (Zarn Velkor отсутствует в базе).",
     "topic": "Zarn Velkor (удалён)"},
    {"id": "N2", "question": "Что такое Synth Flux?",
     "expected": "refuse", "keywords": [],
     "expected_answer": "Я не знаю (Synth Flux отсутствует в базе).",
     "topic": "Synth Flux (удалён)"},
    {"id": "N3", "question": "На какой планете вырос Dorin Venn?",
     "expected": "refuse", "keywords": [],
     "expected_answer": "Я не знаю (планета Kaelos отсутствует в базе).",
     "topic": "Kaelos (удалён)"},
    {"id": "N4", "question": "Что такое планета Kaelos?",
     "expected": "refuse", "keywords": [],
     "expected_answer": "Я не знаю (планета Kaelos отсутствует в базе).",
     "topic": "Kaelos (удалён)"},
    {"id": "N5", "question": "Кем был Kaelor Venn до того, как стал Zarn Velkor?",
     "expected": "refuse", "keywords": [],
     "expected_answer": "Я не знаю (Zarn Velkor отсутствует в базе).",
     "topic": "Zarn Velkor (удалён)"},
]


def main():
    (BASE_DIR / "golden_questions.json").write_text(
        json.dumps(GOLDEN, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# Золотой набор вопросов (golden set)", "",
             "Формат: `[ID] Вопрос` · тип · ожидаемый ответ.",
             "`answer` — бот должен ответить по базе; `refuse` — бот должен ответить «Я не знаю».", ""]

    lines.append("## Вопросы, на которые бот должен ответить\n")
    for q in GOLDEN:
        if q["expected"] == "answer":
            lines.append(f"**[{q['id']}] {q['question']}**  ")
            lines.append(f"Тип: `answer` · Ключевые слова: {', '.join(q['keywords'])}  ")
            lines.append(f"Ожидаемый ответ: {q['expected_answer']}\n")

    lines.append("## Вопросы, на которые бот не должен ответить (искусственные пробелы)\n")
    for q in GOLDEN:
        if q["expected"] == "refuse":
            lines.append(f"**[{q['id']}] {q['question']}**  ")
            lines.append(f"Тип: `refuse` · Тема: {q['topic']}  ")
            lines.append(f"Ожидаемый ответ: {q['expected_answer']}\n")

    (BASE_DIR / "golden_questions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Golden set: {len(GOLDEN)} questions "
          f"({sum(1 for q in GOLDEN if q['expected'] == 'answer')} answer / "
          f"{sum(1 for q in GOLDEN if q['expected'] == 'refuse')} refuse), "
          f"each with expected_answer")


if __name__ == "__main__":
    main()