# -*- coding: utf-8 -*-

"""
Виджет предпросмотра текста
"""

import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, 
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

class PreviewWidget(QWidget):
    """Виджет для предпросмотра текста"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections = []
        self.show_invisible_mode = False
        self.original_text = ""
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QTextEdit()
        title.setPlainText("Предпросмотр")
        title.setReadOnly(True)
        title.setMaximumHeight(50)
        title.setStyleSheet("QTextEdit { background-color: #f0f0f0; font-weight: bold; }")
        header_layout.addWidget(title)
        
        # Кнопка показа скрытых символов
        self.show_invisible_btn = QPushButton("🔍 Показать скрытые символы")
        self.show_invisible_btn.setCheckable(True)
        self.show_invisible_btn.toggled.connect(self.toggle_invisible_mode)
        self.show_invisible_btn.setMaximumWidth(200)
        header_layout.addWidget(self.show_invisible_btn)
        
        layout.addLayout(header_layout)
        
        # Вкладки для разделов
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Вкладка для исходного текста
        self.original_text_widget = QTextEdit()
        self.original_text_widget.setReadOnly(True)
        self.tab_widget.addTab(self.original_text_widget, "Исходный текст")
    
    def toggle_invisible_mode(self, checked):
        """Переключение режима показа скрытых символов"""
        self.show_invisible_mode = checked
        if checked:
            self.show_invisible_btn.setText("👁 Скрыть символы")
            self.update_all_texts_with_invisible()
        else:
            self.show_invisible_btn.setText("🔍 Показать скрытые символы")
            self.update_all_texts_normal()
    
    def show_invisible_chars(self, text):
        """
        Показать невидимые символы для отладки
        
        Args:
            text: исходный текст
            
        Returns:
            текст с визуальным отображением скрытых символов
        """
        if not text:
            return text
        
        # Заменяем невидимые символы на визуальные представления
        replacements = {
            '\uFEFF': '[BOM]',      # byte order mark
            '\u2000': '[ENQ]',      # en quad
            '\u2001': '[EMQ]',      # em quad
            '\u2002': '[ENS]',      # en space
            '\u2003': '[EMS]',      # em space
            '\u2004': '[3EMS]',     # three-per-em space
            '\u2005': '[4EMS]',     # four-per-em space
            '\u2006': '[6EMS]',     # six-per-em space
            '\u2007': '[FS]',       # figure space
            '\u2008': '[PS]',       # punctuation space
            '\u2009': '[TS]',       # thin space
            '\u200A': '[HS]',       # hair space
            '\u202F': '[NNS]',      # narrow no-break space
            '\u205F': '[MMS]',      # medium mathematical space
            '\u3000': '[IS]',       # ideographic space
            ' ': '·',               # обычный пробел
            '\u00A0': '␣',         # неразрывный пробел
            '\t': '→→',            # табуляция
            '\n': '↵\n',           # перевод строки
            '\r': '←',             # возврат каретки
            '\u200B': '[ZWSP]',    # zero width space
            '\u200C': '[ZWNJ]',    # zero width non-joiner
            '\u200D': '[ZWJ]',     # zero width joiner
            '\u200E': '[LRM]',     # left-to-right mark
            '\u200F': '[RLM]',     # right-to-left mark
            '\u202A': '[LRE]',     # left-to-right embedding
            '\u202B': '[RLE]',     # right-to-left embedding
            '\u202C': '[PDF]',     # pop directional formatting
            '\u202D': '[LRO]',     # left-to-right override
            '\u202E': '[RLO]',     # right-to-left override
            '\u2060': '[WJ]',      # word joiner
            '\u00AD': '[SHY]',     # soft hyphen
        }
        
        result = text
        for char, replacement in replacements.items():
            if char in result:
                result = result.replace(char, replacement)
        
        # Добавляем подсветку для управляющих символов
        control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
        result = control_chars.sub(lambda m: f'[CTRL:{ord(m.group(0)):02X}]', result)
        
        return result
    
    def set_original_text(self, text):
        """Установить исходный текст"""
        self.original_text = text
        if self.show_invisible_mode:
            self.update_all_texts_with_invisible()
        else:
            self.update_all_texts_normal()
    
    def set_sections(self, sections):
        """Установить разделы для предпросмотра"""
        self.sections = sections
        
        # Удаляем старые вкладки, кроме первой
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        
        # Добавляем вкладки для разделов
        for section_num, content in sections:
            if content:
                text_widget = QTextEdit()
                if self.show_invisible_mode:
                    text_widget.setPlainText(self.show_invisible_chars(content))
                else:
                    text_widget.setPlainText(content)
                text_widget.setReadOnly(True)
                self.tab_widget.addTab(text_widget, f"Раздел {section_num}")
    
    def update_all_texts_with_invisible(self):
        """Обновить все тексты с показом скрытых символов"""
        # Обновляем исходный текст
        if hasattr(self, 'original_text') and self.original_text:
            self.original_text_widget.setPlainText(
                self.show_invisible_chars(self.original_text)
            )
        
        # Обновляем разделы
        for i in range(1, self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i-1 < len(self.sections):
                section_num, content = self.sections[i-1]
                if content:
                    widget.setPlainText(self.show_invisible_chars(content))
    
    def update_all_texts_normal(self):
        """Обновить все тексты в обычном режиме"""
        # Обновляем исходный текст
        if hasattr(self, 'original_text') and self.original_text:
            self.original_text_widget.setPlainText(self.original_text)
        
        # Обновляем разделы
        for i in range(1, self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i-1 < len(self.sections):
                section_num, content = self.sections[i-1]
                if content:
                    widget.setPlainText(content)