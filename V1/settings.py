from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta
from prompts import SHORT_DESCRIPTION_PROMPT, PROMPT_TO_IMAGE_MODEL, PRESENTATION_STRUCTURE_PROMPT
import os
from dotenv import load_dotenv


load_dotenv()


DAYS_DELTA = 3

today = datetime.now()
yesterday = today - timedelta(days=DAYS_DELTA)
DATE_FROM = yesterday.strftime('%d.%m.%y')
DATE_TO = today.strftime('%d.%m.%y')



@dataclass
class Settings:

    # VK ===========================================================================================
    logic = {
        'parse': True,
        'process': True,
        'save_to_db': True,
        'save_to_file': True,
        'publicate': True
    }

    # VK ===========================================================================================
    vk: dict[str, Any] = field(default_factory=lambda: {
        'access_token': os.getenv('VK_ACCESS_TOKEN'),
        'group_id': os.getenv('VK_GROUP_ID'),
        'api_version': os.getenv('VK_API_VERSION', '5.131'),
    })

    
    # Parsers ======================================================================================
    sources = [
        {
            'enable': True,
            'source_name': 'sciencedaily',
            'parser_type': 'rss',
            'url': 'https://www.sciencedaily.com/rss/health_medicine.xml',
            'headers': {'User-Agent': 'Mozilla/5.0'},
            'date': {
                'date_from': DATE_FROM,        # 01.06.26
                'date_to': DATE_TO,          # 17.07.26
            },
            'number_of_articles': 100
        }
    ]

    # AI ===========================================================================================
    models = {
        'text_model': {
            'model': 'deepseek-r1:7b',       # deepseek-r1:7b
            'url': 'http://localhost:11434/api/generate',
            'stream': False,                 # Постепенная выдача ответа по токенам (эффект печатания)
            'temperature': 0.7,              # Креативность/случайность (0.0 - детерминировано, 1.0 - творчески)
            'top_p': 0.9,                    # Разнообразие выбора (ядровая выборка, отсекает маловероятные токены)
            'max_tokens': 8192,              # Максимальная длина ответа в токенах (~3-4 на символ слов для русского)
            'prompts': {
                'short_description_prompt': SHORT_DESCRIPTION_PROMPT,
                'presentation_structure_prompt': PRESENTATION_STRUCTURE_PROMPT,
                'prompt_to_image_model': PROMPT_TO_IMAGE_MODEL
            }
        },
        'image_model': {
            'model': 'pollinations',
            'url': 'https://image.pollinations.ai/prompt/',
            'width': '1024',
            'height': '1024',
        }
    }

    # DB ===========================================================================================
    _tables = {
        'articles': [
            # === ПОЛЯ ИЗ _Article ===
            'id TEXT PRIMARY KEY',  # UUID - используем TEXT вместо INTEGER
            'source TEXT',
            'article_text TEXT',
            'title_translated TEXT'
            'article_text_translated TEXT',
            'ai_description TEXT',
            'ai_description_translated TEXT',
            
            # === ПОЛЯ ИЗ _Article_Brief_Data ===
            'title TEXT',
            'link TEXT UNIQUE',
            'summary TEXT',
            'published TEXT',
            'feed_id TEXT',  # переименовано, чтобы не конфликтовать с id
            'guidislink BOOLEAN DEFAULT 0',
            
            # === ПОЛЯ ИЗ _TitleDetail ===
            'title_detail_type TEXT',
            'title_detail_language TEXT',
            'title_detail_base TEXT',
            'title_detail_value TEXT',
            
            # === ПОЛЯ ИЗ _SummaryDetail ===
            'summary_detail_type TEXT',
            'summary_detail_language TEXT',
            'summary_detail_base TEXT',
            'summary_detail_value TEXT',
            
            # === ПОЛЯ ИЗ _Link (список) ===
            # Для списка ссылок используем JSON
            'links_json TEXT',
            
            # === ПОЛЯ ИЗ published_parsed (time.struct_time) ===
            'published_parsed_year INTEGER',
            'published_parsed_month INTEGER',
            'published_parsed_day INTEGER',
            'published_parsed_hour INTEGER',
            'published_parsed_minute INTEGER',
            'published_parsed_second INTEGER',
            'published_parsed_weekday INTEGER',
            'published_parsed_yday INTEGER',
            'published_parsed_isdst INTEGER',
            
            # === СЛУЖЕБНЫЕ ПОЛЯ ===
            'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'VK_published BOOLEAN DEFAULT 0'

            # === Связанные таблицы ===

        ],
        'images': [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'article_id TEXT NOT NULL',
            'image_base64 TEXT',
        ]
    }
    save_data_to_table = 'articles'
    read_from_table = 'articles'
    field_to_compare = 'link'
            

    
