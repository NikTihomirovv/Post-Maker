# managers/articles_manager.py
from dataclasses import dataclass, field
import time
import logging
from typing import Optional
import uuid

class ArticlesManager:
    """Класс для управления статьями"""

    def __init__(self, _settings):
        self._settings = _settings
        
        self._logger = logging.getLogger(__name__)
        self._article_factory = _ArticlesFactory()
        self._articles = []


    def destroy(self):
        """Освобождает ресурсы и очищает список статей"""
        try:
            # Очищаем список статей
            if self._articles:
                self._articles.clear()
                # self._logger.info('✅ Список статей очищен')
            
            # self._logger.info('✅ ArticlesManager ресурсы освобождены')
        except Exception as e:
            self._logger.error(f'❌ Ошибка при очистке ArticlesManager: {e}')


    def create_new_article(self, **kwargs) -> '_Article' | None:
        try:
            article = self._article_factory.create_from_rss_entry(**kwargs)
            
            if article:
                self._articles.append(article)
                # self._logger.info(f'✅ Статья создана в dataclass')
                return article
            
            else:
                self._logger.warning('❌ Не удалось создать статью')
                return None
                
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания статьи: {e}')
            return None
        
        
    def get_all_articles(self) -> list['_Article']:
        return self._articles



class _ArticlesFactory:
    """Фабрика для создания статьи."""

    @staticmethod
    def create_from_rss_entry(**kwargs) -> '_Article':
        """Создание Article из RSS записи feedparser."""

        _article_id = str(uuid.uuid4())
        _article_brief_data = kwargs.get('article_brief_data')
        _article_text = kwargs.get('article_text')
        _source = kwargs.get('source')
        _article_text_translated = kwargs.get('article_text_translated')
        _title_translated = kwargs.get('title_translated')
        _ai_description = kwargs.get('ai_description')
        _ai_description_translated = kwargs.get('ai_description_translated')
        _images_base64 = kwargs.get('images')

        # Создаем Images
        images = []
        if _images_base64 and isinstance(_images_base64, list):
            for image_base64 in _images_base64:
                if image_base64:
                    images.append(_Image(
                        id=str(uuid.uuid4()),
                        article_id=_article_id,
                        image_base64=image_base64
                    ))

        # Создаём TitleDetail
        title_detail = None
        if 'title_detail' in _article_brief_data:
            td = _article_brief_data['title_detail']
            title_detail = _TitleDetail(
                type=td.get('type', ''),
                language=td.get('language'),
                base=td.get('base', ''),
                value=td.get('value', '')
            )
        
        # Создаём список Link
        links = []
        for link_data in _article_brief_data.get('links', []):
            links.append(_Link(
                rel=link_data.get('rel', ''),
                type=link_data.get('type', ''),
                href=link_data.get('href', '')
            ))
        
        # Создаём SummaryDetail
        summary_detail = None
        if 'summary_detail' in _article_brief_data:
            sd = _article_brief_data['summary_detail']
            summary_detail = _SummaryDetail(
                type=sd.get('type', ''),
                language=sd.get('language'),
                base=sd.get('base', ''),
                value=sd.get('value', '')
            )

        
        # Создаём _Article_Brief_Data
        _article_brief_data_obj = _Article_Brief_Data(
            title=_article_brief_data.get('title', ''),
            link=_article_brief_data.get('link', ''),
            summary=_article_brief_data.get('summary', ''),
            published=_article_brief_data.get('published', ''),
            id=_article_brief_data.get('id', ''),
            guidislink=_article_brief_data.get('guidislink', False),
            title_detail=title_detail,
            links=links,
            summary_detail=summary_detail,
            published_parsed=_article_brief_data.get('published_parsed')
        )

        if not _article_text or '':
            _article_text = ''

        return _Article(
            article_brief_data=_article_brief_data_obj,
            id=_article_id,
            article_text=_article_text,
            title_translated = _title_translated,
            article_text_translated=_article_text_translated,
            ai_description=_ai_description,
            ai_description_translated=_ai_description_translated,
            source=_source,
            images=images
        )


@dataclass
class _TitleDetail:
    """Детали заголовка."""
    type: str = ''
    language: str | None = None
    base: str = ''
    value: str = ''


@dataclass
class _Link:
    """Ссылка."""
    rel: str = ''
    type: str = ''
    href: str = ''


@dataclass
class _SummaryDetail:
    """Детали описания."""
    type: str = ''
    language: str | None = None
    base: str = ''
    value: str = ''


@dataclass
class _Article_Brief_Data:
    """Класс для хранения данных статьи."""
    
    # Основные поля
    title: str = ''
    link: str = ''
    summary: str = ''
    published: str = ''
    id: str = ''
    guidislink: bool = False
    
    # Вложенные датаклассы
    title_detail: _TitleDetail | None = None
    links: list[_Link] = field(default_factory=list)
    summary_detail: _SummaryDetail | None = None
    published_parsed: time.struct_time | None = None


@dataclass
class _Image:
    """Класс для хранения изображения"""
    id: Optional[int] = None
    article_id: Optional[str] = None
    image_base64: str = ''


@dataclass
class _Article:
    """Класс для хранения статьи."""

    article_brief_data: _Article_Brief_Data | None = None
    id: str = ''
    title_translated: str = ''
    article_text: str = ''
    article_text_translated: str = ''
    ai_description: str = ''
    ai_description_translated: str = ''
    source: str = ''
    images: list['_Image'] = field(default_factory=list)