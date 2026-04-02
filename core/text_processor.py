# -*- coding: utf-8 -*-

"""
Модуль для обработки текста
"""

import re
import json
import unicodedata

class TextProcessor:
    """Класс для обработки текста"""
    
    def __init__(self):
        """Инициализация процессора текста"""
        self.marker_pattern = r'^\s*(\d+)\.\s*'
        self.marker_description = "Цифры с точкой (1., 2., ...)"
        self.remove_brackets = True
        self.bracket_pairs = ['()']  # Список пар скобок для удаления
        self.remove_spaces = True
        self.normalize_punctuation = True
        self.chars_to_remove = []  # Список символов для удаления
        self.remove_invisible = True  # Удалять скрытые символы
        
    def set_marker_pattern(self, pattern, description=""):
        """Установить шаблон маркера"""
        self.marker_pattern = pattern
        self.marker_description = description
    
    def get_marker_pattern(self):
        """Получить шаблон маркера"""
        return self.marker_pattern
    
    def get_marker_description(self):
        """Получить описание маркера"""
        return self.marker_description
    
    def set_remove_brackets(self, remove):
        """Установить флаг удаления скобок"""
        self.remove_brackets = remove
    
    def set_bracket_pairs(self, pairs):
        """Установить список пар скобок"""
        self.bracket_pairs = pairs
    
    def set_remove_spaces(self, remove):
        """Установить флаг удаления лишних пробелов"""
        self.remove_spaces = remove
    
    def set_normalize_punctuation(self, normalize):
        """Установить флаг нормализации знаков препинания"""
        self.normalize_punctuation = normalize
    
    def set_chars_to_remove(self, chars):
        """Установить список символов для удаления"""
        self.chars_to_remove = chars
    
    def set_remove_invisible(self, remove):
        """Установить флаг удаления скрытых символов"""
        self.remove_invisible = remove
    
    def remove_parentheses_content(self, text):
        """
        Удаляет содержимое в указанных скобках
        
        Args:
            text: исходный текст
            
        Returns:
            текст с удаленным содержимым в скобках
        """
        result = text
        
        for pair in self.bracket_pairs:
            if len(pair) == 2:
                open_bracket = pair[0]
                close_bracket = pair[1]
                # Экранируем специальные символы regex
                open_bracket_escaped = re.escape(open_bracket)
                close_bracket_escaped = re.escape(close_bracket)
                pattern = re.compile(
                    f'{open_bracket_escaped}[^{open_bracket_escaped}{close_bracket_escaped}]*{close_bracket_escaped}',
                    re.DOTALL
                )
                result = pattern.sub('', result)
        
        return result
    
    def remove_specific_chars(self, text):
        """
        Удаляет указанные символы из текста
        
        Args:
            text: исходный текст
            
        Returns:
            текст с удаленными символами
        """
        if not self.chars_to_remove:
            return text
        
        for char in self.chars_to_remove:
            if char:
                text = text.replace(char, '')
        
        return text
    
    def remove_number_markers(self, text):
        """
        Удаляет маркеры из начала и конца текста
        
        Args:
            text: текст раздела
            
        Returns:
            текст с удаленными маркерами
        """
        # Удаляем маркер в начале текста
        pattern_start = re.compile(self.marker_pattern)
        text = pattern_start.sub('', text)
        
        # Удаляем цифру с точкой в конце текста, но оставляем саму точку
        pattern_end = re.compile(r'\s*\d+\.\s*$')
        text = pattern_end.sub('.', text)
        
        # Если после замены получилось две точки подряд, заменяем на одну
        text = re.sub(r'\.\.', '.', text)
        
        return text
    
    def get_invisible_chars_info(self, text):
        """
        Анализирует текст на наличие скрытых и нестандартных символов
        
        Args:
            text: исходный текст
            
        Returns:
            словарь с информацией о найденных символах
        """
        invisible_info = {
            'has_invisible': False,
            'chars': {},
            'samples': []
        }
        
        # Определение невидимых и специальных символов
        invisible_categories = {
            'bom': r'[\uFEFF]',  # BOM (Byte Order Mark)
            'control': r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Управляющие символы
            'special_spaces': r'[\u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000]',  # Специальные пробелы
            'zero_width': r'[\u200B\u200C\u200D\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2060]',  # Нулевой ширины
            'soft_hyphen': r'[\u00AD]',  # Мягкий перенос
        }
        
        for category, pattern in invisible_categories.items():
            matches = re.findall(pattern, text)
            if matches:
                invisible_info['has_invisible'] = True
                invisible_info['chars'][category] = len(matches)
                # Сохраняем примеры (не более 3)
                samples = list(set(matches))[:3]
                for sample in samples:
                    try:
                        name = unicodedata.name(sample, 'UNKNOWN')
                    except:
                        name = 'UNKNOWN'
                    sample_info = {
                        'char': sample,
                        'code': f'U+{ord(sample):04X}',
                        'name': name,
                        'category': category
                    }
                    if sample_info not in invisible_info['samples']:
                        invisible_info['samples'].append(sample_info)
        
        return invisible_info
    
    def remove_invisible_chars(self, text, log_callback=None):
        """
        Удаление скрытых и невидимых символов
        
        Args:
            text: исходный текст
            log_callback: функция для логирования обнаруженных символов
            
        Returns:
            очищенный текст
        """
        if not self.remove_invisible:
            return text
        
        # Получаем информацию о скрытых символах до удаления
        invisible_info = self.get_invisible_chars_info(text)
        
        # Логируем найденные символы
        if log_callback and invisible_info['has_invisible']:
            log_callback(f"Обнаружены скрытые символы:")
            for sample in invisible_info['samples']:
                log_callback(f"  - {sample['name']} ({sample['code']}) - {sample['char']}")
            for category, count in invisible_info['chars'].items():
                log_callback(f"  {category}: {count} символов")
        
        # 1. Удаляем BOM (самый первый символ)
        text = text.replace('\uFEFF', '')
        
        # 2. Замена специальных пробелов на обычные (ДО нормализации)
        special_spaces = {
            '\u2000': ' ',  # en quad
            '\u2001': ' ',  # em quad
            '\u2002': ' ',  # en space
            '\u2003': ' ',  # em space
            '\u2004': ' ',  # three-per-em space
            '\u2005': ' ',  # four-per-em space
            '\u2006': ' ',  # six-per-em space
            '\u2007': ' ',  # figure space
            '\u2008': ' ',  # punctuation space
            '\u2009': ' ',  # thin space
            '\u200A': ' ',  # hair space
            '\u202F': ' ',  # narrow no-break space
            '\u205F': ' ',  # medium mathematical space
            '\u3000': ' ',  # ideographic space
            '\u00A0': ' ',  # неразрывный пробел (NBSP)
        }
        for special, normal in special_spaces.items():
            if special in text:
                text = text.replace(special, normal)
        
        # 3. Нормализация Юникода (NFKC - совместимая композиция)
        text = unicodedata.normalize('NFKC', text)
        
        # 4. Удаление управляющих символов (кроме \n, \r, \t)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 5. Удаление невидимых символов
        invisible_chars = [
            '\u200B',  # zero width space
            '\u200C',  # zero width non-joiner
            '\u200D',  # zero width joiner
            '\u200E',  # left-to-right mark
            '\u200F',  # right-to-left mark
            '\u202A',  # left-to-right embedding
            '\u202B',  # right-to-left embedding
            '\u202C',  # pop directional formatting
            '\u202D',  # left-to-right override
            '\u202E',  # right-to-left override
            '\u2060',  # word joiner
            '\u00AD',  # soft hyphen
        ]
        for char in invisible_chars:
            if char in text:
                text = text.replace(char, '')
        
        # 6. Дополнительная чистка: удаляем лишние пробелы, которые могли появиться
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def clean_text(self, text):
        """
        Очищает текст: удаляет лишние пробелы и нормализует знаки препинания
        
        Args:
            text: исходный текст
            
        Returns:
            очищенный текст
        """
        # Удаляем лишние пробелы
        if self.remove_spaces:
            text = re.sub(r'\s+', ' ', text)
        
        # Нормализуем знаки препинания
        if self.normalize_punctuation:
            # Удаляем пробелы перед знаками препинания
            text = re.sub(r'\s+([,\.;:!?])', r'\1', text)
            # Добавляем пробел после знаков препинания (если нет)
            text = re.sub(r'([,\.;:!?])([^\s])', r'\1 \2', text)
        
        # Удаляем пробелы в начале и конце
        text = text.strip()
        
        return text
    
    def clean_text_section(self, text, log_callback=None):
        """
        Полная очистка текстового раздела
        Правильная последовательность:
        0. Удаление скрытых символов (самое первое)
        1. Удаление содержимого в скобках (структурная очистка)
        2. Удаление маркеров (удаление служебной информации)
        3. Удаление указанных символов (финальная чистка)
        4. Очистка текста (пробелы и пунктуация)
        
        Args:
            text: текст раздела
            log_callback: функция для логирования
            
        Returns:
            очищенный текст
        """
        # Шаг 0: Удаление скрытых символов (самое первое)
        text = self.remove_invisible_chars(text, log_callback)
        
        # Шаг 1: Удаляем содержимое в скобках (структурная очистка)
        if self.remove_brackets:
            text = self.remove_parentheses_content(text)
        
        # Шаг 2: Удаляем маркеры (удаление служебной информации)
        text = self.remove_number_markers(text)
        
        # Шаг 3: Удаляем указанные символы (финальная чистка)
        text = self.remove_specific_chars(text)
        
        # Шаг 4: Очищаем текст (пробелы и пунктуация)
        text = self.clean_text(text)
        
        return text
    
    def clean_whole_text(self, text, log_callback=None):
        """
        Очистка всего текста без разбиения на разделы
        (не удаляет маркеры, только скобки, символы и пробелы)
        
        Args:
            text: исходный текст
            log_callback: функция для логирования
            
        Returns:
            очищенный текст
        """
        # Шаг 0: Удаление скрытых символов
        text = self.remove_invisible_chars(text, log_callback)
        
        # Шаг 1: Удаляем содержимое в скобках
        if self.remove_brackets:
            text = self.remove_parentheses_content(text)
        
        # Шаг 2: Удаляем указанные символы
        text = self.remove_specific_chars(text)
        
        # Шаг 3: Очищаем текст (пробелы и пунктуация)
        text = self.clean_text(text)
        
        return text
    
    def find_markers(self, text):
        """
        Находит все маркеры в тексте
        
        Args:
            text: исходный текст
            
        Returns:
            список найденных маркеров
        """
        pattern = re.compile(self.marker_pattern, re.MULTILINE)
        return list(pattern.finditer(text))
    
    def get_profile(self):
        """
        Получить текущий профиль настроек
        
        Returns:
            словарь с настройками
        """
        return {
            'marker_pattern': self.marker_pattern,
            'marker_description': self.marker_description,
            'remove_brackets': self.remove_brackets,
            'bracket_pairs': self.bracket_pairs,
            'remove_spaces': self.remove_spaces,
            'normalize_punctuation': self.normalize_punctuation,
            'chars_to_remove': self.chars_to_remove,
            'remove_invisible': self.remove_invisible
        }
    
    def load_profile(self, profile):
        """
        Загрузить профиль настроек
        
        Args:
            profile: словарь с настройками
        """
        if 'marker_pattern' in profile:
            self.marker_pattern = profile['marker_pattern']
        if 'marker_description' in profile:
            self.marker_description = profile['marker_description']
        if 'remove_brackets' in profile:
            self.remove_brackets = profile['remove_brackets']
        if 'bracket_pairs' in profile:
            self.bracket_pairs = profile['bracket_pairs']
        if 'remove_spaces' in profile:
            self.remove_spaces = profile['remove_spaces']
        if 'normalize_punctuation' in profile:
            self.normalize_punctuation = profile['normalize_punctuation']
        if 'chars_to_remove' in profile:
            self.chars_to_remove = profile['chars_to_remove']
        if 'remove_invisible' in profile:
            self.remove_invisible = profile['remove_invisible']