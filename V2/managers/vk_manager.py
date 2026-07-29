# managers/vk_manager.py
import logging
import requests
import base64
from typing import Optional, Dict, Any, List


class VKManager:
    """Класс для взаимодействия с API VK"""

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._settings = settings
        
        self._access_token = self._settings.vk.get('access_token', '')
        self._group_id = self._settings.vk.get('group_id', '')
        self._api_version = self._settings.vk.get('api_version', '5.131')
        self._api_url = 'https://api.vk.com/method/'
        
        if not self._access_token:
            self._logger.warning('⚠️ VK access token не найден')

    def destroy(self):
        # self._logger.info('✅ VKManager ресурсы освобождены')
        pass


    def create_post(self, 
                    message: str,
                    attachments: List[str] = None,
                    publish_date: int = None,
                    from_group: int = 1,
                ) -> Optional[Dict[str, Any]]:
        """
        Создает пост на стене группы
        """
        try:
            if not self._access_token:
                self._logger.error('❌ Отсутствует access_token')
                return None
            
            if not self._group_id:
                self._logger.error('❌ Отсутствует group_id')
                return None
            
            if not message:
                self._logger.error('❌ Текст поста не может быть пустым')
                return None
            
            params = {
                'owner_id': -int(self._group_id),
                'message': message,
                'from_group': from_group,
                'access_token': self._access_token,
                'v': self._api_version
            }
            
            if attachments:
                # Проверяем формат attachments
                valid_attachments = []
                for att in attachments:
                    if isinstance(att, str) and att.startswith('photo'):
                        valid_attachments.append(att)
                    else:
                        self._logger.warning(f'⚠️ Неверный формат attachment: {att[:50] if att else "None"}')
                
                if valid_attachments:
                    params['attachments'] = ','.join(valid_attachments)
                    self._logger.info(f'🖼️ Добавлено {len(valid_attachments)} изображений')
            
            if publish_date:
                params['publish_date'] = publish_date
            
            # self._logger.debug(f"📤 Отправляем запрос в VK API")
            # self._logger.debug(f"📊 owner_id: {params['owner_id']}")
            
            response = requests.post(
                f'{self._api_url}wall.post',
                data=params,
                timeout=30
            )
            
            if not response.text:
                self._logger.error('❌ Пустой ответ от VK API')
                return None
            
            try:
                data = response.json()
            except ValueError as e:
                self._logger.error(f'❌ Ошибка парсинга JSON: {e}')
                self._logger.error(f'📄 Ответ: {response.text[:200]}')
                return None
            
            if 'error' in data:
                error_code = data['error'].get('error_code')
                error_msg = data['error'].get('error_msg')
                self._logger.error(f'❌ Ошибка VK API: {error_code} - {error_msg}')
                return None
            
            if 'response' in data:
                post_id = data['response'].get('post_id')
                # self._logger.info(f'✅ Пост создан в VK (post_id: {post_id})')
                return data['response']
            else:
                self._logger.error('❌ Неизвестный ответ от VK API')
                return None
                
        except requests.exceptions.Timeout:
            self._logger.error('❌ Таймаут при подключении к VK API')
            return None
        except requests.exceptions.ConnectionError:
            self._logger.error('❌ Ошибка подключения к VK API')
            return None
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания поста: {e}')
            return None
