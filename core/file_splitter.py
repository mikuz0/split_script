# -*- coding: utf-8 -*-

"""
Модуль для разбиения файлов
"""

import os
import codecs
from core.text_processor import TextProcessor

class FileSplitter:
    """Класс для разбиения файлов"""
    
    def __init__(self):
        """Инициализация сплиттера"""
        self.text_processor = TextProcessor()
        
    def set_processor_config(self, settings=None, **kwargs):
        """
        Установка конфигурации процессора
        
        Args:
            settings: словарь с настройками
            **kwargs: отдельные параметры настройки
        """
        # Если передан словарь настроек
        if settings:
            if 'marker_pattern' in settings:
                self.text_processor.set_marker_pattern(
                    settings['marker_pattern'],
                    settings.get('marker_description', '')
                )
            if 'remove_brackets' in settings:
                self.text_processor.set_remove_brackets(settings['remove_brackets'])
            if 'bracket_pairs' in settings:
                self.text_processor.set_bracket_pairs(settings['bracket_pairs'])
            if 'remove_spaces' in settings:
                self.text_processor.set_remove_spaces(settings['remove_spaces'])
            if 'normalize_punctuation' in settings:
                self.text_processor.set_normalize_punctuation(settings['normalize_punctuation'])
            if 'chars_to_remove' in settings:
                self.text_processor.set_chars_to_remove(settings['chars_to_remove'])
            if 'remove_invisible' in settings:
                self.text_processor.set_remove_invisible(settings['remove_invisible'])
        else:
            # Если переданы отдельные параметры (для обратной совместимости)
            if 'remove_brackets' in kwargs:
                self.text_processor.set_remove_brackets(kwargs['remove_brackets'])
            if 'bracket_pairs' in kwargs:
                self.text_processor.set_bracket_pairs(kwargs['bracket_pairs'])
            if 'marker_pattern' in kwargs:
                self.text_processor.set_marker_pattern(
                    kwargs['marker_pattern'],
                    kwargs.get('marker_description', '')
                )
    
    def load_file(self, filepath):
        """
        Загружает текст из файла с определением кодировки
        
        Args:
            filepath: путь к файлу
            
        Returns:
            текст файла или None в случае ошибки
        """
        try:
            # Пытаемся определить кодировку
            with open(filepath, 'rb') as f:
                raw_data = f.read()
            
            # Проверяем BOM и читаем в правильной кодировке
            if raw_data.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            elif raw_data.startswith(codecs.BOM_UTF16_LE):
                encoding = 'utf-16-le'
            elif raw_data.startswith(codecs.BOM_UTF16_BE):
                encoding = 'utf-16-be'
            else:
                # Пробуем распространенные кодировки
                encodings = ['utf-8', 'windows-1251', 'cp1251', 'koi8-r']
                for enc in encodings:
                    try:
                        raw_data.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    encoding = 'utf-8'  # по умолчанию
            
            # Читаем файл с определенной кодировкой
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
                
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла: {e}")
    
    def get_base_filename(self, filepath):
        """
        Получает базовое имя файла без расширения
        
        Args:
            filepath: путь к файлу
            
        Returns:
            имя файла без расширения
        """
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        return base_name
    
    def split_text(self, text):
        """
        Разбивает текст на разделы
        
        Args:
            text: исходный текст
            
        Returns:
            список кортежей (номер, содержимое)
        """
        matches = self.text_processor.find_markers(text)
        sections = []
        
        for i, match in enumerate(matches):
            # Номер раздела (из маркера)
            section_num = match.group(1)
            
            # Начало раздела
            start_pos = match.start()
            
            # Конец раздела
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # Извлекаем содержимое
            raw_content = text[start_pos:end_pos]
            
            # Очищаем содержимое (с удалением маркеров)
            cleaned_content = self.text_processor.clean_text_section(raw_content)
            
            sections.append((section_num, cleaned_content))
        
        return sections
    
    def clean_whole_file(self, text):
        """
        Очищает весь текст без разбиения (сохраняет маркеры)
        
        Args:
            text: исходный текст
            
        Returns:
            очищенный текст
        """
        return self.text_processor.clean_whole_text(text)
    
    def save_cleaned_file(self, cleaned_text, input_filepath, output_dir):
        """
        Сохраняет очищенный текст в файл
        
        Args:
            cleaned_text: очищенный текст
            input_filepath: путь к исходному файлу
            output_dir: директория для сохранения
            
        Returns:
            путь к сохраненному файлу
        """
        # Создаем директорию, если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = self.get_base_filename(input_filepath)
        filename = f"{base_name}_cleaned.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Сохраняем файл в UTF-8 без BOM
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        return filepath
    
    def save_sections(self, sections, input_filepath, output_dir, callback=None):
        """
        Сохраняет разделы в файлы (UTF-8 без BOM для совместимости с Windows)
        
        Args:
            sections: список разделов
            input_filepath: путь к исходному файлу
            output_dir: директория для сохранения
            callback: функция обратного вызова для обновления прогресса
            
        Returns:
            список созданных файлов
        """
        # Создаем директорию, если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = self.get_base_filename(input_filepath)
        created_files = []
        
        for i, (section_num, content) in enumerate(sections):
            # Формируем имя файла: 001_имя.txt
            file_num = str(i + 1).zfill(3)
            filename = f"{file_num}_{base_name}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Сохраняем файл в UTF-8 без BOM
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(filepath)
            
            # Вызываем callback для обновления прогресса
            if callback:
                callback(i + 1, len(sections), filepath)
        
        return created_files