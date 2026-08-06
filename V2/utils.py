# utils.py - с deep-translator
from deep_translator import GoogleTranslator
import logging
import time
import re


def translate_long_text(text: str, 
                        source_lang: str = 'en', 
                        target_lang: str = 'ru', 
                        max_length: int = 4500,
                        delay: float = 0.5) -> str:
    """
    Переводит длинный текст с помощью deep-translator.
    """
    if not text:
        return ''
    
    # Пробуем перевести целиком
    if len(text) <= max_length:
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            if result:
                return result
        except Exception as e:
            error_msg = str(e).lower()
            if "length" in error_msg or "5000" in error_msg or "too long" in error_msg:
                pass

            else:
                return text
    
    # Разбиваем текст на логические блоки (по предложениям)
    blocks = _split_into_blocks(text, max_length)
    
    # Переводим каждый блок
    translated_blocks = []
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    for i, block in enumerate(blocks, 1):
        
        # Если блок все еще слишком длинный - разбиваем еще
        if len(block) > max_length:
            sub_blocks = _split_by_words(block, max_length)
            for sub_block in sub_blocks:
                translated = _safe_translate(translator, sub_block, source_lang, target_lang)
                if translated:
                    translated_blocks.append(translated)
                time.sleep(delay)
        else:
            translated = _safe_translate(translator, block, source_lang, target_lang)
            if translated:
                translated_blocks.append(translated)
            time.sleep(delay)
    
    result = ' '.join(translated_blocks)
    return result


def _split_into_blocks(text: str, max_length: int) -> list:
    """Разбивает текст на блоки по максимальной длине"""
    blocks = []
    current_block = ''
    
    # Разбиваем по предложениям
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        # Если предложение слишком длинное, разбиваем по запятым
        if len(sentence) > max_length:
            # Если есть текущий блок - сохраняем
            if current_block:
                blocks.append(current_block)
                current_block = ''
            
            # Разбиваем длинное предложение на части
            parts = re.split(r'(?<=,)\s+', sentence)
            temp_block = ''
            for part in parts:
                if len(temp_block) + len(part) + 1 <= max_length:
                    temp_block += ' ' + part if temp_block else part
                else:
                    if temp_block:
                        blocks.append(temp_block)
                    temp_block = part
            if temp_block:
                blocks.append(temp_block)
        else:
            # Проверяем, помещается ли предложение в текущий блок
            if len(current_block) + len(sentence) + 1 <= max_length:
                current_block += ' ' + sentence if current_block else sentence
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = sentence
    
    if current_block:
        blocks.append(current_block)
    
    return blocks


def _split_by_words(text: str, max_length: int) -> list:
    """Разбивает текст на части по словам"""
    if len(text) <= max_length:
        return [text]
    
    words = text.split()
    parts = []
    current_part = ''
    
    for word in words:
        if len(current_part) + len(word) + 1 <= max_length:
            current_part += ' ' + word if current_part else word
        else:
            if current_part:
                parts.append(current_part)
            current_part = word
    
    if current_part:
        parts.append(current_part)
    
    return parts


def _safe_translate(translator, text: str, source_lang: str, target_lang: str) -> str:
    """Безопасно переводит текст с повторными попытками"""
    if not text or len(text.strip()) < 2:
        return text
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = translator.translate(text)
            if result:
                return result
            else:
                time.sleep(1)
        except Exception as e:
            error_msg = str(e).lower()
            if "length" in error_msg or "5000" in error_msg or "too long" in error_msg:
                # Если все еще слишком длинный - разбиваем еще мельче
                if len(text) > 2000:
                    sub_parts = _split_by_words(text, 2000)
                    translated_parts = []
                    for sub_part in sub_parts:
                        sub_result = _safe_translate(translator, sub_part, source_lang, target_lang)
                        if sub_result:
                            translated_parts.append(sub_result)
                        time.sleep(0.3)
                    return ' '.join(translated_parts)
            else:
                time.sleep(1)
    
    # Если все попытки не удались - возвращаем исходный текст
    return text


def string_prompts_to_list(raw_text: str) -> list[str]:
    """
    Парсит сырой текст от модели в список промптов
    """
    if not raw_text:
        return []
    raw_text = raw_text.strip()
    
    import re
    parts = re.split(r'\.\s+', raw_text)
    
    cleaned = []
    for p in parts:
        p = ' '.join(p.strip().split())
        if p:
            cleaned.append(p + '.')
    
    return cleaned


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance