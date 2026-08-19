from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta
from prompts import SHORT_DESCRIPTION_PROMPT, GENERATE_PROMPT_TO_IMAGE_MODEL, PRESENTATION_STRUCTURE_PROMPT, DEFAULT_PROMPT_TO_IMAGE_MODEL
import os
from dotenv import load_dotenv


load_dotenv()


DAYS_DELTA = 2
NUMBER_OF_ARTICLES_FROM_SOURCE = 10

today = datetime.now()
yesterday = today - timedelta(days=DAYS_DELTA)
DATE_FROM = yesterday.strftime('%d.%m.%y')
DATE_TO = today.strftime('%d.%m.%y')



@dataclass
class Settings:

    # ==============================================================================================
    mode = {
        'debug': False,                              # Проходит весь workflow кроме публикации, использует бесплатные модели
        'text_only': True,                           # Создает только тектсовые посты
    }

    logic = {
        'parse': True,
        'process': True,
        'generate_img': True,
        'use_default_img': False,                    # применится если генерация отключена
        'generate_prompt_to_img_model': True,
        'generate_short_description': True,
        'translate': True,
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
            'mapping_structure': (
                ('title','title'),
                ('summary', 'summary'),
                ('link', 'link'),
                ('published', 'pub_date'),
            ),
            'dates': {
                'date_from': DATE_FROM,        # 01.06.26
                'date_to': DATE_TO,          # 17.07.26
            },
            'number_of_articles': NUMBER_OF_ARTICLES_FROM_SOURCE
        },
        {
            'enable': True,
            'source_name': 'the guardian',
            'parser_type': 'rss',
            'url': 'https://www.theguardian.com/health/rss',
            'headers': {'User-Agent': 'Mozilla/5.0'},
            'mapping_structure': (
                ('title','title'),
                ('summary', 'summary'),
                ('link', 'link'),
                ('published', 'pub_date'),
            ),
            'dates': {
                'date_from': DATE_FROM,        # 01.06.26
                'date_to': DATE_TO,          # 17.07.26
            },
            'number_of_articles': NUMBER_OF_ARTICLES_FROM_SOURCE
        },
        {
            'enable': True,
            'source_name': 'NPR',
            'parser_type': 'rss',
            'url': 'https://feeds.npr.org/1128/rss.xml',
            'headers': {'User-Agent': 'Mozilla/5.0'},
            'mapping_structure': (
                ('title','title'),
                ('summary', 'summary'),
                ('link', 'link'),
                ('published', 'pub_date'),
            ),
            'dates': {
                'date_from': DATE_FROM,        # 01.06.26
                'date_to': DATE_TO,          # 17.07.26
            },
            'number_of_articles': NUMBER_OF_ARTICLES_FROM_SOURCE
        }
    ]

    # AI ===========================================================================================
    models = {
        'text_model': {
            'prompts': {
                'short_description_prompt': SHORT_DESCRIPTION_PROMPT,
                'presentation_structure_prompt': PRESENTATION_STRUCTURE_PROMPT,
                'generate_prompt_to_image_model': GENERATE_PROMPT_TO_IMAGE_MODEL,
                'default_prompt_to_image_model': DEFAULT_PROMPT_TO_IMAGE_MODEL,
            }
        }
    }

    # DB ===========================================================================================
    POST_CREATE_TABLE = 'post'
    POST_READ_TABLE  = 'post'
    POST_UPDATE_TABLE = 'post'
    POST_DELETE_TABLE = 'post'
    POST_FIELD_TO_COMPARE = 'link'

    IMAGE_TABLE = 'image'
            

    
