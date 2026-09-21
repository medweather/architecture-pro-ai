# Исследование моделей и инфраструктуры для RAG-бота QuantumForge Software

---

## 1. Сравнение LLM-моделей

### Локальные модели (Llama 3.1 8B, Qwen 2.5, Mistral 7B)

Качество: Llama 3.1 8B и Qwen 2.5 сопоставимы с GPT-4o-mini на summarization и QA. На сложных инструкциях (SOC 2) уступают GPT-4o на 15-20%. Mistral 7B слаб на русском языке.

Скорость: 20-40 токенов/с на одном GPU A10 (24 GB). Приемлемо для асинхронного режима.

Стоимость: аренда A10 - 15 000 $/год. Покупка A100 - 8 000 $ единоразово плюс 3 000 $/год на обслуживание. Требуется MLOps-инженер.

Развёртывание: vLLM или TGI, квантование (GGUF, AWQ) - 1-2 дня.

Конфиденциальность: данные не покидают контур компании, полный контроль.

Русский язык: базово поддерживается, но качество RAG на русском ниже, чем на английском. Нужен файнтюнинг.

Источники: [Llama 3.1](https://huggingface.co/meta-llama/Llama-3.1-8B), [Qwen 2.5](https://huggingface.co/Qwen/Qwen2.5-7B), [Mistral 7B](https://huggingface.co/mistralai/Mistral-7B-v0.3), [vLLM](https://github.com/vllm-project/vllm)

### Облачные модели (GPT-4o, GPT-4o-mini, YandexGPT)

Качество: GPT-4o - лучшая точность и работа с multilanguage. YandexGPT силён на русскоязычных текстах, но уступает OpenAI на английском контенте (ADR, API-документация).

Скорость: GPT-4o-mini - 90 токенов/с, GPT-4o - 60 токенов/с. Ответ менее чем за 2 секунды. YandexGPT - 50 токенов/с.

Стоимость: при ~500 запросах/день (~1.5 млн токенов/мес) GPT-4o-mini - 15 $/мес, GPT-4o - 100 $/мес. YandexGPT вдвое дешевле.

Развёртывание: API-ключ - 5 минут. Встроенный content filtering, rate limiting, SLA 99.9%.

Конфиденциальность: данные уходят на внешние серверы. OpenAI не использует API-данные для обучения (при отключённой опции), но факт передачи - риск для SOC 2.

Русский язык: GPT-4o - отлично. YandexGPT - нативный лидер по качеству.

Источники: [OpenAI Pricing](https://openai.com/api/pricing/), [OpenAI Models](https://platform.openai.com/docs/models), [YandexGPT](https://yandex.cloud/ru/docs/yandexgpt/)

### Вывод по LLM

Для QuantumForge критичны конфиденциальность (SOC 2) и качество на двух языках. Рекомендуется гибрид: sensitive-запросы - к локальной LLM, общие - к облачной. Альтернатива - облачная с BAA (Business Associate Agreement) и аудитом провайдера.

---

## 2. Сравнение моделей эмбеддингов

### Локальные модели (BAAI/bge-m3, multilingual-e5-large)

Скорость индексации: на CPU 16 ядер - 200 док./с (bge-m3), 150 док./с (e5-large). На GPU A10 - до 2000 док./с. Индекс на ~21 000 документов - ~2 минуты (GPU) или ~15 минут (CPU). Прирост 400 стр./мес индексируется за секунды.

Качество: MTEB 64-65% (bge-m3), 63-64% (e5-large). bge-m3 поддерживает sparse + dense retrieval. Для двуязычного контента bge-m3 - лучший open-source вариант.

Стоимость: бесплатно (MIT/Apache 2.0). Затраты только на железо.

Источники: [BGE-M3](https://huggingface.co/BAAI/bge-m3), [multilingual-e5-large](https://huggingface.co/intfloat/multilingual-e5-large), [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)

### Облачные модели (OpenAI text-embedding-3-large)

Скорость индексации: ~500 док./с через API (rate limit 3000 RPM). ~21 000 документов - ~40 секунд.

Качество: MTEB 64.6%, стабильное качество на 100+ языках. Варьируемая размерность (256-3072) экономит память векторной БД.

Стоимость: $0.13/1M токенов. Для ~21 000 документов (~15M токенов) - $2 единоразово за полный индекс. Прирост 400 стр./мес - $0.05/мес.

Источники: [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

### Вывод по эмбеддингам

Для SOC 2 и конфиденциальности рекомендуется bge-m3 (BAAI): сопоставимое качество, hybrid retrieval (dense + sparse), полностью локально. Статья: https://arxiv.org/abs/2402.03216
