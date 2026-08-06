import feedparser
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime


class ParsersManager: 
    """Класс для работы с парсерами"""

    def __init__(
        self,
        settings,
    ):
        self._settings = settings
        self._logger = logging.getLogger(__name__)
        self._parser_factory = _ParsersFactory()
        self._parsers = []


    def destroy(self):
        """Освобождает ресурсы и очищает список парсеров"""
        try:
            parsers_count = len(self._parsers)
            
            if parsers_count > 0:
                self._parsers.clear()
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка при очистке ParsersManager: {e}')


    def parse_all(self):
        """Парсит все источники и возвращает список всех статей"""

        if not isinstance(self._settings.sources, list) or len(self._settings.sources) == 0:
            self._logger.error(f'❌ Ошибка в получении списка источников.')
            return []

        results = []
        
        for _source in self._settings.sources:
            if _source.get('enable'):

                _source_name = _source.get('source_name')
                _parser_type = _source.get('parser_type')

                match _parser_type:
                    case 'rss':
                        _parser = self._parser_factory.create_rss_parser(
                            _source=_source
                        )

                    case _:
                        self._logger.error(f'❌ Неверный тип парсера: {_parser_type}')
                        continue

                source_results = _parser.parse()
                
                if source_results and isinstance(source_results, list):
                    results.extend(source_results)

                elif source_results:
                    self._logger.warning(f'❌ Неожиданный формат результата от {_source_name}')
                    continue

        return results


class _ParsersFactory():
    """Фабрика для создания парсеров"""

    @staticmethod
    def create_rss_parser(**kwargs):
        return _RssParser(**kwargs)
    

class _RssParser:
    """Парсер для rss статей."""

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._source = kwargs.get('_source')

        self._source_name = self._source.get('source_name')
        self._url = self._source.get('url')
        self._headers = self._source.get('headers')
        self._dates = self._source.get('dates')
        self._number_of_articles = self._source.get('number_of_articles')
        self._mapping_structure = self._source.get('_mapping_structure')


    def _transform_date(self, _dates: dict[str]) -> dict[str]:
        """Преобразует даты из строк в datetime."""

        _date_to = _dates.get('date_to')
        _date_from = _dates.get('date_from')
        _date_from_transformed = None
        _date_to_transformed = None

        if _date_from:
            try:
                _date_from_transformed = datetime.strptime(_date_from, '%d.%m.%y')
            except ValueError:
                self._logger.warning(f'❌ Неверный формат date_from: {_date_from}')
                
        if _date_to:
            try:
                _date_to_transformed = datetime.strptime(_date_to, '%d.%m.%y')
            except ValueError:
                self._logger.warning(f'❌ Неверный формат date_to: {_date_to}')

        return {
            'date_from': _date_from_transformed,
            'date_to': _date_to_transformed, 
        }


    def _find_value_in_feed_recursively(self, _feed_entry, _element_to_find):

        if not isinstance(_element_to_find, str) or _element_to_find == '':
            self._logger.error(f'❌ Ошибка: _element_name должен быть непустой строкой, получен {_element_to_find}')
            return None
        
        if isinstance(_feed_entry, dict):
            if _element_to_find in _feed_entry:
                value = _feed_entry[_element_to_find]
                if isinstance(value, str) and value:
                    return value
                
                elif value is not None:
                    return value
            
            for key, value in _feed_entry.items():
                if isinstance(value, (dict, list)):
                    result = self._find_value_in_feed_recursively(value, _element_to_find)
                    if result is not None:
                        return result

        
        elif isinstance(_feed_entry, list):
            for item in _feed_entry:
                if isinstance(item, (dict, list)):
                    result = self._find_value_in_feed_recursively(item, _element_to_find)
                    if result is not None:
                        return result
        
        return None


    def _transform_rss_date(self, date_str: str) -> datetime | None:
        """Преобразует RSS дату в datetime."""

        if not date_str:
            return None
        try:
            parts = date_str.split()
            date_str_clean = ' '.join(parts[:5])
            return datetime.strptime(date_str_clean, '%a, %d %b %Y %H:%M:%S')
        except (ValueError, IndexError):
            return None


    def _apply_mapping(self, _feed_entry):

        if self._mapping_structure: 
            _mapping_structure = self._mapping_structure

        else: 
            _mapping_structure = (
                ('title','title'),
                ('summary', 'summary'),
                ('link', 'link'),
                ('published', 'pub_date'),
            )

        # Валидация
        if not isinstance(_mapping_structure, tuple) or len(_mapping_structure) == 0:
            self._logger.error(f'❌ Ошибка в получении структуры маппинга {_mapping_structure}')
            return None

        for _item in _mapping_structure:
            if not isinstance(_item, tuple) or len(_item) < 2:
                self._logger.error(f'❌ Ошибка в получении структуры маппинга {_mapping_structure}')
                return None

        # Маппинг
        structure = {}
        for _element in _mapping_structure:
            _element_to_find = _element[0]
            _element_to_create = _element[1]
            _value = self._find_value_in_feed_recursively(_feed_entry, _element_to_find)

            if _element_to_create == 'pub_date':
                _value = self._transform_rss_date(_value)

            if _value:
                structure[_element_to_create] = _value

        return structure


    def parse(self) -> list:
        """
        Парсит RSS ленту и возвращает список всех статей в заданном диапазоне дат
        
        Returns:
            list: список словарей с данными статей
        """
        try:
            # Валидация
            if not isinstance(self._number_of_articles, int) or self._number_of_articles <= 0:
                self._logger.error(f'❌ Параметры не переданны или неверны: _number_of_articles = {self._number_of_articles}')
                return []

            if not self._url:
                self._logger.error(f'❌ URL для {self._source_name} не найден')
                return []
            
            if not isinstance(self._dates, dict) or self._dates == {}:
                self._logger.error(f'❌ Неверно передана дата {self._dates}')
                return []

            self._logger.info(f'✅ Начинаем парсинг источника: {self._source_name}, url {self._url}')
            
            # Преобразуем даты
            self._dates = self._transform_date(self._dates)
            date_from = self._dates.get('date_from')
            date_to = self._dates.get('date_to')

            # Парсим RSS
            _feed = feedparser.parse(self._url)

            if not _feed.entries:
                self._logger.info('ℹ️ Новостей нет')
                return []

            _cleaned_articles = []
            for entry in _feed.entries:
                _cleaned_data = self._apply_mapping(entry)
                if _cleaned_data:
                    _cleaned_articles.append(_cleaned_data)

            # Фильтруем по дате
            _filtered_articles = [
                article for article in _cleaned_articles
                if 'pub_date' in article
                and (date_from is None or article.get('pub_date') >= date_from)
                and (date_to is None or article.get('pub_date') <= date_to)
            ]
            
            # Сортируем по дате (свежие сверху)
            _filtered_articles.sort(
                key=lambda x: x.get('pub_date', 0),
                reverse=True
            )

            for article in _filtered_articles:
                if 'pub_date' in article and isinstance(article['pub_date'], datetime):
                    article['pub_date'] = article['pub_date'].strftime('%Y-%m-%d %H:%M:%S')

            # Ограничиваем количество
            articles_to_process = _filtered_articles[:self._number_of_articles]
            
            if not articles_to_process:
                return []

            results = []
            for _article in articles_to_process:

                _article['source'] = self._source_name
            
                _article_text = self._parse_article_text(_article.get('link'))
                if _article_text:
                    _article['text'] = _article_text
                    results.append(_article)

                else:
                    self._logger.error(f'❌Не удалось получить текст статьи ')

            return results

        except Exception as e:
            self._logger.error(f'❌ Ошибка парсинга {self._source_name}: {e}')
            return []
        

    def _parse_article_text(self, _article_text_link: str = '') -> str | None:
        """Парсит полный текст статьи по ссылке"""

        try: 
            self._logger.debug(f'🔍 Начинаем парсинг текста по ссылке: {_article_text_link}')

            # Валидация
            if not _article_text_link or _article_text_link == '':
                self._logger.error(f'❌ Не найдена ссылка на текст')
                return None
            
            if not isinstance(self._headers, dict):
                self._logger.error(f'❌ Ошибка в получении headers')
                return None

            _response = requests.get(_article_text_link, headers=self._headers, timeout=30)
            _response.raise_for_status()
            
            _soup = BeautifulSoup(_response.text, 'html.parser')
            _article_body = _soup.find('div', id='text')
            
            if not _article_body:
                _article_body = _soup.find('article')
            
            if not _article_body:
                _article_body = _soup.find('div', class_='article-content')

            if _article_body:
                _article_text = _article_body.get_text(strip=True)

                if len(_article_text) > 100:
                    return _article_text
                else:
                    self._logger.warning(f'⚠️ Найден слишком короткий текст ({len(_article_text)} символов)')
                    return None
            
            else:
                self._logger.error(f'❌ Не найден контейнер с текстом статьи')
                return None 
                
        except requests.exceptions.Timeout:
            self._logger.error(f'❌ Таймаут при загрузке страницы: {_article_text_link}')
            return None
        except requests.exceptions.RequestException as e:
            self._logger.error(f'❌ Ошибка загрузки страницы: {e}')
            return None
        except Exception as e:
            self._logger.error(f'❌ Ошибка парсинга текста: {e}')
            return None