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
        self.split_method = 'regex'
        self.manual_markers = []
        self.keep_manual_markers = False
        self.manual_case_sensitive = False
        self.length_value = 5000
        self.length_unit = 'chars'
        self.length_smart = True
        self.length_keep_paragraphs = True
        
    def set_processor_config(self, settings=None, **kwargs):
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
    
    def set_split_config(self, method='regex', **kwargs):
        self.split_method = method
        
        if method == 'manual':
            self.manual_markers = kwargs.get('markers', [])
            self.keep_manual_markers = kwargs.get('keep_markers', False)
            self.manual_case_sensitive = kwargs.get('case_sensitive', False)
        
        elif method == 'length':
            self.length_value = kwargs.get('length', 5000)
            self.length_unit = kwargs.get('unit', 'chars')
            self.length_smart = kwargs.get('smart', True)
            self.length_keep_paragraphs = kwargs.get('keep_paragraphs', True)
    
    def load_file(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()
            
            if raw_data.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            elif raw_data.startswith(codecs.BOM_UTF16_LE):
                encoding = 'utf-16-le'
            elif raw_data.startswith(codecs.BOM_UTF16_BE):
                encoding = 'utf-16-be'
            else:
                encodings = ['utf-8', 'windows-1251', 'cp1251', 'koi8-r']
                for enc in encodings:
                    try:
                        raw_data.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    encoding = 'utf-8'
            
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
                
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла: {e}")
    
    def get_base_filename(self, filepath):
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        return base_name
    
    def split_text(self, text, clean_callback=None):
        """
        Разбивает текст на разделы в зависимости от выбранного метода
        """
        if self.split_method == 'manual':
            sections = self.text_processor.split_by_manual_markers(
                text,
                self.manual_markers,
                self.keep_manual_markers,
                self.manual_case_sensitive,
                clean_section=True,
                clean_callback=clean_callback
            )
        elif self.split_method == 'length':
            sections = self.text_processor.split_by_length(
                text,
                self.length_value,
                self.length_unit,
                self.length_smart,
                self.length_keep_paragraphs,
                clean_section=True,
                clean_callback=clean_callback
            )
        else:
            matches = self.text_processor.find_markers(text)
            sections = []
            
            for i, match in enumerate(matches):
                section_num = match.group(1)
                start_pos = match.start()
                
                if i + 1 < len(matches):
                    end_pos = matches[i + 1].start()
                else:
                    end_pos = len(text)
                
                raw_content = text[start_pos:end_pos]
                cleaned_content = self.text_processor.clean_text_section(raw_content, clean_callback)
                sections.append((section_num, cleaned_content))
        
        return sections
    
    def clean_whole_file(self, text, clean_callback=None):
        return self.text_processor.clean_whole_text(text, clean_callback)
    
    def save_cleaned_file(self, cleaned_text, input_filepath, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = self.get_base_filename(input_filepath)
        filename = f"{base_name}_cleaned.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        return filepath
    
    def save_sections(self, sections, input_filepath, output_dir, callback=None):
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = self.get_base_filename(input_filepath)
        created_files = []
        
        for i, (section_num, content) in enumerate(sections):
            file_num = str(i + 1).zfill(3)
            filename = f"{file_num}_{base_name}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(filepath)
            
            if callback:
                callback(i + 1, len(sections), filepath)
        
        return created_files