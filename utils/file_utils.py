# -*- coding: utf-8 -*-

"""
Утилиты для работы с файлами
"""

import os

def get_file_info(filepath):
    """
    Получить информацию о файле
    
    Args:
        filepath: путь к файлу
        
    Returns:
        словарь с информацией о файле
    """
    if not os.path.exists(filepath):
        return None
    
    stat = os.stat(filepath)
    
    return {
        'name': os.path.basename(filepath),
        'size': stat.st_size,
        'modified': stat.st_mtime
    }

def ensure_dir(directory):
    """
    Создать директорию, если её нет
    
    Args:
        directory: путь к директории
    """
    os.makedirs(directory, exist_ok=True)