import base64
import logging
import os
import time
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
PROVOD_AI_API_KEY = os.getenv('PROVOD_AI_API_KEY')


# Local (free) ==========================================================================================================
@dataclass
class DeepSeekLocalSettings:
    name: str = 'deepseek-r1:7b'
    url: str = 'http://localhost:11434/api/generate'
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 8192

@dataclass
class PolinationsSettings:
    name: str = 'pollinations'
    url: str = 'https://image.pollinations.ai/prompt/'
    width: int = 1024
    height: int = 1024


@dataclass
class LocalModels:
    deep_seek_local: DeepSeekLocalSettings = field(default_factory=DeepSeekLocalSettings)
    polinations: PolinationsSettings = field(default_factory=PolinationsSettings)


# Provod.ai (paid) ======================================================================================================
@dataclass
class DeepSeekV4Flash:
    name: str = 'deepseek-v4-flash-0731'
    temperature: int = 0.7
    max_tokens: int = 10000


@dataclass
class ProvodAiModels:
    api_key: str = PROVOD_AI_API_KEY
    url: str = 'https://api.provod.ai/v1'
    deep_seek_v4_flash: DeepSeekV4Flash = field(default_factory=DeepSeekV4Flash)


# Settings ==============================================================================================================
@dataclass
class Settings:
    use_paid_models: bool = True
    local_models: LocalModels = field(default_factory=LocalModels)
    provod_ai_models: ProvodAiModels = field(default_factory=ProvodAiModels)


# Manager ===============================================================================================================
class AIManager:
    """Класс для управления моделями."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()

        self.text_models_factory = TextModelsFactory()
        self.image_models_factory = ImageModelsFactory()
        self.text_model = self.text_models_factory.get_text_model(self.settings)
        self.image_model = self.image_models_factory.get_image_model(self.settings)

        self.is_initialized = self._check_models_init()


    def _check_models_init(self) -> bool:
        """Проверяет, инициализированы ли все модели."""
        
        if not self.text_model or not self.text_model.is_initialized:
            self.logger.error('❌ Текстовая модель не готова')
            return False
        
        if not self.image_model or not self.image_model.is_initialized:
            self.logger.error('❌ Модель изображений не готова')
            return False
        
        self.logger.info('✅ Все модели готовы')
        return True

    
    def destroy(self):
        """Закрывает сессию и освобождает ресурсы"""

        if self.text_model:
            self.text_model._destroy()

        if self.image_model:
            self.image_model._destroy()


    def process_text(self, text_to_process: str, prompt: str) -> str:
        """Перерабатывает полученный текст."""

        try:
            if not isinstance(prompt, str) or not prompt:
                self.logger.error(f'❌ Ошибка: промпт невалидный: {prompt}')
                return ''
            
            if not isinstance(text_to_process, str) or not text_to_process:
                self.logger.error(f'❌ Ошибка: текст для обработки пуст')
                return ''
            
            answer = self.text_model._generate(f'{prompt} {text_to_process}')
            
            if not answer:
                self.logger.warning('⚠️ Модель вернула пустой ответ')
                return ''
                
            return answer
            
        except Exception as e:
            self.logger.error(f'❌ Ошибка в обработке текста: {e}')
            return ''
        

    def generate_images(self, prompts: list[str]) -> list[str] | list[None]:
        """Генерирует картинки из списка запросов."""

        try:
            if not prompts or not isinstance(prompts, list):
                self.logger.error('❌ Отсутствуют промпты для генерации изображений')
                return []

            if not all(prompt and isinstance(prompt, str) and prompt.strip() for prompt in prompts):
                self.logger.error('❌ Некоторые промпты пустые или невалидные')
                return []

            images = []
            for prompt in prompts:
                image = self.image_model._generate(prompt)

                if image: 
                    images.append(image)

                else:
                    self.logger.error('❌ Не удалось получить изображение')
                
            if images and len(images) > 0:
                return images
            
            else:
                self.logger.warning('⚠️ Не удалось сгенерировать изображения')
                return []

        except Exception as e:
            self.logger.error(f'❌ Ошибка в обработке изображений: {e}')
            return []


# Фабрики ===============================================================================================================
class TextModelsFactory:
    """Фабрика для текстовых моделей."""

    @staticmethod
    def get_text_model(settings):

        match settings.use_paid_models:

            case True:
                return ProvodAiTextModel(settings)
            
            case False:
                return DeepSeekLocal(settings)


class ImageModelsFactory:
    """Фабрика для моделей для создания изображений."""

    @staticmethod
    def get_image_model(settings):

        match settings.use_paid_models:

            case True:
                return Polinations(settings)
            
            case False:
                return Polinations(settings)
        
                
# Бесплатные модели =====================================================================================================
class DeepSeekLocal:
    """Класс для работы с deepseek в docker."""

    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.session = requests.Session() 

        self.name = self.settings.local_models.deep_seek_local.name
        self.url = self.settings.local_models.deep_seek_local.url
        self.stream = self.settings.local_models.deep_seek_local.stream
        self.temperature = self.settings.local_models.deep_seek_local.temperature
        self.top_p = self.settings.local_models.deep_seek_local.top_p
        self.max_tokens = self.settings.local_models.deep_seek_local.max_tokens

        self.is_initialized = False
        self.model = None 
        self.model = self._set_model()


    def _destroy(self):
        """Закрывает сессию requests"""
        if self.session:
            self.session.close()


    def _set_model(self) -> str:
        """Проверка и установка модели."""

        try:
            base_url = self.url.replace('/api/generate', '')
            response = self.session.get(f'{base_url}/api/tags', timeout=5)
            response.raise_for_status()

            models = response.json().get('models', [])
            model_names = [m.get('name') for m in models]

            if self.name in model_names:
                self.logger.info('✅ Подключение к Ollama установлено')
                self.logger.info(f'✅ Доступная модель: {model_names}')
                self.is_initialized = True

                return self.name

            else:
                self.logger.error(f'❌ Модель {self.name} не найдена')
                return ''

        except requests.exceptions.ConnectionError:
            self.logger.error('❌ Не удалось подключиться к Ollama. Проверьте, запущен ли контейнер.')
            return None
        
        except Exception as e:
            self.logger.error(f'❌ Ошибка инициализации модели: {e}')
            return None


    def _generate(self, prompt: str) -> str:
        """Генерация ответа от модели."""

        try:
            if not self.is_initialized:
                self.logger.error('❌ Класс не инициализирован')
                return ''

            if not self.model:
                self.logger.error('❌ Модель не инициализирована')
                return ''

            if not isinstance(prompt, str) or prompt == '':
                self.logger.error('❌ Ошибка в получении промпта')
                return ''
        
            self.logger.info(f'✅Запрос к модели: {prompt[:50]}...')
            
            payload = {
                'model': self.name,
                'prompt': prompt,
                'stream': self.stream,
                'options': {
                    'temperature': self.temperature,
                    'top_p': self.top_p,
                    'num_predict': self.max_tokens
                }
            }
            
            response = self.session.post(
                self.url,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            
            data = response.json()
            answer = data.get('response', '')
            self.logger.info(f'✅ Получен ответ: {len(answer)} символов')
            return answer
            
        except requests.exceptions.Timeout:
            self.logger.error('❌ Таймаут при генерации')
            return ''
        
        except Exception as e:
            self.logger.error(f'❌ Ошибка генерации: {e}')
            return ''

            

class Polinations:
    """Класс для работы с polinations."""

    def __init__(self, settings):

        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.session = requests.Session()
        
        self.name = self.settings.local_models.polinations.name
        self.url = self.settings.local_models.polinations.url
        self.width = self.settings.local_models.polinations.width
        self.height = self.settings.local_models.polinations.height

        self.is_initialized = False
        self.model = None 
        self.model = self._set_model()

        
    def _destroy(self):
        """Закрывает сессию и освобождает ресурсы."""
        if self.session:
            self.session.close()


    def _set_model(self) -> str:
        """Проверка доступности модели."""

        try:
            if self.name != 'pollinations':
                self.logger.error('❌ Такой модели нет')
                return ''
            
            response = self.session.head(self.url, timeout=5)
            if response.status_code == 200:
                self.logger.info('✅ Подключение к Pollinations.ai установлено')
                self.is_initialized = True
                return self.name
            
            else: 
                self.logger.error(f'❌ Неожиданный статус: {response.status_code}')
                return ''
            
        except requests.exceptions.ConnectionError:
            self.logger.error('⚠️ Не удалось подключиться к Pollinations.ai. Проверьте интернет-соединение.')
            return ''
        
        except requests.exceptions.Timeout:
            self.logger.error('⚠️ Таймаут при подключении к Pollinations.ai')
            return ''
        
        except Exception as e:
            self.logger.error(f'⚠️ Ошибка инициализации: {e}')
            return ''
        
    
    def _generate(self, prompt: str) -> str:
        """Генерирует изображения и возвращает их в формате base64"""

        try:
            if not self.is_initialized:
                self.logger.error('❌ Класс не инициализирован')
                return ''

            if not self.model:
                self.logger.error('❌ Модель не инициализирована')
                return ''

            if not isinstance(prompt, str) or prompt == '':
                self.logger.error('❌ Ошибка в получении промпта')
                return ''

            self.logger.info(f'🎨 Начинаем генерацию изображения')
            encoded_prompt = prompt.replace(' ', '%20').replace('"', '%22')
            url = f"{self.url}{encoded_prompt}?width={self.width}&height={self.height}&nologo=true"
            start = time.time()
            response = requests.get(url, timeout=120)
            delta = time.time() - start

            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')

                if image_base64:
                    self.logger.info(f'✅ Готово ({delta:.2f} сек)')
                    return image_base64
                                
            else:
                self.logger.error(f'   ❌ Ошибка: {response.status_code}')
                return ''

        except Exception as e:
            self.logger.error(f'❌ Ошибка при генерации изображения: {e}')
            return ''


# Платные модели ========================================================================================================
class ProvodAiTextModel:
    """Класс для работы с моделя из provod.ai"""

    def __init__(self, settings):

        self.logger = logging.getLogger(__name__)
        self.settings = settings

        self.url = self.settings.provod_ai_models.url
        self.api_key = self.settings.provod_ai_models.api_key

        self.name = self.settings.provod_ai_models.deep_seek_v4_flash.name
        self.temperature = self.settings.provod_ai_models.deep_seek_v4_flash.temperature
        self.max_tokens = self.settings.provod_ai_models.deep_seek_v4_flash.max_tokens

        self.is_initialized = False
        self.client = None
        self.model = None
        self.model = self._set_model()


    def _destroy(self):
        """Закрывает сессию и освобождает ресурсы."""
        pass


    def _set_model(self) -> str:
        """Проверяет доступность модели."""

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.url
            )

            self.logger.info('✅ Подключение к Provod.ai установлено. Доступные модели:')

            available_models = []
            models = self.client.models.list()
            for model in models.data:
                available_models.append(model.id)
                self.logger.info(f'✅ {model.id}')

            if self.name not in available_models:
                self.logger.error(f'❌ Модели "{self.name}" нет в списке доступных')
                return ''

            self.logger.info(f'✅ Модель "{self.name}" найдена в списке доступных')
            self.is_initialized = True
            self.model = self.name
            return self.model

        except Exception as e:
            self.logger.error(f'❌ Ошибка подключения к provod.ai: {e}')
            return ''


    def _generate(self, prompt: str) -> str:
        """Генерация ответа от модели."""
    
        try:
            if not self.is_initialized:
                self.logger.error('❌ Класс не инициализирован')
                return ''
    
            if not self.model:
                self.logger.error('❌ Модель не инициализирована')
                return ''
    
            if not isinstance(prompt, str) or prompt == '':
                self.logger.error('❌ Ошибка в получении промпта')
                return ''
            
            self.logger.info(f'✅Запрос к модели: {prompt[:50]}...')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты — полезный ассистент."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            if response:
                answer = response.choices[0].message.content
                self.logger.info(f'✅ Получен ответ: {len(answer)} символов')
                return answer

            else: 
                self.logger.info(f'❌ Не удалось получить ответ от модели')
                return ''
            

        except requests.exceptions.Timeout:
            self.logger.error('❌ Таймаут при генерации')
            return ''
                
        except Exception as e:
            self.logger.error(f'❌ Ошибка генерации: {e}')
            return ''