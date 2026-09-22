# Отчёт автотестирования RAG-бота

Золотой набор: **13** вопросов (8 известных, 5 пробелов).

## Сравнение: baseline vs improved

| Метрика | Baseline (dense) | Improved (hybrid) |
|---|---|---|
| Известные темы | 7/8 (0.875) | 8/8 (1.0) |
| Отказы (пробелы) | 5/5 (1.0) | 5/5 (1.0) |
| Общая точность | 12/13 (0.923) | 13/13 (1.0) |

## Результаты по вопросам

| ID | Вопрос | Ожидание | Baseline | Improved | Источники (improved) |
|---|---|---|---|---|---|
| G1 | Кто такой Dorin Venn? | answer | ✅ | ✅ | Luke_Skywalker.md, Torin_Mellis.md |
| G2 | Что такое Void Core и чем он опасен? | answer | ✅ | ✅ | Death_Star.md, HyperRelay.md |
| G3 | Какая организация называется Aether Guard? | answer | ✅ | ✅ | Jedi.md, Ahsoka_Tano.md |
| G4 | Что такое HyperRelay и чем он питается? | answer | ✅ | ✅ | HyperRelay.md, TIE_fighter.md |
| G5 | Кто такой Sheev Malachar? | answer | ✅ | ✅ | Darth_Sidious.md, Palpatine.md |
| G6 | Что такое Void Cabal? | answer | ✅ | ✅ | Sith.md, HyperRelay.md |
| G7 | Кто такой Torin Mellis? | answer | ✅ | ✅ | Torin_Mellis.md, Qui-Gon_Jinn.md |
| G8 | Кто такой Zephyr? | answer | ❌ | ✅ | Yoda.md, Alderaan.md |
| N1 | Кто такой Zarn Velkor? | refuse | ✅ | ✅ | Mace_Windu.md, Qui-Gon_Jinn.md |
| N2 | Что такое Synth Flux? | refuse | ✅ | ✅ | Han_Solo.md, Finn__Star_Wars_.md |
| N3 | На какой планете вырос Dorin Venn? | refuse | ✅ | ✅ | Luke_Skywalker.md, Torin_Mellis.md |
| N4 | Что такое планета Kaelos? | refuse | ✅ | ✅ | Geonosis.md, Dagobah.md |
| N5 | Кем был Kaelor Venn до того, как стал Zarn Velkor? | refuse | ✅ | ✅ | Torin_Mellis.md, Ahsoka_Tano.md |

## Оставшиеся проблемы (improved)

Провалов нет.
