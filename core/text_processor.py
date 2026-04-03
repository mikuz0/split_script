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
        self.bracket_pairs = ['()']
        self.remove_spaces = True
        self.normalize_punctuation = True
        self.chars_to_remove = []
        self.remove_invisible = True
        
    def set_marker_pattern(self, pattern, description=""):
        self.marker_pattern = pattern
        self.marker_description = description
    
    def get_marker_pattern(self):
        return self.marker_pattern
    
    def get_marker_description(self):
        return self.marker_description
    
    def set_remove_brackets(self, remove):
        self.remove_brackets = remove
    
    def set_bracket_pairs(self, pairs):
        self.bracket_pairs = pairs
    
    def set_remove_spaces(self, remove):
        self.remove_spaces = remove
    
    def set_normalize_punctuation(self, normalize):
        self.normalize_punctuation = normalize
    
    def set_chars_to_remove(self, chars):
        self.chars_to_remove = chars
    
    def set_remove_invisible(self, remove):
        self.remove_invisible = remove
    
    def remove_parentheses_content(self, text):
        result = text
        for pair in self.bracket_pairs:
            if len(pair) == 2:
                open_bracket = pair[0]
                close_bracket = pair[1]
                open_bracket_escaped = re.escape(open_bracket)
                close_bracket_escaped = re.escape(close_bracket)
                pattern = re.compile(
                    f'{open_bracket_escaped}[^{open_bracket_escaped}{close_bracket_escaped}]*{close_bracket_escaped}',
                    re.DOTALL
                )
                result = pattern.sub('', result)
        return result
    
    def remove_specific_chars(self, text):
        if not self.chars_to_remove:
            return text
        for char in self.chars_to_remove:
            if char:
                text = text.replace(char, '')
        return text
    
    def remove_number_markers(self, text):
        pattern_start = re.compile(self.marker_pattern)
        text = pattern_start.sub('', text)
        pattern_end = re.compile(r'\s*\d+\.\s*$')
        text = pattern_end.sub('.', text)
        text = re.sub(r'\.\.', '.', text)
        return text
    
    def get_invisible_chars_info(self, text):
        invisible_info = {
            'has_invisible': False,
            'chars': {},
            'samples': []
        }
        
        invisible_categories = {
            'bom': r'[\uFEFF]',
            'control': r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',
            'special_spaces': r'[\u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000]',
            'zero_width': r'[\u200B\u200C\u200D\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2060]',
            'soft_hyphen': r'[\u00AD]',
        }
        
        for category, pattern in invisible_categories.items():
            matches = re.findall(pattern, text)
            if matches:
                invisible_info['has_invisible'] = True
                invisible_info['chars'][category] = len(matches)
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
        if not self.remove_invisible:
            return text
        
        invisible_info = self.get_invisible_chars_info(text)
        
        if log_callback and invisible_info['has_invisible']:
            log_callback(f"Обнаружены скрытые символы:")
            for sample in invisible_info['samples']:
                log_callback(f"  - {sample['name']} ({sample['code']}) - {sample['char']}")
            for category, count in invisible_info['chars'].items():
                log_callback(f"  {category}: {count} символов")
        
        text = text.replace('\uFEFF', '')
        
        special_spaces = {
            '\u2000': ' ', '\u2001': ' ', '\u2002': ' ', '\u2003': ' ',
            '\u2004': ' ', '\u2005': ' ', '\u2006': ' ', '\u2007': ' ',
            '\u2008': ' ', '\u2009': ' ', '\u200A': ' ', '\u202F': ' ',
            '\u205F': ' ', '\u3000': ' ', '\u00A0': ' '
        }
        for special, normal in special_spaces.items():
            if special in text:
                text = text.replace(special, normal)
        
        text = unicodedata.normalize('NFKC', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        invisible_chars = [
            '\u200B', '\u200C', '\u200D', '\u200E', '\u200F',
            '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
            '\u2060', '\u00AD'
        ]
        for char in invisible_chars:
            if char in text:
                text = text.replace(char, '')
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def clean_text(self, text):
        if self.remove_spaces:
            text = re.sub(r'\s+', ' ', text)
        
        if self.normalize_punctuation:
            text = re.sub(r'\s+([,\.;:!?])', r'\1', text)
            text = re.sub(r'([,\.;:!?])([^\s])', r'\1 \2', text)
        
        text = text.strip()
        return text
    
    def clean_text_section(self, text, log_callback=None):
        text = self.remove_invisible_chars(text, log_callback)
        if self.remove_brackets:
            text = self.remove_parentheses_content(text)
        text = self.remove_number_markers(text)
        text = self.remove_specific_chars(text)
        text = self.clean_text(text)
        return text
    
    def clean_whole_text(self, text, log_callback=None):
        text = self.remove_invisible_chars(text, log_callback)
        if self.remove_brackets:
            text = self.remove_parentheses_content(text)
        text = self.remove_specific_chars(text)
        text = self.clean_text(text)
        return text
    
    def find_markers(self, text):
        pattern = re.compile(self.marker_pattern, re.MULTILINE)
        return list(pattern.finditer(text))
    
    def split_by_manual_markers(self, text, markers, keep_markers=False, case_sensitive=False, clean_section=True, clean_callback=None):
        """
        Разбиение текста по ручным меткам.
        При keep_markers=True метка сохраняется в начале следующей секции,
        а не выделяется в отдельный файл.
        
        Args:
            text: исходный текст
            markers: список меток-разделителей
            keep_markers: сохранять ли метки в тексте
            case_sensitive: учитывать ли регистр
            clean_section: применять ли очистку к секциям
            clean_callback: функция для логирования при очистке
            
        Returns:
            список секций
        """
        if not markers:
            section_text = text.strip()
            if clean_section:
                section_text = self.clean_text_section(section_text, clean_callback)
            return [(1, section_text)]
        
        sections = []
        current_pos = 0
        sorted_markers = sorted(markers, key=len, reverse=True)
        escaped_markers = [re.escape(m) for m in sorted_markers]
        
        if case_sensitive:
            pattern = re.compile('|'.join(escaped_markers), re.MULTILINE)
        else:
            pattern = re.compile('|'.join(escaped_markers), re.MULTILINE | re.IGNORECASE)
        
        matches = list(pattern.finditer(text))
        
        if not matches:
            section_text = text.strip()
            if clean_section:
                section_text = self.clean_text_section(section_text, clean_callback)
            return [(1, section_text)]
        
        marker_positions = []
        for match in matches:
            marker_positions.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })
        
        section_start = 0
        section_num = 1
        
        for i, marker in enumerate(marker_positions):
            if section_start < marker['start']:
                section_text = text[section_start:marker['start']].strip()
                if section_text:
                    if clean_section:
                        section_text = self.clean_text_section(section_text, clean_callback)
                    sections.append((section_num, section_text))
                    section_num += 1
            
            if keep_markers:
                section_start = marker['start']
            else:
                section_start = marker['end']
        
        if section_start < len(text):
            section_text = text[section_start:].strip()
            if section_text:
                if clean_section:
                    section_text = self.clean_text_section(section_text, clean_callback)
                sections.append((section_num, section_text))
        
        if not sections:
            section_text = text.strip()
            if clean_section:
                section_text = self.clean_text_section(section_text, clean_callback)
            return [(1, section_text)]
        
        return sections
    
    def split_by_length(self, text, length, unit='chars', smart=True, keep_paragraphs=True, clean_section=True, clean_callback=None):
        if not text or length <= 0:
            section_text = text.strip()
            if clean_section:
                section_text = self.clean_text_section(section_text, clean_callback)
            return [(1, section_text)]
        
        if unit == 'lines':
            lines = text.split('\n')
            sections = []
            current_section = []
            current_count = 0
            
            for line in lines:
                current_count += 1
                current_section.append(line)
                
                if current_count >= length:
                    section_text = '\n'.join(current_section).strip()
                    if clean_section:
                        section_text = self.clean_text_section(section_text, clean_callback)
                    sections.append((len(sections) + 1, section_text))
                    current_section = []
                    current_count = 0
            
            if current_section:
                section_text = '\n'.join(current_section).strip()
                if clean_section:
                    section_text = self.clean_text_section(section_text, clean_callback)
                sections.append((len(sections) + 1, section_text))
            
            return sections
        
        else:
            sections = []
            start = 0
            
            while start < len(text):
                end = min(start + length, len(text))
                
                if smart and end < len(text):
                    new_end = self.find_nearest_sentence_end(text, end, 'backward')
                    if new_end > start:
                        end = new_end
                
                if keep_paragraphs and end < len(text):
                    paragraph_end = text.rfind('\n', start, end)
                    if paragraph_end > start + length // 2:
                        end = paragraph_end + 1
                
                section_text = text[start:end].strip()
                if section_text:
                    if clean_section:
                        section_text = self.clean_text_section(section_text, clean_callback)
                    sections.append((len(sections) + 1, section_text))
                
                start = end
            
            return sections
    
    def find_nearest_sentence_end(self, text, position, direction='forward'):
        sentence_ends = ['.', '!', '?', ':', ';']
        
        if direction == 'forward':
            for i in range(position, min(position + 500, len(text))):
                if i < len(text) and text[i] in sentence_ends:
                    if i + 1 < len(text) and text[i + 1] == ' ':
                        return i + 1
                    elif i + 1 >= len(text):
                        return i
        else:
            for i in range(position, max(0, position - 500), -1):
                if i > 0 and text[i] in sentence_ends:
                    if i + 1 < len(text) and text[i + 1] == ' ':
                        return i + 1
                    else:
                        return i
        
        return position
    
    def get_profile(self):
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