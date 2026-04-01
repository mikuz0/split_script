#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль приложения для разбиения текста на файлы
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Добавляем пути для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    app.setApplicationName("Text Splitter")
    app.setOrganizationName("SplitScript")
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()