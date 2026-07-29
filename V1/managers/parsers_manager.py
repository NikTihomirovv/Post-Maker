import feedparser
import requests
from bs4 import BeautifulSoup
import logging
import time


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
            # Получаем количество парсеров
            parsers_count = len(self._parsers)
            
            if parsers_count > 0:
                # self._logger.info(f'📊 Очищаем {parsers_count} парсеров из памяти')
                
                # Очищаем список парсеров
                self._parsers.clear()
                # self._logger.info(f'✅ {parsers_count} парсеров удалено из памяти')

            
            # self._logger.info('✅ ParsersManager ресурсы освобождены')
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка при очистке ParsersManager: {e}')


    def parse_all(self):
        """Парсит все источники и возвращает список всех статей"""
        if self._settings.logic.get('parse', False) == False:
            # self._logger.info('✅ Парсинг выключен')
            return []

        if not isinstance(self._settings.sources, list) or len(self._settings.sources) == 0:
            self._logger.error(f'❌ Ошибка в получении списка источников.')
            return []

        results = []
        
        for _source in self._settings.sources:
            if _source.get('enable'):
                _source_name = _source.get('source_name')
                _parser_type = _source.get('parser_type')
                # self._logger.info(f'✅ Создаем парсер для источника: {_source_name}, тип парсера {_parser_type}')

                match _parser_type:
                    case 'rss':
                        _parser = self._parser_factory.create_rss_parser(
                            _source=_source
                        )
                    case 'html':
                        _parser = self._parser_factory.create_html_parser(
                            _source=_source
                        )
                    case _:
                        self._logger.error(f'❌ Неверный тип парсера: {_parser_type}')
                        continue

                # Получаем результат парсинга (теперь это список)
                source_results = _parser.parse()
                
                if source_results and isinstance(source_results, list):
                    # self._logger.info(f'✅ Получено {len(source_results)} статей из {_source_name}')
                    results.extend(source_results)
                elif source_results:
                    self._logger.warning(f'⚠️ Неожиданный формат результата от {_source_name}')

        # self._logger.info(f'✅ Всего получено статей: {len(results)}')
        return results


class _ParsersFactory():
    """Фабрика для создания парсеров"""

    @staticmethod
    def create_rss_parser(**kwargs):
        return _RssParser(**kwargs)
    

    @staticmethod
    def create_html_parser(**kwargs):
        pass


class _RssParser:
    """Парсер для rss статей."""

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._source = kwargs.get('_source')

        self._source_name = self._source.get('source_name')
        self._url = self._source.get('url')
        self._headers = self._source.get('headers')
        self._date = self._source.get('date')
        self._number_of_articles = self._source.get('number_of_articles')


    def _transform_date(self, _date: dict[str]) -> dict[str]:
        """Преобразует даты из строк в struct_time"""
        _date_to = _date.get('date_to')
        _date_from = _date.get('date_from')
        _date_from_transformed = None
        _date_to_transformed = None

        # Проверка даты
        if _date_from:
            try:
                _date_from_transformed = time.strptime(_date_from, '%d.%m.%y')
                # self._logger.info(f'✅ Фильтр С: {_date_from}')
            except ValueError:
                self._logger.warning(f'❌ Неверный формат date_from: {_date_from}')
                
        if _date_to:
            try:
                _date_to_transformed = time.strptime(_date_to, '%d.%m.%y')
                # self._logger.info(f'✅ Фильтр по: {_date_to}')
            except ValueError:
                self._logger.warning(f'❌ Неверный формат date_to: {_date_to}')

        return {
            'date_from': _date_from_transformed,
            'date_to': _date_to_transformed, 
        }
        

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
            
            if not isinstance(self._date, dict) or self._date == {}:
                self._logger.error(f'❌ Неверно передана дата {self._date}')
                return []

            self._logger.info(f'✅ Начинаем парсинг источника: {self._source_name}, url {self._url}')
            
            # Преобразуем даты
            self._date = self._transform_date(_date=self._date)
            date_from = self._date.get('date_from')
            date_to = self._date.get('date_to')

            # Парсим RSS
            _feed = feedparser.parse(self._url)
            if not _feed.entries:
                # self._logger.info('ℹ️ Новостей нет')
                return []

            # Фильтруем по дате
            filtered_articles = [
                entry for entry in _feed.entries
                if 'published_parsed' in entry
                and (date_from is None or entry.published_parsed >= date_from)
                and (date_to is None or entry.published_parsed <= date_to)
            ]
            
            # Сортируем по дате (свежие сверху)
            filtered_articles.sort(
                key=lambda x: x.get('published_parsed', 0),
                reverse=True
            )

            # self._logger.info(f'✅ Всего статей: {len(_feed.entries)}, в нужном диапазоне дат: {len(filtered_articles)}')

            # Ограничиваем количество
            articles_to_process = filtered_articles[:self._number_of_articles]
            
            if not articles_to_process:
                # self._logger.info('ℹ️ Нет статей для обработки')
                return []

            # Собираем все статьи
            results = []
            _count = 0
            
            for _article_brief_data in articles_to_process:
                _count += 1
                # self._logger.info(f'📄 Обработка статьи {_count}/{len(articles_to_process)}: {_article_brief_data.title[:80]}...')

                # Парсим полный текст статьи
                _article_text = self._parse_article_text(_article_brief_data.link)

                if _article_text:
                    results.append({
                        'article_brief_data': _article_brief_data,
                        'article_text': _article_text,
                        'source': self._source_name,
                    })
                    # self._logger.info(f'   ✅ Статья {_count} добавлена')
                else:
                    self._logger.warning(f'   ⚠️ Не удалось получить текст статьи {_count}')
            
            # self._logger.info(f'✅ Обработано статей: {_count}, успешно: {len(results)}')
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

            # Загружаем страницу
            _response = requests.get(_article_text_link, headers=self._headers, timeout=30)
            _response.raise_for_status()
            
            # Парсим HTML
            _soup = BeautifulSoup(_response.text, 'html.parser')
            
            # Ищем контент статьи (для ScienceDaily)
            _article_body = _soup.find('div', id='text')
            
            # Если не нашли по id, пробуем другие селекторы
            if not _article_body:
                _article_body = _soup.find('article')
            
            if not _article_body:
                _article_body = _soup.find('div', class_='article-content')

            if _article_body:
                # Получаем текст и очищаем от лишних пробелов
                _article_text = _article_body.get_text(strip=True)
                
                # Проверяем, что текст не пустой и достаточно длинный
                if len(_article_text) > 100:
                    # self._logger.info(f'✅ Найден текст статьи: {len(_article_text)} символов')
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