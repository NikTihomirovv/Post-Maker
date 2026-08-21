from dataclasses import dataclass, field
import logging
from typing import Optional
import uuid
from datetime import datetime


class PostManager:
    """Класс для управления постами"""

    def __init__(self, _settings):
        self._settings = _settings
        
        self._logger = logging.getLogger(__name__)
        self._post_factory = _PostFactory()
        self._posts = []


    def destroy(self):
        """Освобождает ресурсы"""
        try:
            if self._posts:
                self._posts.clear()
                    
        except Exception as e:
            self._logger.error(f'❌ Ошибка при очистке PostManager: {e}')


    def create_post(self, **kwargs) -> '_Post' | None:
        try:
            _post = self._post_factory.create_post(**kwargs)
                    
            if _post:
                self._posts.append(_post)
                return _post
                    
            else:
                self._logger.warning('❌ Не удалось создать пост')
                return None
                        
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания поста: {e}')
            return None
        
        
    def get_all_posts(self) -> list['_Post']:
        return self._posts


    def get_empty_dataclass(self) -> '_Post':
        return self._post_factory.create_empty()


class _PostFactory:
    """Фабрика для создания постов"""

    @staticmethod
    def create_empty() -> '_Post':
        empty_image = _Image(
            id=None,
            post_id=None,
            image_base64=''
        )
        return _Post(
            image=[empty_image]
        )

    @staticmethod
    def create_post(**kwargs) -> '_Post':

        _article_id = str(uuid.uuid4())
        _images_base64 = kwargs.get('image')
        
        images = []
        if _images_base64 and isinstance(_images_base64, list):
            for image_base64 in _images_base64:
                if image_base64:
                    images.append(_Image(
                        id = str(uuid.uuid4()),
                        post_id = _article_id,
                        image_base64 = image_base64
                    ))

        return _Post(
            id = _article_id,
            
            title = kwargs.get('title'),
            summary = kwargs.get('summary'),
            text = kwargs.get('text'),
            ai_description = kwargs.get('ai_description'),
            
            title_translated = kwargs.get('title_translated'),
            summary_translated = kwargs.get('summary_translated'),
            text_translated = kwargs.get('text_translated'),
            ai_description_translated = kwargs.get('ai_description_translated'),
            
            source = kwargs.get('source'),
            link = kwargs.get('link'),
            pub_date = kwargs.get('pub_date'),
            
            is_published_vk = kwargs.get('is_published_vk'),
            is_saved_to_folder = kwargs.get('is_saved_to_folder'),

            image = images
        )


@dataclass
class _Image:
    """Класс для хранения изображения"""

    id: str = None
    post_id: Optional[str] = None
    image_base64: str = ''


@dataclass
class _Post:
    """Класс для хранения постов."""

    id: str = ''

    title: str = ''
    summary: str = ''
    text: str = ''
    ai_description: str =''

    title_translated: str = ''
    summary_translated: str = ''
    text_translated: str = ''
    ai_description_translated: str = ''

    source: str = ''
    link: str = ''
    pub_date: str = ''

    is_published_vk: bool = ''
    is_saved_to_folder: bool = ''

    # Связанные
    image: list['_Image'] = field(default_factory=list) 

