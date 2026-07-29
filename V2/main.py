from composition import Composition
import logging
import traceback
from utils import translate_long_text, string_prompts_to_list
import time
from typing import Any
from pathlib import Path
import re
import base64


class Executor(Composition):

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._read_from_table = self.settings.read_from_table
        self._save_data_to_table = self.settings.save_data_to_table
        self._field_to_compare = self.settings.field_to_compare


    def get_unprocessed_articles(self) -> list[dict]:

        if not self.settings.logic.get('parse', False):
            self._logger.info('✅ Парсинг выключен!')
            return None
             
        unprocesed_articles = []
        _new_item = 0

        try: 
            _parsed_articles = self.parsers_manager.parse_all()
            if not _parsed_articles:
                self._logger.info('✅ Нет новых статей из источников')
                return None

            self._logger.info(f'✅ Получено {len(_parsed_articles)} статей из источников')

            for _parsed_article in _parsed_articles:

                _article_link = _parsed_article.get('link', '')
                if not _article_link:
                    self._logger.error(f'   ❌ Пропускаем статью. Нет ссылки')
                    continue

                existed = self.db_manager.read(
                    self._save_data_to_table,
                    self._field_to_compare, 
                    _article_link,
                    1
                )
                if existed:
                    self._logger.info(f'    ✅ Статья уже существует в бд')
                    continue

                self._logger.info(f'    ✅ Найдена статья не сохраненная в бд')
                _new_item += 1
                unprocesed_articles.append(_parsed_article)

            self._logger.info(f'✅ Найдено {_new_item} новыйх статей. Всего получено {len(_parsed_articles)} статей из источников' )
            return unprocesed_articles if unprocesed_articles else []

        except Exception as e:
                self._logger.error(f'❌ Критическая ошибка в получении новых статей: {e}')
                traceback.print_exc()


    def process_new_articles(self, _unprocess_articles: list[dict]) -> list[Any]:

        if not self.settings.logic.get('process', False):
            self._logger.info('✅ Обработка выключена!')
            return _unprocess_articles

        prepared_posts = []
        _processed_count = 0

        self._logger.info(f'✅ Получено {len(_unprocess_articles)} статей для обработки')

        try:
            for idx, _unprocessed_article in enumerate(_unprocess_articles, 1):
                self._logger.info(f'    ✅ Начинаем обработку статьи {idx}')

                _article_text = _unprocessed_article.get('text', '')
                _article_title = _unprocessed_article.get('title', '')


                # ============ ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ============
                self._logger.info('    ✅ Генерируем промпты для изображений')
                _prompt_to_image_model = self.ai_manager.process_text(
                    _article_text,
                    self.settings.models['text_model']['prompts']['prompt_to_image_model']
                )
                                 
                if _prompt_to_image_model:
                    _prompt_to_image_models = string_prompts_to_list(_prompt_to_image_model)
                    self._logger.info(f'    ✅ Сгенерировано {len(_prompt_to_image_model)} промптов')

                    self._logger.info('    ✅ Генерируем изображения')
                    _images = self.ai_manager.generate_image(_prompt_to_image_models[:5])
                    if _images: 
                        self._logger.info(f'    ✅ Сгенерировано {len(_images)} изображений')

                    else: 
                        self._logger.warning('      ⚠️ Не удалось сгенерировать изображения')
                        _images = []
                    
                else:
                    self._logger.warning('      ⚠️ Не удалось сгенерировать промпты для изображений')
                    _images = []


                # ============ ГЕНЕРАЦИЯ ОПИСАНИЯ ============
                self._logger.info('    ✅ Генерируем краткое описание')
                _ai_description = self.ai_manager.process_text(
                    _article_text,
                    self.settings.models['text_model']['prompts']['short_description_prompt']
                )
                                
                if not _ai_description:
                    self._logger.warning('      ⚠️ Не удалось сгенерировать описание, используем оригинальный текст')
                    _ai_description = _article_text[:500] + '...'


                # ============ ПЕРЕВОД ============
                self._logger.info('    ✅ Начинаем перевод текстов.')
                # Переводим заголовок
                _title_translated = translate_long_text(
                    text=_article_title,
                    source_lang='en',
                    target_lang='ru',
                    max_length=10000,
                    delay=0.5
                )
                                
                # Переводим текст статьи
                _article_text_translated = translate_long_text(
                    text=_article_text,
                    source_lang='en',
                    target_lang='ru',
                    max_length=10000,
                    delay=0.5
                )
                                
                # Переводим описание
                _ai_description_translated = translate_long_text(
                    text=_ai_description,
                    source_lang='en',
                    target_lang='ru',
                    max_length=10000,
                    delay=0.5
                )


                # ============ СОЗДАНИЕ ОБЪЕКТА СТАТЬИ ============
                # Дополнительная информация
                _unprocessed_article['title_translated'] = _title_translated
                _unprocessed_article['article_text_translated'] = _article_text_translated
                _unprocessed_article['ai_description'] = _ai_description
                _unprocessed_article['ai_description_translated'] = _ai_description_translated
                _unprocessed_article['images'] = _images if _images else []
                                
                # Создаем объект поста через фабрику
                _post_obj = self.post_manager.create_post(**_unprocessed_article)
                if not _post_obj:
                    self._logger.error(f'   ❌ Не удалось создать объект поста: {_article_title[:50]}...')
                    continue

                self._logger.info(f'    ✅ Успешно создан объект поста: {_article_title[:50]}...')
                prepared_posts.append(_post_obj)
                _processed_count += 1

            self._logger.info(f'✅ Успешно создано {_processed_count} объектов')
            return prepared_posts if prepared_posts else []

        except Exception as e:
            self._logger.error(f'❌ Критическая ошибка в обработке новых статей: {e}')
            traceback.print_exc()


    def save_to_db(self, _post_objects: list[Any]) -> None:

        if not self.settings.logic.get('save_to_db', False):
            self._logger.info('✅ Сохранение в бд выключено!')
            return None

        self._logger.info(f'✅ Сохраняем в бд {len(_post_objects)} постов')
        _saved_db = 0

        try:
            for _idx, _post_object in enumerate(_post_objects, 1):
                 
                success = self.db_manager.create(
                    _to_table=self._save_data_to_table,
                    _field_to_compare=self._field_to_compare,
                    _data=_post_object
                )
                             
                if success:
                    _saved_db += 1
                    self._logger.info(f'    ✅ Пост {_idx} успешно сохранен')
                else:
                    self._logger.error(f'   ❌ Ошибка сохранения поста: {_idx}')

            self._logger.info(f'✅ Сохранено в бд {_saved_db} постов')
            return None

        except Exception as e:
            self._logger.error(f'❌ Критическая ошибка при сохранении в бд: {e}')
            traceback.print_exc()
        

    def publicate_unpublished(self) -> None:

        if not self.settings.logic.get('publicate', False):
            self._logger.info('✅ Публикации выключены!')
            return None

        try: 
            _posts = self.db_manager.read(self._read_from_table, 'VK_published', 0)
            self._logger.info(f'✅ Найдено {len(_posts)} неопубликованных постов')

            _published_count = 0

            for _post in _posts:

                _post_id = _post.get('id')
                _post_title = _post.get('title_translated') or _post.get('title', 'Без названия')
                _post_text = _post.get('ai_description_translated') or _post.get('ai_description', '')
                _post_source = _post.get('source', 'Неизвестный источник')
                _post_link = _post.get('link', '')
                _post_pub_date = _post.get('published', 'Дата неизвестна')
                _post_images = self.db_manager.read('images', 'article_id', _post_id)

                self._logger.info(f'    ✅ Создаем публикацию для поста {_post_id}')

                post_text = f"""
                🔬 {_post_title}
                
                {_post_text}
                
                📌 Источник: {_post_source}
                📅 Дата: {_post_pub_date}
                🔗 Подробнее: {_post_link}
                
                #наука #исследование #медицина
                """

                result = self.vk_manager.create_post(message=post_text.strip())            
                if result:
                    _published_count += 1
                    self._logger.info(f'    ✅ Пост создан (ID: {_post_id})')
                                        
                    self.db_manager.update_field_by_id(
                        _table=self._save_data_to_table,
                        _id=_post_id,
                        _field='VK_published',
                        _value=1
                    )
                    
                else:
                    self._logger.error(f'   ❌ Ошибка публикации (ID: {_post_id})')
                                    
                time.sleep(2)

            self._logger.info(f'✅ Опубликованно {_published_count} Статей')
            return None

        except Exception as e:
            self._logger.error(f'❌ Критическая ошибка при публикации: {e}')
            traceback.print_exc()


    def save_unpublished_to_file(self) -> None:

        if not self.settings.logic.get('save_to_file', False):
            self._logger.info('✅ Сохранение в файл выключено!')
            return None

        try:
            _script_dir = Path(__file__).parent
            _folder_name = 'Posts'
            _folder_path = _script_dir / _folder_name
            _folder_path.mkdir(parents=True, exist_ok=True)

            if not _folder_path.exists() and not _folder_path.is_dir():
                self._logger.info(f'    ❌ Ошибка создания папки для постов')
                return None

            _posts = self.db_manager.read(self._read_from_table, 'VK_published', 0)
            self._logger.info(f'✅ Найдено {len(_posts)} неопубликованных постов')

            _published_count = 0
            
            for _post in _posts:
            
                _post_id = _post.get('id')
                _post_title = _post.get('title_translated') or _post.get('title', 'Без названия')
                _post_text = _post.get('ai_description_translated') or _post.get('ai_description', '')
                _post_source = _post.get('source', 'Неизвестный источник')
                _post_link = _post.get('link', '')
                _post_pub_date = _post.get('published', 'Дата неизвестна')
                _post_images = self.db_manager.read('images', 'article_id', _post_id)

                self._logger.info(f'    ✅ Создаем папку для поста {_post_id}')

                _post_folder_name = _post_title[:25]
                _post_folder_name = re.sub(r'[<>:"/\\|?*]', '_', _post_folder_name)
                _post_folder_name = _post_folder_name.rstrip('. ')

                _post_folder_path = _folder_path / _post_folder_name
                _post_folder_path.mkdir(parents=True, exist_ok=True)

                _post_image_path = _post_folder_path / 'images'
                _post_image_path.mkdir(parents=True, exist_ok=True)

                if (not _post_folder_path.exists() and not _post_folder_path.is_dir()) or \
                    (not _post_image_path.exists() and not _post_image_path.is_dir()):

                    self._logger.info(f'    ❌ Ошибка создания папки для поста {_post_title[:25]}')
                    continue

                _post_text_formed = f"""
                🔬 {_post_title}
                                
                {_post_text}
                                
                📌 Источник: {_post_source}
                📅 Дата: {_post_pub_date}
                🔗 Подробнее: {_post_link}
                                
                #наука #исследование #медицина
                """

                _post_text_file = _post_folder_path / 'post_text.txt'
                with open(_post_text_file, 'w', encoding='utf-8') as f:
                    f.write(_post_text_formed)

                if not _post_text_file.exists():
                    self._logger.info(f'    ❌ Ошибка создания текстового файла для поста {_post_title[:25]}')
                    continue

                for _idx, _post_image in enumerate(_post_images, 1):

                    try:
                        if isinstance(_post_image, dict):
                            _image_data_str = _post_image.get('image_base64', '')
                        
                        if not _image_data_str:
                            self._logger.error(f'    ❌ Пустое изображение {_idx}')
                            continue
                            
                        _image_data = base64.b64decode(_image_data_str)
                        _filename = f"{_idx}.png"
                        _output_path = _post_image_path / _filename
                        _output_path.write_bytes(_image_data)
                        self._logger.info(f'    ✅ Изображение {_idx} сохранено')
                        
                    except Exception as e:
                        self._logger.error(f'    ❌ Ошибка сохранения изображения {_idx}: {e}')
                        continue

                _published_count+=1

                self.db_manager.update_field_by_id(
                    _table=self._save_data_to_table,
                    _id=_post_id,
                    _field='VK_published',
                    _value=1
                )

            self._logger.info(f'✅ Создано {_published_count} новых статей в папке')
            return None

        except Exception as e:
            self._logger.error(f'❌ Критическая при сохранении в файл: {e}')
            traceback.print_exc()


def main():
    # Настройка логирования
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("deep_translator").setLevel(logging.INFO)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logic = Executor()

    unprocessed_articles = logic.get_unprocessed_articles()
    posts_obj = logic.process_new_articles(unprocessed_articles)
    logic.save_to_db(posts_obj)
    logic.publicate_unpublished()
    logic.save_unpublished_to_file()
    logic.destroy()


    
if __name__ == '__main__':
    main()