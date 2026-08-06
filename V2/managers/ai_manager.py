import requests
import json
import logging
from typing import Optional
import requests
import json
import base64
import requests
import time
import base64


class AIManager:
    """Класс для управления моделями."""

    def __init__(self, _settings):
        self._logger = logging.getLogger(__name__)
        self._settings = _settings

        # Текстовая модель
        self._text_model = TextModel(_settings=_settings)
        self._image_model = ImageModel(_settings=_settings)

    
    def destroy(self):
        """Закрывает сессию и освобождает ресурсы"""
        if self._text_model:
            self._text_model.destroy()

        if self._image_model:
            self._image_model.destroy()
            
        # self._logger.info('✅ AIManager ресурсы освобождены')


    def process_text(self, _text_to_process: str, _prompt: str) -> str:

        answer = ''
        if isinstance(_prompt, str) or _prompt != '':
            if _text_to_process:
                answer = self._text_model.generate(f'{_prompt} {_text_to_process}')

        else:
            self._logger.error(f'❌ Ошибка в получении промпта: {_prompt}')
            return None

        return answer
    

    def generate_image(self, _prompts: list[str]) -> list[str]:

        if not _prompts or not isinstance(_prompts, list):
            self._logger.error('❌ Отсутствуют промпты для генерации изображений')
            return []
        
        images = self._image_model.generate(_prompts)
            
        if images and len(images) > 0:
            return images
        
        else:
            self._logger.warning('⚠️ Не удалось сгенерировать изображения')
            return []


class TextModel:
    """Класс для работы с текстовой моделью."""

    def __init__(self, _settings):
        self._logger = logging.getLogger(__name__)
        self._settings = _settings
        self._session = requests.Session() 
        self._model_name = None 
        
        self._model_name = self._set_model()
        self._model_url = self._settings.models['text_model']['url']
        self._params = self._settings.models['text_model']


    def destroy(self):
        """Закрывает сессию requests"""
        if self._session:
            self._session.close()
            # self._logger.info('✅ Сессия TextModel закрыта')


    def _set_model(self) -> Optional[str]:
        """Проверка и установка модели."""

        try:
            _model_name = self._settings.models['text_model']['model']
            _base_url = self._settings.models['text_model']['url']
            _base_url = _base_url.replace('/api/generate', '')
            
            response = self._session.get(f'{_base_url}/api/tags', timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m.get('name') for m in models]
            
            # self._logger.info('✅ Подключение к Ollama установлено')
            # self._logger.info(f'✅ Доступные модели: {model_names}')

            if _model_name not in model_names:
                self._logger.warning(f'❌ Модель {_model_name} не найдена')
                # self._logger.info(f' Загружаем модель {_model_name}...')
                
                if self._pull_model(_model_name, _base_url):
                    # self._logger.info(f'✅ Модель {_model_name} загружена')
                    return _model_name
                
                else:
                    self._logger.error('❌ Не удалось загрузить модель')
                    if model_names:
                        # self._logger.info(f'Используем: {model_names[0]}')
                        return model_names[0]
                    return None
            
            # self._logger.info(f'✅ Модель {_model_name} доступна')
            return _model_name

        except requests.exceptions.ConnectionError:
            self._logger.error('❌ Не удалось подключиться к Ollama. Проверьте, запущен ли контейнер.')
            return None
        
        except Exception as e:
            self._logger.error(f'❌ Ошибка инициализации модели: {e}')
            return None


    def _pull_model(self, model_name: str, base_url: str) -> bool:
        """Загрузка модели."""

        try:
            # self._logger.info(f'Загрузка модели {model_name}...')
            
            response = self._session.post(
                f'{base_url}/api/pull',
                json={'model': model_name},
                stream=True,
                timeout=600
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    # if 'status' in data:
                    #     self._logger.info(f'  {data['status']}')
                    if data.get('success'):
                        return True
            return True
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка загрузки: {e}')
            return False


    def generate(self, _prompt: str) -> str:
        """Генерация ответа от модели."""

        if not self._model_name:
            self._logger.error('❌ Модель не инициализирована')
            return 'Ошибка: модель не доступна'

        try:
            # self._logger.info(f'     Запрос к модели: {_prompt[:50]}...')
            
            payload = {
                'model': self._model_name,
                'prompt': _prompt,
                'stream': self._params.get('stream', False),
                'options': {
                    'temperature': self._params.get('temperature', 0.7),
                    'top_p': self._params.get('top_p', 0.9),
                    'num_predict': self._params.get('max_tokens', 2048)
                }
            }
            
            response = self._session.post(
                self._model_url,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            
            data = response.json()
            answer = data.get('response', '')
            # self._logger.info(f'✅ Получен ответ: {len(answer)} символов')
            return answer
            
        except requests.exceptions.Timeout:
            self._logger.error('❌ Таймаут при генерации')
            return 'Ошибка: таймаут'
        
        except Exception as e:
            self._logger.error(f'❌ Ошибка генерации: {e}')
            return f'Ошибка: {e}'
        

class ImageModel:

    def __init__(self, _settings):

        self._logger = logging.getLogger(__name__)
        self._settings = _settings
        self._session = requests.Session() 
        self._model_name = None 
        
        # self._model_name = self._set_model()
        self._model_url = self._settings.models['image_model']['url']
        self._params = self._settings.models['image_model']
        self._set_model()

    
    def destroy(self):
        """Закрывает сессию и освобождает ресурсы."""
        if self._session:
            self._session.close()
            # self._logger.info('✅ Сессия ImageModel закрыта')


    def _set_model(self) -> bool:
        """Проверка доступности модели."""

        try:
            if self._params['model'] != 'pollinations':
                self._logger.error('Такой модели нет')
                return False
            
            # self._logger.info('Проверка подключения к pollinations.ai')

            _response = self._session.head(self._model_url, timeout=5)
            if _response.status_code == 200:
                # self._logger.info('✅ Подключение к Pollinations.ai установлено')
                return True
            
            elif _response.status_code == 405:
                # self._logger.info('✅ Подключение к Pollinations.ai установлено (метод не поддерживается)')
                return True
            
            else: 
                self._logger.warning(f'⚠️ Неожиданный статус: {_response.status_code}')
            return False
            
        except requests.exceptions.ConnectionError:
            self._logger.warning('⚠️ Не удалось подключиться к Pollinations.ai. Проверьте интернет-соединение.')
            return False
        except requests.exceptions.Timeout:
            self._logger.warning('⚠️ Таймаут при подключении к Pollinations.ai')
            return False
        except Exception as e:
            self._logger.warning(f'⚠️ Ошибка инициализации: {e}')
            return False
        
    
    def generate(self, _prompts: list[str]) -> Optional[list[str]]:
        """
        Генерирует изображения и возвращает их в формате base64
        """
        
        _url = self._params.get('url', None)
        _width = self._params.get('width', '1024')
        _height = self._params.get('height', '1024')

        if not _url or not isinstance(_url, str):
            self._logger.error('❌ Ошибка в получении URL')
            return None

        images = []
        _total = len(_prompts)
        
        self._logger.info(f'🎨 Начинаем генерацию {_total} изображений...')
        
        for idx, prompt in enumerate(_prompts, 1):
            self._logger.info(f'  📝 {idx}/{_total}: {prompt}...')
            
            try:
                encoded_prompt = prompt.replace(' ', '%20').replace('"', '%22')
                url = f"{_url}{encoded_prompt}?width={_width}&height={_height}&nologo=true"
                
                _start = time.time()
                _response = requests.get(url, timeout=120)
                _delta = time.time() - _start
                
                if _response.status_code == 200:
                    image_base64 = base64.b64encode(_response.content).decode('utf-8')
                    images.append(image_base64)
                    self._logger.info(f'✅ Готово ({_delta:.2f} сек)')
                else:
                    self._logger.error(f'❌ Ошибка: {_response.status_code}')
                    images.append(None)
                    
            except Exception as e:
                self._logger.error(f'❌ Ошибка: {e}')
                images.append(None)
        
        # success_count = sum(1 for img in images if img is not None)
        # self._logger.info(f'✅ Генерация завершена. Успешно: {success_count}/{_total}')
        
        return images if images else None
                