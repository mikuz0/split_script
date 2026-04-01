# -*- coding: utf-8 -*-

"""
Диалоговое окно "О программе"
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class AboutDialog(QDialog):
    """Диалог о программе"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Название
        title = QLabel("Text Splitter")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Версия
        version = QLabel("Версия 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # Описание
        desc = QLabel(
            "Программа для разбиения текстовых файлов на отдельные файлы\n"
            "по заданным маркерам с возможностью очистки текста."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)