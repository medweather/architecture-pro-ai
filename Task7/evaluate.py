"""Automated evaluation of the RAG bot on the golden set.

Runs the golden set twice:
  - baseline : dense-only retrieval (ChromaDB + bge-m3)
  - improved : hybrid retrieval (dense + lexical reranking)

Each run logs every request (baseline -> logs_baseline.jsonl,
improved -> logs.jsonl), then metrics are aggregated and compared.
"""

import json
from datetime import datetime
from pathlib import Path

from Task7.rag_bot import RAGBot, Retriever, is_refusal
from Task7.tools.hybrid_retriever import HybridRetriever

BASE_DIR = Path(__file__).resolve().parent
GOLDEN_FILE = BASE_DIR / "golden_questions.json"
LOG_FILE = BASE_DIR / "logs.jsonl"
LOG_BASELINE = BASE_DIR / "logs_baseline.jsonl"
RESULTS_FILE = BASE_DIR / "eval_results.json"
REPORT_FILE = BASE_DIR / "evaluation_report.md"


def keyword_hit(answer, keywords):
    low = answer.lower()
    return all(k.lower() in low for k in keywords) if keywords else False


def evaluate_one(q, result):
    answer = result["answer"]
    refusal = is_refusal(answer)
    if q["expected"] == "answer":
        correct = (not refusal) and keyword_hit(answer, q["keywords"])
        reason = ("ответ по базе" if correct
                  else "отказ вместо ответа" if refusal
                  else "ответ без ожидаемых ключевых слов")
    else:
        correct = refusal
        reason = "корректный отказ" if correct else "выдал ответ при отсутствии данных"
    return {
        "id": q["id"], "question": q["question"], "topic": q["topic"],
        "expected": q["expected"], "correct": correct, "reason": reason,
        "refusal": refusal, "answer": answer, "answer_length": len(answer),
        "sources": result["record"]["sources"],
    }


def run_mode(name, retriever, golden, log_path):
    log_path.write_text("", encoding="utf-8")
    bot = RAGBot(retriever=retriever, log_file=log_path)
    rows = []
    for q in golden:
        result = bot.answer(q["question"], log=True)
        row = evaluate_one(q, result)
        rows.append(row)
        print(f"  [{name}] {'OK ' if row['correct'] else 'FAIL'} {q['id']:3s} "
              f"{q['question'][:50]:52s} -> {row['reason']}")
    metrics = {
        "total": len(rows),
        "answerable_total": sum(1 for r in rows if r["expected"] == "answer"),
        "answerable_correct": sum(r["correct"] for r in rows if r["expected"] == "answer"),
        "refuse_total": sum(1 for r in rows if r["expected"] == "refuse"),
        "refuse_correct": sum(r["correct"] for r in rows if r["expected"] == "refuse"),
        "overall_correct": sum(r["correct"] for r in rows),
    }
    metrics["answerable_accuracy"] = round(
        metrics["answerable_correct"] / max(metrics["answerable_total"], 1), 3)
    metrics["refuse_accuracy"] = round(
        metrics["refuse_correct"] / max(metrics["refuse_total"], 1), 3)
    metrics["overall_accuracy"] = round(metrics["overall_correct"] / len(rows), 3)
    return rows, metrics


def main():
    golden = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))

    print("=== BASELINE: dense retrieval ===")
    base_rows, base_metrics = run_mode("base", Retriever(), golden, LOG_BASELINE)

    print("\n=== IMPROVED: hybrid retrieval ===")
    imp_rows, imp_metrics = run_mode("hyb", HybridRetriever(), golden, LOG_FILE)

    out = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "baseline": {"retriever": "dense (bge-m3)", "metrics": base_metrics, "results": base_rows},
        "improved": {"retriever": "hybrid (dense + lexical)", "metrics": imp_metrics, "results": imp_rows},
    }
    RESULTS_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(base_metrics, imp_metrics, base_rows, imp_rows)

    print(f"\nBaseline overall: {base_metrics['overall_accuracy']}")
    print(f"Improved overall: {imp_metrics['overall_accuracy']}")


def write_report(bm, im, base_rows, imp_rows):
    lines = ["# Отчёт автотестирования RAG-бота", "",
             f"Золотой набор: **{bm['total']}** вопросов "
             f"({bm['answerable_total']} известных, {bm['refuse_total']} пробелов).", "",
             "## Сравнение: baseline vs improved", "",
             "| Метрика | Baseline (dense) | Improved (hybrid) |",
             "|---|---|---|",
             f"| Известные темы | {bm['answerable_correct']}/{bm['answerable_total']} "
             f"({bm['answerable_accuracy']}) | {im['answerable_correct']}/{im['answerable_total']} "
             f"({im['answerable_accuracy']}) |",
             f"| Отказы (пробелы) | {bm['refuse_correct']}/{bm['refuse_total']} "
             f"({bm['refuse_accuracy']}) | {im['refuse_correct']}/{im['refuse_total']} "
             f"({im['refuse_accuracy']}) |",
             f"| Общая точность | {bm['overall_correct']}/{bm['total']} "
             f"({bm['overall_accuracy']}) | {im['overall_correct']}/{im['total']} "
             f"({im['overall_accuracy']}) |", "",
             "## Результаты по вопросам", "",
             "| ID | Вопрос | Ожидание | Baseline | Improved | Источники (improved) |",
             "|---|---|---|---|---|---|"]
    base_by_id = {r["id"]: r for r in base_rows}
    for r in imp_rows:
        b = base_by_id[r["id"]]
        bm_mark = "✅" if b["correct"] else "❌"
        im_mark = "✅" if r["correct"] else "❌"
        srcs = ", ".join(r["sources"][:2]) or "—"
        lines.append(f"| {r['id']} | {r['question']} | {r['expected']} | "
                     f"{bm_mark} | {im_mark} | {srcs} |")

    lines += ["", "## Оставшиеся проблемы (improved)", ""]
    fails = [r for r in imp_rows if not r["correct"]]
    if not fails:
        lines.append("Провалов нет.")
    else:
        for r in fails:
            lines.append(f"- **{r['id']}** «{r['question']}» — {r['reason']}. "
                         f"Источники: {', '.join(r['sources']) or '—'}")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()