from composition import Composition
import logging
import traceback
from utils import translate_long_text, string_prompts_to_list, detect_language
import time
from typing import Any
from pathlib import Path
import re
import base64


class Executor(Composition):

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._POST_READ_TABLE = self.settings.POST_READ_TABLE
        self._POST_CREATE_TABLE = self.settings.POST_CREATE_TABLE
        self._POST_UPDATE_TABLE = self.settings.POST_UPDATE_TABLE
        self._POST_FIELD_TO_COMPARE = self.settings.POST_FIELD_TO_COMPARE

        self._DEFAULT_IMG_NAMES = ['default_img_1.jpg', 'default_img_2.jpg', 'default_img_3.jpg', 'default_img_4.jpg', 'default_img_5.jpg']
        self._DEFAULT_IMG_DIR = Path(__file__).parent / 'resources'


    def start(self):
        _empty_dataclass = self.post_manager.get_empty_dataclass()
        self.db_manager.dataclass_to_sql_structure(_empty_dataclass)
        self.db_manager.create_tables_if_not_exists()


    def get_unprocessed_articles(self) -> list[dict]:

        if not self.settings.logic.get('parse', False):
            self._logger.info('⏭️ Парсинг выключен!')
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
                    self._POST_READ_TABLE,
                    self._POST_FIELD_TO_COMPARE, 
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


    def process_new_articles(self, _unprocess_articles: list[dict]) -> None:

        try:
            if not isinstance(_unprocess_articles, list) or len(_unprocess_articles) == 0:
                self._logger.info(f'    ❌ Не удалось получить статьи для обработки')
                return 
            else:
                self._logger.info(f'✅ Получено {len(_unprocess_articles)} статей для обработки')


            if not self.settings.logic.get('process', False):
                self._logger.info(f'    ⏭️ Обработка статей отключена!')
                self._extend_article_data_with_plug(_unprocess_articles)

            else:
                self._logger.info(f'    ✅ Начинаем обработку статей')
                self._extend_article_data(_unprocess_articles)

            return

        except Exception as e:
            self._logger.error(f'❌ Критическая ошибка в обработке новых статей: {e}')
            traceback.print_exc()


    def _extend_article_data_with_plug(self, _unprocess_articles: list[Any]) -> list[Any]:

        try: 
            self._logger.info(f'    =' + '='*50)

            for idx, _unprocessed_article in enumerate(_unprocess_articles, 1):
    
                self._logger.info(f'    ✅ Создаем заглушку для статьи: {idx}')

                _unprocessed_article['is_published_vk'] = False
                _unprocessed_article['is_saved_to_folder'] = False
                _unprocessed_article['title_translated'] = 'Не обработано'
                _unprocessed_article['summary_translated'] = 'Не обработано'
                _unprocessed_article['text_translated'] = 'Не обработано'
                _unprocessed_article['ai_description'] = 'Не обработано'
                _unprocessed_article['ai_description_translated'] = 'Не обработано'
                _unprocessed_article['image'] = []

                self._create_post_object(_unprocessed_article)
            return 

        except Exception as e:
            self._logger.error(f'❌ Ошибка в создании заглушки: {e}')


    def _extend_article_data(self, _unprocess_articles: list[Any]) -> None:

        try:
            for idx, _unprocessed_article in enumerate(_unprocess_articles, 1):
            
                self._logger.info(f'    =' + '='*50)
                self._logger.info(f'    ✅ Обрабатываем статью: {idx}')
                                
                _article_text = _unprocessed_article.get('text', '')
                _article_title = _unprocessed_article.get('title', '')
                _article_summary = _unprocessed_article.get('summary', '')      

                _images = self._add_images(_article_text=_article_text)
                _ai_description = self._add_short_description(_article_text=_article_text)
                _ai_description_translated =  self._add_translation(_text=_ai_description)
                _title_translated = self._add_translation(_text=_article_title)
                _summary_translated = self._add_translation(_text=_article_summary)
                _article_text_translated = self._add_translation(_text=_article_text)
            
                _unprocessed_article['is_published_vk'] = False
                _unprocessed_article['is_saved_to_folder'] = False
                _unprocessed_article['ai_description'] = _ai_description if _ai_description else ''
                _unprocessed_article['summary_translated'] = _summary_translated if _summary_translated else ''
                _unprocessed_article['title_translated'] = _title_translated if _title_translated else '' 
                _unprocessed_article['text_translated'] = _article_text_translated if _article_text_translated else ''
                _unprocessed_article['ai_description_translated'] = _ai_description_translated if _ai_description_translated else ''
                _unprocessed_article['image'] = _images if _images else []

                self._create_post_object(_unprocessed_article)
            return 
    
        except Exception as e:
            self._logger.error(f'❌ Ошибка в добавлении информации: {e}')


    def _add_images(self, _article_text: str) -> list[str] | list[None]:
        """Возвращает сгенерированные или дефолтные img"""

        try:
            if not self.settings.logic.get('generate_img', False):
                self._logger.info('    ⏭️ Генерация изображений отключена!')
                return []

            if self.settings.mode.get('text_only', True):
                self._logger.info('    ⏭️ Генерация изображений отключена! Включен text_only mode!')
                return []
            
            if self.settings.logic.get('use_default_img', False):
                self._logger.info(f'    ✅ Используем дефолтные изображения')
                _images = self._load_default_images(
                    _path=self._DEFAULT_IMG_DIR,
                    _img_names=self._DEFAULT_IMG_NAMES
                )
                return _images

            if not self.settings.logic.get('generate_prompt_to_img_model', False):
                self._logger.info('    ⏭️ Генерация промптов для изображений отключена. Используем дефолтные.')
                
                _prompt_to_image_model = self.settings.models['text_model']['prompts']['default_prompt_to_image_model']

                if not isinstance(_prompt_to_image_model, str) or not _prompt_to_image_model:
                    self._logger.error(f'   ❌ Не удалось получить дефолтный промпт для текстовой модели')
                    return []
            
            else:   
                self._logger.info('    ✅ Генерируем промпты для изображений')

                _prompt_to_text_model = self.settings.models['text_model']['prompts']['generate_prompt_to_image_model']
                if not isinstance(_prompt_to_text_model, str) or not _prompt_to_text_model:
                    self._logger.error(f'   ❌ Не удалось получить промпт для текстовой модели')
                    return []

                _prompt_to_image_model = self.ai_manager.process_text(
                    _article_text,
                    _prompt_to_text_model
                )

            if not _prompt_to_image_model:
                self._logger.error(f'   ❌ Не удалось получить промпт для модели для генерации изображений')
                return []
                                                            
            _prompt_to_image_models = string_prompts_to_list(_prompt_to_image_model)
            self._logger.info(f'    ✅ Получено {len(_prompt_to_image_models)} промптов')
            self._logger.info(f'    ✅ Генерируем изображения')
                                        
            _images = self.ai_manager.generate_images(_prompt_to_image_models[:5])
            if _images: 
                self._logger.info(f'    ✅ Получено {len(_images)} изображений')
                return _images
            
            else: 
                self._logger.warning('      ❌ Не удалось сгенерировать изображения')
                return []

        except Exception as e:
            self._logger.error(f'❌ Ошибка в создании изображений: {e}')
                                    

    def _load_default_images(self, _path: str, _img_names: list[str]) -> list[str] | list[None]:
        """Загружает дефолтные изображения"""

        _default_img_loaded = []

        try:
            if not isinstance(_img_names, list):
                self._logger.error(f'❌ Ошибка: _img_names должен быть списком, получен {type(_img_names)}')
                return []
                
            if not _img_names:
                self._logger.error('❌ Список дефолтных изображений пуст')
                return []
                                                
            for _img in _img_names:
                _img_path = _path / _img
                if not _img_path.exists():
                    self._logger.error(f'❌ Дефолтное изображение не найдено: {_img_path}')
                    continue
                                                        
                with open(_img_path, 'rb') as f:
                    _img_data = f.read()
                    _img_base64 = base64.b64encode(_img_data).decode('utf-8')
                    _default_img_loaded.append(_img_base64)
                                                
            if _default_img_loaded:
                self._logger.info(f'    ✅ Загружено {len(_default_img_loaded)} дефолтных изображений')
                return _default_img_loaded         
            
            else:
                self._logger.error('    ❌ Не удалось загрузить ни одного дефолтного изображения')
                return []
                                            
        except Exception as e:
            self._logger.error(f'❌ Ошибка загрузки дефолтных изображений: {e}')


    def _add_short_description(self, _article_text: str) -> str:

        try:
            if not self.settings.logic.get('generate_short_description', False):
                self._logger.info('    ⏭️ Генерация краткого описания отключена!')
                return ''

            _generate_short_description_prompt = self.settings.models['text_model']['prompts']['short_description_prompt']
            if not isinstance(_generate_short_description_prompt, str) or _generate_short_description_prompt == '':
                self._logger.error(f'   ❌ Не удалось получить промпт для генерации краткого описания')
                return ''

            self._logger.info('    ✅ Генерируем краткое описание')
            _ai_description = self.ai_manager.process_text(
                _article_text,
                _generate_short_description_prompt
            )
                                                    
            if _ai_description:
                self._logger.info('    ✅ Краткое описание сгенерировано')

            else:
                self._logger.error('      ❌ Не удалось сгенерировать описание, используем оригинальный текст')
                _ai_description = _article_text[:500] + '...'

            return _ai_description

        except Exception as e:
            self._logger.error(f'❌ Ошибка генерации кракого описания: {e}')


    def _add_translation(self, _text: str) -> str:

        try:
            if not self.settings.logic.get('translate', False):
                self._logger.info('    ⏭️ Перевод статей отключен!')
                return ''

            if _text == '':
                self._logger.info('    ⏭️ Текст отсутствует')
                return ''

            self._logger.info(f'    ✅ Текст для перевода: {_text[:30]}')

            detected_lang = detect_language(_text[:500])
            if detected_lang == 'ru':
                self._logger.info('    ⏭️ Текст уже на русском')
                return _text

            _source_lang='en'
            _target_lang='ru'
            _max_attempts = 15

            for attempt in range(1, _max_attempts + 1):
                self._logger.info(f'    ✅ Попытка перевода {attempt}/{_max_attempts}')

                _result = translate_long_text(
                    text=_text,
                    source_lang=_source_lang,
                    target_lang=_target_lang,
                    max_length=10000,
                    delay=5
                )

                if _result:
                    _result_lang = detect_language(_result[:500])
                                        
                    if _result_lang == _target_lang:
                        self._logger.info(f'    ✅ Перевод успешен: {_result[:50]}...')
                        return _result

            self._logger.error('      ❌ Не удалось перевести текст')
            return 'Не переведено'

        except Exception as e:
            self._logger.error(f'❌ Ошибка при переводе текста: {e}')


    def _create_post_object(self, _extended_article: dict[Any]) -> None:

        try:
            if not isinstance(_extended_article, dict):
                self._logger.error(f'   ❌ Ошибка в получении расширенных статей')
                return None

            else: 
                self._logger.error(f'    ✅ Получена расширенная статья для создания объектов поста')

            _post_obj = self.post_manager.create_post(**_extended_article)
            self._save_to_db(_post_obj)
            
            if not _post_obj:
                self._logger.error(f'   ❌ Не удалось создать объект поста')
                return None
            
            self._logger.info(f'    ✅ Успешно создан объект поста для статьи')
            return None

        except Exception as e:
            self._logger.error(f'❌ Ошибка в создании объекта поста: {e}')


    def _save_to_db(self, _post_object) -> None:

        try:
            if not self.settings.logic.get('save_to_db', False):
                self._logger.info('⏭️ Сохранение в бд выключено!')
                return

            self._logger.info(f'    ✅ Сохраняем пост в бд')

            success = self.db_manager.create_from_dataclass(
                _to_table=self._POST_CREATE_TABLE,
                _field_to_compare=self._POST_FIELD_TO_COMPARE,
                _data=_post_object
            )
                             
            if success:
                self._logger.info(f'    ✅ Пост успешно сохранен')
            else:
                self._logger.error(f'   ❌ Ошибка сохранения поста')

            return 

        except Exception as e:
            self._logger.error(f'❌ Критическая ошибка при сохранении в бд: {e}')
            traceback.print_exc()
        

















    def publicate_unpublished(self) -> None:

        if not self.settings.logic.get('publicate', False):
            self._logger.info('⏭️ Публикации выключены!')
            return None

        if self.settings.mode.get('debug', True):
            self._logger.info('⏭️ Публикации выключены! Включен debug mode!')
            return None

        try: 
            _posts = self.db_manager.read(self._POST_READ_TABLE, 'is_published_vk', 0)
            self._logger.info(f'✅ Найдено {len(_posts)} неопубликованных постов')

            _published_count = 0

            for _post in _posts:

                _post_id = _post.get('ID')
                _post_title = _post.get('TITLE_TRANSLATED')
                _post_text = _post.get('AI_DESCRIPTION_TRANSLATED')
                _post_source = _post.get('SOURCE', 'Неизвестный источник')
                _post_link = _post.get('LINK', '')
                _post_pub_date = _post.get('PUB_DATE', 'Дата неизвестна')
                _post_images = self.db_manager.read('image', 'post_id', _post_id)

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
                        _table=self._POST_UPDATE_TABLE,
                        _id=_post_id,
                        _field='is_published_vk',
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
            self._logger.info('⏭️ Сохранение в файл выключено!')
            return None

        try:
            _script_dir = Path(__file__).parent
            _folder_name = 'Posts'
            _folder_path = _script_dir / _folder_name
            _folder_path.mkdir(parents=True, exist_ok=True)

            if not _folder_path.exists() and not _folder_path.is_dir():
                self._logger.info(f'    ❌ Ошибка создания папки для постов')
                return None

            _posts = self.db_manager.read(self._POST_READ_TABLE, 'is_saved_to_folder', 0)
            self._logger.info(f'✅ Найдено {len(_posts)} несохраненных в файл постов')

            _published_count = 0
            
            for _post in _posts:
            
                _post_id = _post.get('ID')
                _post_title = _post.get('TITLE_TRANSLATED')
                _post_text = _post.get('AI_DESCRIPTION_TRANSLATED')
                _post_source = _post.get('SOURCE', 'Неизвестный источник')
                _post_link = _post.get('LINK', '')
                _post_pub_date = _post.get('PUB_DATE', 'Дата неизвестна')
                _post_images = self.db_manager.read('image', 'post_id', _post_id)

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
                            _image_data_str = _post_image.get('IMAGE_BASE64', '')
                        
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
                    _table=self._POST_UPDATE_TABLE,
                    _id=_post_id,
                    _field='is_saved_to_folder',
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

    logic.start()
    unprocessed_articles = logic.get_unprocessed_articles()
    if unprocessed_articles:
        logic.process_new_articles(unprocessed_articles)

    logic.publicate_unpublished()
    logic.save_unpublished_to_file()
    logic.destroy()

if __name__ == '__main__':
    main()