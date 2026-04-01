# -*- coding: utf-8 -*-

"""
Виджет для отображения лога
"""

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt
from datetime import datetime

class LogWidget(QTextEdit):
    """Виджет лога сообщений"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.setStyleSheet("QTextEdit { background-color: #2b2b2b; color: #ffffff; font-family: monospace; }")
        self.add_message("Лог готов к работе")
    
    def add_message(self, message):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f"[{timestamp}] {message}")
        # Прокручиваем вниз
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def clear(self):
        """Очистить лог"""
        super().clear()
        self.add_message("Лог очищен")