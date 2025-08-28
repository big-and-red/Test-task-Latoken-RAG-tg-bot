# 🏆 LATOKEN RAG Telegram Bot - Хакатон Winner Project

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.3.6-green.svg)](https://github.com/pgvector/pgvector)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-21.10-blue.svg)](https://python-telegram-bot.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Победитель хакатона LATOKEN** 🥇 - Интеллектуальный Telegram бот с продвинутой RAG (Retrieval-Augmented Generation) системой для работы с корпоративными знаниями.

## 📖 Описание

Этот проект представляет собой высокопроизводительный Telegram бот, построенный на собственной реализации RAG-архитектуры. Бот способен обрабатывать документы различных форматов, создавать векторные представления текста и отвечать на вопросы пользователей на основе загруженной базы знаний.

### 🎯 Ключевые особенности

- **🧠 Собственная RAG-архитектура** - полностью кастомная реализация без использования готовых фреймворков
- **🔍 Гибридный поиск** - комбинация семантического поиска (70%) и TF-IDF по ключевым словам (30%)
- **📊 MMR Reranking** - оптимизация разнообразия результатов через Maximal Marginal Relevance
- **🗄️ Векторная БД** - PostgreSQL с pgvector для эффективного хранения и поиска эмбеддингов
- **📁 Мультиформатность** - поддержка PDF, DOCX, TXT, Excel, JSON файлов
- **🗜️ ZIP-архивы** - рекурсивная обработка архивов с любой вложенностью
- **🤖 Claude Integration** - использование Anthropic Claude для генерации ответов
- **⚡ Оптимизированный поиск** - двухэтапная система отбора кандидатов

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │───▶│   Handlers       │───▶│   Services      │
│                 │    │  • qviz          │    │  • RAG          │
│                 │    │  • add_source    │    │  • Search       │
│                 │    │  • choose_rag    │    │  • Embedding    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  PostgreSQL     │◀───│   Repositories   │◀───│   Text Service  │
│  + pgvector     │    │  • Source        │    │  • Chunking     │
│                 │    │  • Embedding     │    │  • Embeddings   │
└─────────────────┘    │  • Active RAG    │    └─────────────────┘
                       └──────────────────┘
```

## 🚀 Установка и настройка

### Предварительные требования

- Python 3.11+
- PostgreSQL 16+ с установленным pgvector
- Telegram Bot Token
- Anthropic API Key

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Test-task-Latoken-RAG-tg-bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# Telegram
TELEGRAM_TOKEN=your_telegram_bot_token

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
POSTGRES_USER=latoken
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=db_latoken

# Models cache path
RAG_EMBED_MODELS_CACHE=/path/to/your/models/cache
```

### 4. Настройка PostgreSQL + pgvector

```sql
-- Создание базы данных
CREATE DATABASE db_latoken;

-- Подключение к БД и установка pgvector
\c db_latoken;
CREATE EXTENSION vector;
```

### 5. Миграции

```bash
alembic upgrade head
```

### 6. Запуск бота

```bash
python main.py
```

## 🔧 API и команды

### Основные команды

| Команда | Описание |
|---------|----------|
| `/start` | Показать приветствие и доступные команды |
| `/help` | Подробная инструкция по использованию |
| `/add_rag_source` | Загрузка нового ZIP-архива с документами |
| `/choose_rag` | Выбор активного источника знаний |
| `/qviz` | Активация режима диалога с базой знаний |
| `/stop` | Деактивация режима диалога |
| `/test` | Тестирование знаний в виде квиза |

### Workflow использования

1. **Загрузка документов**: `/add_rag_source` → отправить ZIP-архив
2. **Выбор источника**: `/choose_rag` → выбрать из списка
3. **Диалог**: `/qviz` → задавать вопросы в текстовом формате

## 📊 Технические решения

### Векторный поиск

```python
# Гибридный поиск с весами
semantic_score = cosine_similarity(query_vector, doc_vector)
keyword_score = tfidf_similarity(query_text, doc_text)
final_score = semantic_score * 0.7 + keyword_score * 0.3
```

### MMR Reranking

```python
# Максимизация релевантности при обеспечении разнообразия
mmr_score = λ * relevance - (1 - λ) * max_similarity_to_selected
```

### Двухэтапный отбор кандидатов

1. **Первичная выборка**: `LIMIT * 2` кандидатов через векторный поиск
2. **Переранжирование**: MMR для финального отбора `LIMIT` результатов

## 🛠️ Технологический стек

### Backend & Core
- **Python 3.11+** - основной язык разработки
- **python-telegram-bot 21.10** - Telegram Bot API
- **SQLAlchemy 2.0** - ORM для работы с БД
- **Alembic** - миграции базы данных

### AI & ML
- **Anthropic Claude** - генерация ответов
- **sentence-transformers** - создание эмбеддингов
- **scikit-learn** - TF-IDF векторизация
- **numpy** - математические операции с векторами

### Database & Storage
- **PostgreSQL 16** - основная база данных
- **pgvector** - векторное хранилище и поиск
- **psycopg2** - PostgreSQL адаптер

### Document Processing
- **LangChain** - загрузка и обработка документов
- **PyPDF2** - работа с PDF файлами
- **python-docx** - обработка Word документов
- **openpyxl** - работа с Excel файлами
- **python-magic** - определение типов файлов

## 🏅 Достижения хакатона

- 🥇 **1-е место** на хакатоне LATOKEN
- 🛠️ **Полностью рабочий продукт** с функциональной архитектурой
- 📚 **Комплексная база знаний** по LATOKEN, включая Culture Deck

## 📁 Структура проекта

```
Test-task-Latoken-RAG-tg-bot/
├── alembic/                 # Миграции БД
├── configs/                 # Конфигурация приложения
├── db/                      # Модели и репозитории
│   ├── models.py           # SQLAlchemy модели
│   └── repos/              # Слой доступа к данным
├── handlers/                # Обработчики команд бота
│   ├── qviz.py            # Диалог с RAG
│   ├── add_rag_source.py  # Загрузка документов
│   └── choose_rag.py      # Выбор источника
├── services/                # Бизнес-логика
│   ├── rag_service.py     # RAG обработка
│   ├── search_service.py  # Поиск и ранжирование
│   └── embedding_service.py # Векторизация
├── utils/                   # Утилиты
│   └── custom_loaders.py  # Загрузчики документов
├── main.py                 # Точка входа
└── requirements.txt        # Зависимости
```

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.
