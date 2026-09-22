"""Run a fixed set of demo dialogues through the RAG bot and save the transcript.

Produces demo_dialogues.md with:
  - 5 successful in-domain dialogues
  - 2 out-of-domain questions that should trigger "Я не знаю"
"""

from pathlib import Path

from rag_bot import RAGBot

BASE_DIR = Path(__file__).resolve().parent

SUCCESS_QUERIES = [
    "Кто такой Zarn Velkor?",
    "Что такое Void Core и чем он опасен?",
    "Что такое Synth Flux?",
    "Кто такой Torin Mellis и кого он обучал?",
    "На какой планете вырос Dorin Venn?",
]

UNKNOWN_QUERIES = [
    "Как приготовить борщ?",
    "Кто выиграл чемпионат мира по футболу в 2022 году?",
]


def run():
    bot = RAGBot()
    lines = ["# Примеры диалогов RAG-бота\n"]

    lines.append("## Успешные диалоги (ответ по базе знаний)\n")
    for i, query in enumerate(SUCCESS_QUERIES, 1):
        result = bot.answer(query)
        sources = ", ".join(sorted({s["source"] for s in result["sources"]}))
        print(f"[OK {i}/{len(SUCCESS_QUERIES)}] {query}")
        lines.append(f"### {i}. {query}\n")
        lines.append(f"**Вопрос:** {query}\n")
        lines.append("**Ответ бота:**\n")
        lines.append("```")
        lines.append(result["answer"])
        lines.append("```")
        lines.append(f"**Источники:** {sources}\n")

    lines.append("\n## Случаи «Я не знаю» (вопрос вне базы знаний)\n")
    for i, query in enumerate(UNKNOWN_QUERIES, 1):
        result = bot.answer(query)
        sources = ", ".join(sorted({s["source"] for s in result["sources"]}))
        print(f"[UNK {i}/{len(UNKNOWN_QUERIES)}] {query}")
        lines.append(f"### {i}. {query}\n")
        lines.append(f"**Вопрос:** {query}\n")
        lines.append("**Ответ бота:**\n")
        lines.append("```")
        lines.append(result["answer"])
        lines.append("```")
        lines.append(f"**Найденные (нерелевантные) источники:** {sources}\n")

    (BASE_DIR / "demo_dialogues.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nSaved demo_dialogues.md")


if __name__ == "__main__":
    run()
