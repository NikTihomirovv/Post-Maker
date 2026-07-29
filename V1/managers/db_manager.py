import logging
import sqlite3
import json
import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import datetime


class DBManager:
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._settings = settings
        self._db = None
        
        try:
            self._db = _DB_SQL_Lite(settings=self._settings)
        except Exception as e:
            self._logger.error(f'❌ Ошибка инициализации БД: {e}')
            self._db = None

    def create(self, _to_table: str = None, _field_to_compare: str = None, _data=None):
        """Создает запись в БД через _DB_SQL_Lite"""
        if self._db:
            return self._db.create(_to_table, _field_to_compare, _data)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return False
        
    def read(self,
            _table: str = None,
            _field: str = None,
            _value: Any = None,
            _limit: int = None
        ) -> List[Dict]:
        """Читает записи из БД"""
        if self._db:
            return self._db.read(_table, _field, _value, _limit)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return []
        
    def update_field_by_id(self, _table: str = None, _id: Any = None, _field: str = None, _value: Any = None) -> bool:
        """Обновляет поле по ID"""
        if self._db:
            return self._db.update_field_by_id(_table, _id, _field, _value)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return False

    def get_article_with_images(self, article_id: str) -> Optional[Dict]:
        """Получает статью со всеми изображениями"""
        if self._db:
            return self._db.get_article_with_images(article_id)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return None

    def destroy(self):
        if self._db:
            self._db.close()


class _DB_SQL_Lite:
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._settings = settings
        self._connection = None
        self._cursor = None
        
        self._db_path = 'articles.db'  
        
        self._connect()
        self._create_table_if_not_exists(_tables=self._settings._tables)
    
    def _connect(self) -> bool:
        try:
            # self._logger.info(f'Подключаемся к SQLite: {self._db_path}')
            
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row  
            self._cursor = self._connection.cursor()
            
            # self._logger.info(f'✅ Подключение к SQLite: {self._db_path}')
            return True
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка подключения к SQLite: {e}')
            return False
        

    def _create_table_if_not_exists(self, _tables: dict) -> bool:
        """Создает все необходимые таблицы в базе данных"""
        try:
            if not isinstance(_tables, dict) or not _tables:
                self._logger.error(f'❌ Ошибка: _tables должен быть непустым словарем')
                return False

            for _table_name, _fields in _tables.items():
                # Проверяем, существует ли таблица
                self._cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (_table_name,)
                )
                table_exists = self._cursor.fetchone() is not None
                
                if table_exists:
                    # self._logger.info(f'✅ Таблица {_table_name} уже существует, проверяем структуру...')
                    
                    # Получаем существующие колонки
                    existing_columns = self._get_table_columns(_table_name)
                    existing_names = [col['name'] for col in existing_columns]
                    
                    # Добавляем недостающие колонки
                    for field in _fields:
                        col_name = field.split()[0]
                        if col_name not in existing_names:
                            col_type = ' '.join(field.split()[1:])
                            self._cursor.execute(f'ALTER TABLE {_table_name} ADD COLUMN {col_name} {col_type}')
                            # self._logger.info(f'  ➕ Добавлена колонка {col_name}')
                    self._connection.commit()
                else:
                    # Создаем новую таблицу
                    _query = ', '.join(_field for _field in _fields)
                    self._cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS {_table_name} (
                            {_query}
                        )
                    ''')
                    self._connection.commit()
                    # self._logger.info(f'✅ Таблица {_table_name} создана')

            # self._logger.info('✅ Все таблицы созданы/обновлены')
            return True
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания таблиц: {e}')
            if self._connection:
                self._connection.rollback()
            return False

    
    def _get_table_columns(self, _table_name: str) -> List[Dict[str, Any]]:
        """Получает информацию о колонках существующей таблицы"""
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return []
            
            self._cursor.execute(f"PRAGMA table_info({_table_name})")
            
            columns = []
            for row in self._cursor.fetchall():
                columns.append({
                    'cid': row['cid'],
                    'name': row['name'],
                    'type': row['type'],
                    'notnull': bool(row['notnull']),
                    'dflt_value': row['dflt_value'],
                    'pk': bool(row['pk'])
                })
            
            # self._logger.info(f"✅ Получена информация о {len(columns)} колонках таблицы {_table_name}")
            return columns
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка получения информации о таблице {_table_name}: {e}')
            return []


    def create(self, 
            _to_table: str = None,
            _field_to_compare: str = None,
            _data=None
        ) -> bool:
        """Создает новую запись в выбранной таблице из датакласса"""

        # Используем значения из настроек, если не переданы
        if _to_table is None:
            _to_table = self._settings.save_data_to_table
        if _field_to_compare is None:
            _field_to_compare = self._settings.field_to_compare

        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return False
            
            if not _field_to_compare:
                self._logger.error('❌ Не найден параметр для сравнения')
                return False
            
            if not _data:
                self._logger.error('❌ Не найден объект для сохранения')
                return False

            # Получаем значение поля для сравнения
            _field_to_compare_in_data = _HelpfullMethods._get_dataclass_field(_data, _field_to_compare)
            
            # Проверяем существование записи
            if _field_to_compare and _field_to_compare_in_data is not None:
                self._cursor.execute(
                    f"SELECT id FROM {_to_table} WHERE {_field_to_compare} = ?",
                    (_field_to_compare_in_data,)
                )
                existing = self._cursor.fetchone()
                if existing:
                    # self._logger.info(f'ℹ️ Запись уже существует: {_field_to_compare}={_field_to_compare_in_data}')
                    return False
            
            # Преобразуем датакласс в словарь с правильными именами полей
            _dataclass_dicted = _HelpfullMethods._article_to_db_dict(_data)
            
            if not _dataclass_dicted:
                self._logger.error('❌ Не удалось преобразовать датакласс в словарь')
                return False
            
            # self._logger.debug(f"📊 Поля из датакласса: {list(_dataclass_dicted.keys())}")
            
            # Получаем структуру таблицы
            table_columns = self._get_table_columns(_to_table)
            if not table_columns:
                self._logger.error(f'❌ Не удалось получить структуру таблицы {_to_table}')
                return False
            
            column_names = [col['name'] for col in table_columns]
            
            # Фильтруем поля: оставляем только те, что есть в таблице
            filtered_fields = {}
            for field_name, field_value in _dataclass_dicted.items():
                if field_name in column_names:
                    # Преобразуем UUID в строку
                    if isinstance(field_value, uuid.UUID):
                        field_value = str(field_value)
                    
                    # Преобразуем булевы значения
                    if isinstance(field_value, bool):
                        field_value = 1 if field_value else 0
                    
                    filtered_fields[field_name] = field_value
                # else:
                #     self._logger.debug(f"ℹ️ Поле {field_name} не найдено в таблице {_to_table}, пропускаем")
            
            if not filtered_fields:
                self._logger.error('❌ Нет полей для вставки')
                return False
            
            # Формируем SQL запрос
            columns = ', '.join(filtered_fields.keys())
            placeholders = ', '.join(['?' for _ in filtered_fields])
            values = list(filtered_fields.values())
            
            query = f"INSERT INTO {_to_table} ({columns}) VALUES ({placeholders})"
            
            # self._logger.info(f"📝 Создаем запись в таблице {_to_table}")
            # self._logger.debug(f"📊 Поля для вставки: {list(filtered_fields.keys())}")
            
            self._cursor.execute(query, values)
            self._connection.commit()
            
            record_id = self._cursor.lastrowid
            # self._logger.info(f"✅ Запись создана (ID: {record_id})")
            
            # === Сохраняем изображения ===
            if hasattr(_data, 'images') and _data.images:
                images_list = _HelpfullMethods._images_to_db_list(_data)
                if images_list:
                    self._save_images(images_list, _data.id)
            
            return True
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания записи: {e}')
            if self._connection:
                self._connection.rollback()
            return False

    def _save_images(self, images_list: list[dict], article_id: str) -> bool:
        """
        Сохраняет изображения в таблицу images
        """
        try:
            if not images_list:
                return True
            
            # Удаляем старые изображения для этой статьи (если они были)
            self._cursor.execute(
                "DELETE FROM images WHERE article_id = ?",
                (article_id,)
            )
            
            # Вставляем новые изображения
            for img_dict in images_list:
                # Убираем поле 'id' из вставки (автоинкремент)
                insert_dict = {k: v for k, v in img_dict.items() if k != 'id'}
                
                columns = ', '.join(insert_dict.keys())
                placeholders = ', '.join(['?' for _ in insert_dict])
                values = list(insert_dict.values())
                
                query = f"INSERT INTO images ({columns}) VALUES ({placeholders})"
                self._cursor.execute(query, values)
            
            self._connection.commit()
            # self._logger.info(f'✅ Сохранено {len(images_list)} изображений для статьи {article_id}')
            return True
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка сохранения изображений: {e}')
            if self._connection:
                self._connection.rollback()
            return False
        
    def read(self, _table: str = None, _field: str = None, _value: Any = None, _limit: int = None) -> List[Dict]:
        """
        Читает записи из таблицы с фильтром по полю
        
        Args:
            _table: имя таблицы
            _field: поле для фильтрации
            _value: значение для фильтрации
            _limit: максимальное количество записей
        
        Returns:
            List[Dict]: список записей
        """
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return []
            
            # Используем таблицу из настроек или переданную
            if _table is None:
                _table = self._settings.read_from_table
            
            # Формируем запрос
            if _field and _value is not None:
                query = f"SELECT * FROM {_table} WHERE {_field} = ?"
                params = (_value,)
            else:
                query = f"SELECT * FROM {_table}"
                params = ()
            
            # Добавляем лимит
            if _limit:
                query += f" LIMIT {_limit}"
            
            # self._logger.debug(f"📝 Выполняем запрос: {query}")
            
            self._cursor.execute(query, params)
            
            results = []
            for row in self._cursor.fetchall():
                results.append(dict(row))
            
            # self._logger.info(f"✅ Получено {len(results)} записей из таблицы {_table}")
            return results
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка чтения из таблицы {_table}: {e}')
            return []
        
    def get_article_with_images(self, article_id: str) -> Optional[Dict]:
        """
        Получает статью со всеми её изображениями
        
        Args:
            article_id: ID статьи
        
        Returns:
            Optional[Dict]: словарь с данными статьи и списком изображений
        """
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return None
            
            # 1. Получаем статью
            self._cursor.execute(
                "SELECT * FROM articles WHERE id = ?",
                (article_id,)
            )
            article_row = self._cursor.fetchone()
            
            if not article_row:
                self._logger.warning(f'⚠️ Статья с ID {article_id} не найдена')
                return None
            
            article = dict(article_row)
            
            # 2. Получаем изображения
            self._cursor.execute(
                "SELECT * FROM images WHERE article_id = ? ORDER BY created_at",
                (article_id,)
            )
            images = [dict(row) for row in self._cursor.fetchall()]
            
            article['images'] = images
            # self._logger.info(f'✅ Получена статья {article_id} с {len(images)} изображениями')
            
            return article
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка получения статьи с изображениями: {e}')
            return None

    def get_all_articles_with_images(self, limit: int = 100) -> List[Dict]:
        """
        Получает все статьи с их изображениями
        
        Args:
            limit: максимальное количество статей
        
        Returns:
            List[Dict]: список статей с изображениями
        """
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return []
            
            # 1. Получаем все статьи
            self._cursor.execute(
                "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            articles = [dict(row) for row in self._cursor.fetchall()]
            
            # 2. Для каждой статьи получаем изображения
            for article in articles:
                self._cursor.execute(
                    "SELECT * FROM images WHERE article_id = ? ORDER BY created_at",
                    (article['id'],)
                )
                images = [dict(row) for row in self._cursor.fetchall()]
                article['images'] = images
            
            # self._logger.info(f'✅ Получено {len(articles)} статей с изображениями')
            return articles
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка получения статей с изображениями: {e}')
            return []

    def update_field_by_id(self, 
                        _table: str = None,
                        _id: Any = None,
                        _field: str = None,
                        _value: Any = None
                    ) -> bool:
        """
        Обновляет значение поля по ID записи
        
        Args:
            _table: имя таблицы
            _id: ID записи
            _field: поле для обновления
            _value: новое значение
        
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return False
            
            if _table is None:
                _table = self._settings.save_data_to_table
            
            if not _field:
                self._logger.error('❌ Не указано поле для обновления')
                return False
            
            if _id is None:
                self._logger.error('❌ Не указан ID записи')
                return False
            
            # Преобразуем булевы значения
            if isinstance(_value, bool):
                _value = 1 if _value else 0
            
            # Выполняем запрос
            query = f"UPDATE {_table} SET {_field} = ? WHERE id = ?"
            values = [_value, _id]
            
            # self._logger.info(f"📝 Обновляем поле {_field} в таблице {_table} (ID: {_id})")
            # self._logger.debug(f"📊 Запрос: {query}")
            # self._logger.debug(f"📊 Значения: {values}")
            
            self._cursor.execute(query, values)
            self._connection.commit()
            
            affected_rows = self._cursor.rowcount
            if affected_rows > 0:
                # self._logger.info(f"✅ Поле {_field} обновлено (ID: {_id})")
                pass
            else:
                self._logger.warning(f"⚠️ Запись с ID {_id} не найдена")
            
            return affected_rows > 0
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка обновления поля {_field} (ID: {_id}): {e}')
            if self._connection:
                self._connection.rollback()
            return False
        

    def close(self):
        """Закрывает соединение с БД"""
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
            # self._logger.info('✅ Соединение с SQLite закрыто')
        except Exception as e:
            self._logger.error(f'❌ Ошибка при закрытии: {e}')



class _HelpfullMethods:

    @staticmethod
    def _get_dataclass_field(obj, field_name: str, default=None):
        """Получает значение поля из датакласса рекурсивно"""
        if obj is None:
            return default
        
        if hasattr(obj, field_name):
            return getattr(obj, field_name)
        
        if isinstance(obj, dict) and field_name in obj:
            return obj[field_name]
        
        if isinstance(obj, list):
            for item in obj:
                result = _HelpfullMethods._get_dataclass_field(item, field_name, default)
                if result is not default:
                    return result
            return default
        
        if hasattr(obj, '__dataclass_fields__') or hasattr(obj, '__dict__'):
            for attr_name in dir(obj):
                if attr_name.startswith('_'):
                    continue
                try:
                    value = getattr(obj, attr_name)
                    if value is not None and not callable(value):
                        if hasattr(value, '__dict__') or hasattr(value, '__dataclass_fields__') or isinstance(value, (dict, list)):
                            result = _HelpfullMethods._get_dataclass_field(value, field_name, default)
                            if result is not default:
                                return result
                except Exception:
                    continue
        
        return default
    

    @staticmethod
    def _article_to_db_dict(article) -> dict:
        """
        Преобразует _Article в словарь с именами полей для БД
        """
        result = {}
        
        if article is None:
            return result
        
        # Основные поля _Article
        result['id'] = str(article.id) if hasattr(article, 'id') and article.id else None
        result['source'] = getattr(article, 'source', '')
        result['article_text'] = getattr(article, 'article_text', '')
        result['title_translated'] = getattr(article, 'title_translated', '') 
        result['article_text_translated'] = getattr(article, 'article_text_translated', '')
        result['ai_description'] = getattr(article, 'ai_description', '')
        result['ai_description_translated'] = getattr(article, 'ai_description_translated', '')
        
        # Получаем article_brief_data
        brief = getattr(article, 'article_brief_data', None)
        
        if brief:
            # Поля из _Article_Brief_Data с правильными именами
            result['title'] = getattr(brief, 'title', '')
            result['link'] = getattr(brief, 'link', '')
            result['summary'] = getattr(brief, 'summary', '')
            result['published'] = getattr(brief, 'published', '')
            result['feed_id'] = getattr(brief, 'id', '')  # переименовываем id в feed_id
            result['guidislink'] = 1 if getattr(brief, 'guidislink', False) else 0
            
            # Поля из _TitleDetail
            title_detail = getattr(brief, 'title_detail', None)
            if title_detail:
                result['title_detail_type'] = getattr(title_detail, 'type', '')
                result['title_detail_language'] = getattr(title_detail, 'language', None)
                result['title_detail_base'] = getattr(title_detail, 'base', '')
                result['title_detail_value'] = getattr(title_detail, 'value', '')
            
            # Поля из _SummaryDetail
            summary_detail = getattr(brief, 'summary_detail', None)
            if summary_detail:
                result['summary_detail_type'] = getattr(summary_detail, 'type', '')
                result['summary_detail_language'] = getattr(summary_detail, 'language', None)
                result['summary_detail_base'] = getattr(summary_detail, 'base', '')
                result['summary_detail_value'] = getattr(summary_detail, 'value', '')
            
            # Список ссылок в JSON
            links = getattr(brief, 'links', [])
            if links:
                links_data = []
                for link in links:
                    if hasattr(link, '__dataclass_fields__'):
                        links_data.append({
                            'rel': getattr(link, 'rel', ''),
                            'type': getattr(link, 'type', ''),
                            'href': getattr(link, 'href', '')
                        })
                    elif isinstance(link, dict):
                        links_data.append(link)
                result['links_json'] = json.dumps(links_data, ensure_ascii=False)
            
            # published_parsed в отдельные поля
            published_parsed = getattr(brief, 'published_parsed', None)
            if published_parsed and isinstance(published_parsed, time.struct_time):
                result['published_parsed_year'] = published_parsed.tm_year
                result['published_parsed_month'] = published_parsed.tm_mon
                result['published_parsed_day'] = published_parsed.tm_mday
                result['published_parsed_hour'] = published_parsed.tm_hour
                result['published_parsed_minute'] = published_parsed.tm_min
                result['published_parsed_second'] = published_parsed.tm_sec
                result['published_parsed_weekday'] = published_parsed.tm_wday
                result['published_parsed_yday'] = published_parsed.tm_yday
                result['published_parsed_isdst'] = published_parsed.tm_isdst
        
        return result

    @staticmethod
    def _images_to_db_list(article) -> list[dict]:
        """
        Преобразует изображения из _Article в список словарей для таблицы images
        """
        if article is None:
            return []
        
        images = getattr(article, 'images', [])
        if not images or not isinstance(images, list):
            return []
        
        result = []
        for img in images:
            if img:
                img_dict = {
                    'article_id': getattr(article, 'id', None),
                    'image_base64': getattr(img, 'image_base64', ''),
                }
                result.append(img_dict)
        
        return result