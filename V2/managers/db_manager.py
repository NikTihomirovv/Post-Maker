import logging
import sqlite3
import json
import uuid
import time
from typing import Optional, Any
from dataclasses import fields, is_dataclass, MISSING
import re
from pprint import pprint
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


    def destroy(self):
        if self._db:
            self._db.close()


    def dataclass_to_sql_structure(self, _dataclass):
        if self._db:
            self._db._dataclass_to_sql_structure(_dataclass, _mode='create_table')
        else:
            self._logger.error('❌ Нет подключения к БД')
        return None

    def create_tables_if_not_exists(self):
        if self._db:
            self._db._create_table_if_not_exists()
        else:
            self._logger.error('❌ Нет подключения к БД')
        return None

    def create_from_dataclass(self, _to_table: str = None, _field_to_compare: str = None, _data=None):
        if self._db:
            return self._db._create_from_dataclass(_to_table, _field_to_compare, _data)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return False

    def read(self, _table: str = None, _field: str = None, _value: Any = None, _limit: int = None) -> list[dict]:
        if self._db:
            return self._db.read(_table, _field, _value, _limit)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return []

    def update_field_by_id(self, _table: str = None, _id: Any = None, _field: str = None, _value: Any = None) -> bool:
        if self._db:
            return self._db.update_field_by_id(_table, _id, _field, _value)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return False

    def get_article_with_images(self, article_id: str) -> Optional[dict]:
        if self._db:
            return self._db.get_article_with_images(article_id)
        else:
            self._logger.error('❌ Нет подключения к БД')
            return None


class DataclassToSql:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._sql_structures = []

    def _dataclass_to_sql_structure(self, _dataclass, _mode) -> list:
        try:
            if not is_dataclass(_dataclass):
                self._logger.error('❌ Ошибка в получении датакласса')
                return None
    
            _dataclass_structure = self._dataclass_to_dict(_dataclass, _mode)
            _sql_structure = self._transform_to_sql_structure(_dataclass_structure)

            if _sql_structure:
                self._sql_structures.append(_sql_structure) 
            
            if self._sql_structures:     
                return self._sql_structures

            return None
    
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания таблиц из датакласса: {e}')
            return None

    def _dataclass_to_dict(self, _dataclass_instance, _mode) -> list:
        """
        Рекурсивно преобразует датакласс в список кортежей [(table_name, [fields]), ...]
        """
        if not is_dataclass(_dataclass_instance):
            self._logger.error('❌ Ошибка в получении датакласса')
            return None

        result = []
        current_fields = []

        for _dataclass_field in fields(_dataclass_instance):
            _field_name = _dataclass_field.name
            _field_value = getattr(_dataclass_instance, _field_name)
            
            _field_info = {
                'type': self._clean_field_type(str(_dataclass_field.type)),
                'value': _field_value,
            }

            # Обработка списков (вложенные датаклассы)
            if _field_info.get('type') == 'list' and isinstance(_field_value, list):
                if _mode == 'create_table':
                    # Для создания таблицы - берем структуру первого элемента
                    if len(_field_value) > 0 and is_dataclass(_field_value[0]):
                        nested_result = self._dataclass_to_dict(_field_value[0], _mode)
                        if nested_result:
                            result.extend(nested_result)
                else:
                    # Для create_entry - обрабатываем КАЖДЫЙ элемент списка
                    if len(_field_value) > 0:
                        for item in _field_value:
                            if is_dataclass(item):
                                nested_result = self._dataclass_to_dict(item, _mode)
                                if nested_result:
                                    result.extend(nested_result)
                    else:
                        current_fields.append((_field_name, _field_info))
            else:
                current_fields.append((_field_name, _field_info))

        if current_fields:
            table_name = _dataclass_instance.__class__.__name__.replace('_', '').lower()
            result.append((table_name, current_fields))

        return result if result else None

    def _clean_field_type(self, _field_type: str) -> str:
        try:
            if _field_type.startswith("<class '") and _field_type.endswith("'>"):
                _field_type = _field_type[8:-2]
            _field_type = _field_type.replace(' | None', '').replace('None | ', '')
            _field_type = _field_type.replace('Optional[', '').replace(']', '')
            _field_type = _field_type.strip()
            
            _available_types = ('str', 'int', 'float', 'bool', 'datetime', 'date', 'time.struct_time', 'list', 'dict', 'tuple')
            
            for _available_type in _available_types:
                if _available_type in _field_type:
                    return _available_type
            
            self._logger.error(f'❌ Тип данных не опознан: {_field_type}, используем str по умолчанию')
            return 'str'
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка в преобразовании типа данных: {e}')
            return 'str'

    def _transform_to_sql_structure(self, _dataclass_structure: list) -> list:
        """
        Преобразует структуру датакласса (список кортежей) в SQL структуру (список)
        Возвращает: [(table_name, [field_definitions]), ...]
        """
        try:
            _sql_tables = []

            for _table_name, _table_fields in _dataclass_structure:
                _table_name_clean = re.sub(r'_', '', _table_name).lower()

                _sql_fields = []
                _has_primary_key = False
                
                for _field_name, _field_info in _table_fields:
                    _field_type = _field_info.get('type')
                    _sql_field_type = self._python_type_to_sql(_field_type)
                    _sql_field_name = _field_name.upper()
                    
                    if _sql_field_name == 'ID':
                        _has_primary_key = True
                        _sql_field_def = f"{_sql_field_name} {_sql_field_type} PRIMARY KEY"
                    else:
                        _sql_field_def = f"{_sql_field_name} {_sql_field_type}"
                    
                    _sql_fields.append(_sql_field_def)
                
                if not _has_primary_key:
                    _sql_fields.insert(0, "ID TEXT PRIMARY KEY")
                
                if _sql_fields:
                    _sql_tables.append((_table_name_clean, _sql_fields))

            return _sql_tables if _sql_tables else None
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка при преобразовании: {e}')
            return None

    def _python_type_to_sql(self, _python_type: str) -> str:
        _type_mapping = {
            'str': 'TEXT',
            'int': 'INTEGER',
            'float': 'REAL',
            'bool': 'INTEGER',
            'datetime': 'TIMESTAMP',
            'date': 'DATE',
            'time.struct_time': 'TIMESTAMP',
            'list': 'TEXT',
        }
        
        _python_type_lower = _python_type.lower()
        for _py_type, _sql_type in _type_mapping.items():
            if _py_type in _python_type_lower:
                return _sql_type
        return 'TEXT'


class _DB_SQL_Lite(DataclassToSql):
    def __init__(self, settings):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._settings = settings
        self._connection = None
        self._cursor = None
        self._db_path = 'articles.db'  
        self._connect()

    def _connect(self) -> bool:
        try:
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row  
            self._cursor = self._connection.cursor()
            return True
        except Exception as e:
            self._logger.error(f'❌ Ошибка подключения к SQLite: {e}')
            return False

    def close(self):
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
        except Exception as e:
            self._logger.error(f'❌ Ошибка при закрытии: {e}')

    def _create_table_if_not_exists(self) -> bool:
        try:
            _structures_list = self._sql_structures
            for _tables in _structures_list:
                for _table_name, _table_fields in _tables:
                    self._cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (_table_name,)
                    )
                    table_exists = self._cursor.fetchone() is not None
                    
                    if table_exists:
                        existing_columns = self._get_table_columns(_table_name)
                        existing_names = [col['name'] for col in existing_columns]
                        
                        for _field_def in _table_fields:
                            _field_name = _field_def.split()[0]
                            if _field_name not in existing_names:
                                self._cursor.execute(f'ALTER TABLE {_table_name} ADD COLUMN {_field_def}')
                                self._logger.info(f'  ➕ Добавлена колонка {_field_name}')
                                self._connection.commit()
                    else:
                        _query = ', '.join(_table_fields)
                        self._cursor.execute(f'''
                            CREATE TABLE IF NOT EXISTS {_table_name} (
                                {_query}
                            )
                        ''')
                        self._connection.commit()
                        self._logger.info(f'    ✅ Таблица {_table_name} создана с {len(_table_fields)} полями')
            
            return True
        except Exception as e:
            self._logger.error(f'❌ Ошибка создания таблиц: {e}')
            if self._connection:
                self._connection.rollback()
            return False

    def _get_table_columns(self, _table_name: str) -> list[dict[str, Any]]:
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
            return columns
        except Exception as e:
            self._logger.error(f'❌ Ошибка получения информации о таблице {_table_name}: {e}')
            return []





    def _generate_save_structure(self, _dataclass):
        """
        Генерирует структуру для сохранения датакласса в БД
        """
        
        result_tables = []
        
        table_name = _dataclass.__class__.__name__.replace('_', '').lower()
        fields_list = []
        values_list = []
        
        for _dataclass_field in fields(_dataclass):
            _field_name = _dataclass_field.name
            _field_value = getattr(_dataclass, _field_name)
            
            # Проверка на список вложенных датаклассов
            if isinstance(_field_value, list) and _field_value:
                if is_dataclass(_field_value[0]):
                    for item in _field_value:
                        nested_result = self._generate_save_structure(item)
                        if nested_result:
                            result_tables.extend(nested_result)
                    continue

                else:
                    fields_list.append(_field_name)
                    values_list.append(json.dumps(_field_value) if _field_value else None)

            elif is_dataclass(_field_value):
                nested_result = self._generate_save_structure(_field_value)
                if nested_result:
                    result_tables.extend(nested_result)

                continue
            else:
                fields_list.append(_field_name)
                
                if isinstance(_field_value, uuid.UUID):
                    values_list.append(str(_field_value))
                elif isinstance(_field_value, bool):
                    values_list.append(1 if _field_value else 0)
                elif isinstance(_field_value, datetime):
                    values_list.append(_field_value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    values_list.append(_field_value)
        
        # Добавляем текущую таблицу, если есть поля
        if fields_list:
            result_tables.append({
                'table_name': table_name,
                'fields': fields_list,
                'values': values_list
            })
        return result_tables


    def _create_from_dataclass(self, 
        _to_table: str = None,
        _field_to_compare: str = None,
        _dataclass=None
    ) -> bool:
        """Создает новую запись в выбранной таблице из датакласса"""
        
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return False
            
            if not _dataclass or not _field_to_compare or not _to_table:
                self._logger.error('❌ Не найден объект для сохранения')
                return False
            
            _field_to_compare_in_data = _HelpfullMethods._get_dataclass_field(_dataclass, _field_to_compare)
            if _field_to_compare and _field_to_compare_in_data is not None:
                self._cursor.execute(
                    f"SELECT id FROM {_to_table} WHERE {_field_to_compare} = ?",
                    (_field_to_compare_in_data,)
                )
                if self._cursor.fetchone():
                    self._logger.info(f'ℹ️ Запись уже существует')
                    return False
            
            _save_structure = self._generate_save_structure(_dataclass)
            if _save_structure:
                for _table in _save_structure:
                    _table_name = _table.get('table_name')
                    _table_columns = _table.get('fields')
                    _table_values = _table.get('values')
                    
                    if not _table_columns or not _table_values:
                        self._logger.warning(f'⚠️ Нет данных для таблицы {_table_name}')
                        continue
                    
                    # ============ ПРОВЕРКА СУЩЕСТВОВАНИЯ КОЛОНОК ============
                    # Получаем существующие колонки в таблице
                    existing_columns = self._get_table_columns(_table_name)
                    existing_column_names = [col['name'].lower() for col in existing_columns]
                    
                    # Фильтруем поля: оставляем только те, что существуют в таблице
                    filtered_columns = []
                    filtered_values = []
                    
                    for col, val in zip(_table_columns, _table_values):
                        col_lower = col.lower()
                        if col_lower in existing_column_names:
                            filtered_columns.append(col)
                            filtered_values.append(val)
                        else:
                            self._logger.warning(f'    ⚠️ Колонка {col} не найдена в таблице {_table_name}, пропускаем')
                    
                    # Проверяем, остались ли поля для вставки
                    if not filtered_columns:
                        self._logger.warning(f'⚠️ Нет валидных колонок для таблицы {_table_name}')
                        continue
                    
                    # ============ ФОРМИРУЕМ ЗАПРОС ============
                    _columns_str = ', '.join(filtered_columns)
                    _placeholders = ', '.join(['?' for _ in filtered_values])
                    _query = f"INSERT INTO {_table_name} ({_columns_str}) VALUES ({_placeholders})"
                    
                    self._cursor.execute(_query, filtered_values)
                    self._connection.commit()
                    
                    self._logger.info(f"    ✅ Запись создана в таблице {_table_name} (полей: {len(filtered_columns)})")

            return True

        except Exception as e:
            self._logger.error(f'❌ Ошибка создания записи: {e}')
            if self._connection:
                self._connection.rollback()
            return False


    def read(self, _table: str = None, _field: str = None, _value: Any = None, _limit: int = None) -> list[dict]:
        try:
            if not self._connection:
                self._logger.error('❌ Нет подключения к БД')
                return []
            
            if _table is None:
                _table = self._settings.read_from_table
            
            if _field and _value is not None:
                query = f"SELECT * FROM {_table} WHERE {_field} = ?"
                params = (_value,)
            else:
                query = f"SELECT * FROM {_table}"
                params = ()
            
            if _limit:
                query += f" LIMIT {_limit}"
            
            self._cursor.execute(query, params)
            results = []
            for row in self._cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка чтения из таблицы {_table}: {e}')
            return []

    def update_field_by_id(self, _table: str = None, _id: Any = None, _field: str = None, _value: Any = None) -> bool:
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
            
            if isinstance(_value, bool):
                _value = 1 if _value else 0
            
            query = f"UPDATE {_table} SET {_field} = ? WHERE id = ?"
            values = [_value, _id]
            
            self._cursor.execute(query, values)
            self._connection.commit()
            
            affected_rows = self._cursor.rowcount
            return affected_rows > 0
            
        except Exception as e:
            self._logger.error(f'❌ Ошибка обновления поля {_field} (ID: {_id}): {e}')
            if self._connection:
                self._connection.rollback()
            return False




class _HelpfullMethods:
    @staticmethod
    def _get_dataclass_field(obj, field_name: str, default=None):
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