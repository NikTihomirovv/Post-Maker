
Post-Maker V2
Автоматический сбор, обработка и публикация научных статей из RSS-лент с использованием AI.

📖 Описание
Post-Maker V2 — это система для автоматического парсинга научных новостей из RSS-источников, обработки статей с помощью AI-моделей (перевод, суммаризация, генерация изображений) и публикации готовых постов в VK.

🚀 Возможности
Парсинг RSS-лент — сбор статей из множества источников (ScienceDaily, The Guardian, NPR и др.)

Обработка текста AI — генерация кратких описаний, перевод на русский язык

Генерация изображений — создание иллюстраций к статьям (через Pollinations.ai или Provod.ai)

Фильтрация контента — встроенный валидатор для исключения нежелательных тем

Сохранение в БД — хранение всех статей и изображений в SQLite

Публикация в VK — автоматический постинг в группу ВКонтакте

Экспорт в файлы — сохранение постов в папку с текстом и изображениями

⚙️ Установка
1. Клонирование репозитория
bash
git clone <repository-url>
cd Post-Maker/v2
2. Создание виртуального окружения
Windows:

bash
python -m venv venv
venv\Scripts\activate
Linux/macOS:

bash
python3 -m venv venv
source venv/bin/activate
3. Установка зависимостей
bash
pip install -r requrements.txt
requrements.txt:

txt
requests==2.31.0
openai==1.35.13
python-dotenv==1.0.1
feedparser==6.0.11
beautifulsoup4==4.12.3
python-pptx==0.6.23
Pillow==10.4.0
cairosvg==2.7.1
deep-translator==1.11.4
langdetect==1.0.9
4. Настройка переменных окружения
Создайте файл .env в корне проекта:

env
PROVOD_AI_API_KEY=your_provod_api_key
VK_ACCESS_TOKEN=your_vk_access_token
VK_GROUP_ID=your_group_id
5. Docker с DeepSeek (для локальной AI-модели)
Для работы с локальной моделью DeepSeek через Ollama:

Запуск контейнера:

bash
docker run -d --name ollama-deepseek -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  -v ./models:/root/.ollama/models \
  --restart unless-stopped ollama/ollama
Загрузка модели:

bash
docker exec -it ollama-deepseek ollama pull deepseek-r1:7b
Проверка:

bash
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:7b",
  "prompt": "Hello, world!"
}'
🏗️ Структура проекта
text
v2/
├── main.py                    # Точка входа
├── composition.py             # Сборка всех менеджеров
├── settings.py               # Настройки проекта
├── utils.py                  # Утилиты (перевод, определение языка)
├── prompts.py                # Промпты для AI
├── requrements.txt           # Зависимости
├── .env                      # Переменные окружения
│
├── managers/
│   ├── ai_manager/
│   │   ├── ai_manager.py     # Работа с AI-моделями
│   │   ├── ReadMe.md         # Документация AI Manager
│   │   └── requirements.txt  # Зависимости AI Manager
│   ├── parsers_manager.py    # Парсинг RSS и HTML
│   ├── posts_manager.py      # Управление постами
│   ├── db_manager.py         # Работа с SQLite
│   ├── vk_manager.py         # Публикация в VK
│   └── presentation_manager.py # Генерация презентаций
│
├── Posts/                    # Папка с сохранёнными постами
│   └── [название_статьи]/
│       ├── post_text.txt
│       └── images/
│           ├── 1.png
│           └── 2.png
│
└── resources/                # Ресурсы (дефолтные изображения)
🔧 Настройка
Конфигурация в settings.py
python
# Режимы работы
mode = {
    'debug': False,      # Отключает публикацию в VK
    'text_only': True,   # Отключает генерацию изображений
}

# Логические переключатели
logic = {
    'parse': True,                   # Парсинг RSS
    'process': True,                 # Обработка AI
    'generate_img': True,            # Генерация изображений
    'generate_short_description': True,  # Генерация краткого описания
    'translate': True,               # Перевод на русский
    'save_to_db': True,              # Сохранение в БД
    'save_to_file': True,            # Сохранение в файлы
    'publicate': True,               # Публикация в VK
}

# Источники RSS
sources = [
    {
        'enable': True,
        'source_name': 'sciencedaily',
        'url': 'https://www.sciencedaily.com/rss/health_medicine.xml',
        'number_of_articles': 10,
        'dates': {
            'date_from': DATE_FROM,
            'date_to': DATE_TO,
        }
    },
    # ... другие источники
]
Фильтрация контента
В main.py есть метод _validate(), который проверяет текст на наличие запрещённых слов. Вы можете редактировать список bad_words под свои нужды.

🚀 Запуск
bash
python main.py
🔄 Процесс работы:
Парсинг — сбор новых статей из RSS-источников

Обработка — для каждой статьи:

Генерация краткого описания через AI

Генерация изображений (опционально)

Перевод на русский язык

Сохранение — запись в SQLite базу данных

Публикация — постинг в VK (если включено)

Экспорт — сохранение постов в папку Posts/

🎨 Генерация изображений
Поддерживается два способа:

1. Бесплатный (Pollinations.ai)
Не требует API-ключа

Используется по умолчанию

Качество среднее, работает быстро

2. Платный (Provod.ai)
Требует пополнения баланса

Высокое качество (GPT Image 2, Gemini 3 Pro Image)

Цены от 0,20 ₽ за изображение

📦 AI Manager
Модуль managers/ai_manager/ вынесен в отдельный компонент и может использоваться независимо. Подробнее в AI Manager/ReadMe.md.

📋 Требования
Python 3.10+

Docker (для локальной модели DeepSeek)

Интернет-соединение

API-ключи:

Provod.ai (опционально, для платных моделей)

VK Access Token (для публикации)

📄 Лицензия
MIT

