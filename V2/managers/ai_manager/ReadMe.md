AI Manager
Менеджер для работы с AI-моделями: локальными (Ollama + DeepSeek) и платными (Provod.ai API).

1. Описание
ai_manager — это модуль для унифицированной работы с различными AI-моделями. Поддерживает:

Локальные модели через Ollama (DeepSeek, Llama и др.)

Платные модели через Provod.ai (DeepSeek V4 Flash, GPT, Claude, Gemini и др.)

Генерацию изображений через Pollinations.ai (бесплатно)

Автоматический выбор модели через фабрики

Единый интерфейс для текстовой генерации и генерации изображений

2. Установка
2.1 Клонирование проекта
bash
git clone <repository-url>
cd Post-Maker/v2
2.2 Создание виртуального окружения
Windows:

bash
python -m venv venv
venv\Scripts\activate
Linux/macOS:

bash
python3 -m venv venv
source venv/bin/activate
2.3 Установка зависимостей
bash
pip install -r managers/ai_manager/requirements.txt
Содержимое requirements.txt:

txt
requests==2.31.0
openai==1.35.13
python-dotenv==1.0.1
2.4 Настройка переменных окружения
Создайте файл .env в корне проекта:

env
PROVOD_AI_API_KEY=your_api_key_here
VK_ACCESS_TOKEN=your_vk_token_here
VK_GROUP_ID=your_group_id
2.5 Docker с DeepSeek (для локальной модели)
Для работы с локальной моделью DeepSeek через Ollama:

Запуск контейнера:

bash
docker run -d --name ollama-deepseek -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  -v ./models:/root/.ollama/models \
  --restart unless-stopped ollama/ollama
Загрузка модели DeepSeek:

bash
docker exec -it ollama-deepseek ollama pull deepseek-r1:7b
Проверка работы:

bash
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:7b",
  "prompt": "Hello, world!"
}'
3. Использование
Базовый пример
python
from managers.ai_manager.ai_manager import AIManager

# Инициализация
ai = AIManager()

# Текстовая генерация
prompt = "Кратко опиши ИИ"
text = ai.process_text(
    text_to_process="Искусственный интеллект это...",
    prompt=prompt
)
print(text)

# Генерация изображений
images = ai.generate_images([
    "A beautiful sunset over the ocean",
    "A cat wearing a hat"
])
Переключение между моделями
В ai_manager.py настройка use_paid_models:

python
@dataclass
class Settings:
    use_paid_models: bool = True  # True - Provod.ai, False - локальный DeepSeek
    # ...
4. Структура модуля
text
managers/ai_manager/
├── ai_manager.py        # Основной файл
├── requirements.txt     # Зависимости
├── ReadMe.md           # Этот файл
└── __init__.py         # (опционально)
Классы
Класс	Назначение
AIManager	Главный менеджер, точка входа
DeepSeekLocal	Локальная модель через Ollama
Polinations	Генерация изображений (бесплатно)
ProvodAiTextModel	Платные модели через Provod.ai
TextModelsFactory	Фабрика для выбора текстовой модели
ImageModelsFactory	Фабрика для выбора модели изображений
5. Примеры использования
Только текст (без изображений)
python
ai = AIManager()
result = ai.process_text(
    text_to_process="Расскажи о космосе",
    prompt="Ты — научный ассистент. Ответь кратко:"
)
Генерация нескольких изображений
python
ai = AIManager()
prompts = [
    "A futuristic city at night",
    "A robot painting a picture",
    "A spaceship landing on Mars"
]
images = ai.generate_images(prompts)
for i, img in enumerate(images):
    print(f"Изображение {i+1}: {len(img)} символов")
6. Особенности
Локальная модель (DeepSeek)
Бесплатная

Требует Docker с Ollama

Работает офлайн

Медленнее, чем облачные решения

Платная модель (Provod.ai)
Требует API-ключ и пополнение баланса

Быстрый ответ

Доступ к новейшим моделям

Цены: от 12 ₽ за 1 млн токенов

Генерация изображений
Использует Pollinations.ai (бесплатно)

Не требует API-ключа

Работает только онлайн

Возвращает изображения в формате base64

Так
Она будут в отдельном репозитории
Напиши одним ответом все что выше только без пути после git clone
и в разметке md
AI Manager
Менеджер для работы с AI-моделями: локальными (Ollama + DeepSeek) и платными (Provod.ai API).

1. Описание
ai_manager — это модуль для унифицированной работы с различными AI-моделями. Поддерживает:

Локальные модели через Ollama (DeepSeek, Llama и др.)

Платные модели через Provod.ai (DeepSeek V4 Flash, GPT, Claude, Gemini и др.)

Генерацию изображений через Pollinations.ai (бесплатно)

Автоматический выбор модели через фабрики

Единый интерфейс для текстовой генерации и генерации изображений

2. Установка
2.1 Клонирование репозитория
bash
git clone <repository-url>
cd <project-directory>
2.2 Создание виртуального окружения
Windows:

bash
python -m venv venv
venv\Scripts\activate
Linux/macOS:

bash
python3 -m venv venv
source venv/bin/activate
2.3 Установка зависимостей
bash
pip install -r requirements.txt
Содержимое requirements.txt:

txt
requests==2.31.0
openai==1.35.13
python-dotenv==1.0.1
2.4 Настройка переменных окружения
Создайте файл .env в корне проекта:

env
PROVOD_AI_API_KEY=your_api_key_here
2.5 Docker с DeepSeek (для локальной модели)
Для работы с локальной моделью DeepSeek через Ollama:

Запуск контейнера:

bash
docker run -d --name ollama-deepseek -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  -v ./models:/root/.ollama/models \
  --restart unless-stopped ollama/ollama
Загрузка модели DeepSeek:

bash
docker exec -it ollama-deepseek ollama pull deepseek-r1:7b
Проверка работы:

bash
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:7b",
  "prompt": "Hello, world!"
}'
3. Использование
Базовый пример
python
from ai_manager import AIManager

# Инициализация
ai = AIManager()

# Текстовая генерация
prompt = "Кратко опиши ИИ"
text = ai.process_text(
    text_to_process="Искусственный интеллект это...",
    prompt=prompt
)
print(text)

# Генерация изображений
images = ai.generate_images([
    "A beautiful sunset over the ocean",
    "A cat wearing a hat"
])
Переключение между моделями
В ai_manager.py настройка use_paid_models:

python
@dataclass
class Settings:
    use_paid_models: bool = True  # True - Provod.ai, False - локальный DeepSeek
    # ...
4. Структура модуля
text
ai_manager/
├── ai_manager.py        # Основной файл
├── requirements.txt     # Зависимости
├── ReadMe.md           # Этот файл
└── __init__.py         # (опционально)
Классы
Класс	Назначение
AIManager	Главный менеджер, точка входа
DeepSeekLocal	Локальная модель через Ollama
Polinations	Генерация изображений (бесплатно)
ProvodAiTextModel	Платные модели через Provod.ai
TextModelsFactory	Фабрика для выбора текстовой модели
ImageModelsFactory	Фабрика для выбора модели изображений
5. Примеры использования
Только текст (без изображений)
python
ai = AIManager()
result = ai.process_text(
    text_to_process="Расскажи о космосе",
    prompt="Ты — научный ассистент. Ответь кратко:"
)
Генерация нескольких изображений
python
ai = AIManager()
prompts = [
    "A futuristic city at night",
    "A robot painting a picture",
    "A spaceship landing on Mars"
]
images = ai.generate_images(prompts)
for i, img in enumerate(images):
    print(f"Изображение {i+1}: {len(img)} символов")
Использование с собственными настройками
python
from ai_manager import Settings, AIManager

# Создаем кастомные настройки
settings = Settings()
settings.use_paid_models = False  # Используем локальную модель

ai = AIManager(settings)
result = ai.process_text("Привет!", "Ты — полезный ассистент.")
6. Особенности
Локальная модель (DeepSeek)
Бесплатная

Требует Docker с Ollama

Работает офлайн

Медленнее, чем облачные решения

Платная модель (Provod.ai)
Требует API-ключ и пополнение баланса

Быстрый ответ

Доступ к новейшим моделям

Цены: от 12 ₽ за 1 млн токенов

Генерация изображений
Использует Pollinations.ai (бесплатно)

Не требует API-ключа

Работает только онлайн

Возвращает изображения в формате base64

7. Требования
Python 3.10+

Docker (для локальной модели)

Интернет-соединение (для платных моделей и генерации изображений)

8. Лицензия
MIT