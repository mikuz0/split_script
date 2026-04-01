# -*- coding: utf-8 -*-

"""
Панель настроек обработки
"""

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox,
    QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QListWidget, QListWidgetItem, QComboBox, QMessageBox,
    QFileDialog, QSplitter
)
from PyQt5.QtCore import pyqtSignal, Qt

class SettingsPanel(QWidget):
    """Панель настроек"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profiles_dir = "profiles"
        self.current_profile = None
        self.init_ui()
        self.load_default_profile()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Группа: Маркеры разбиения
        markers_group = QGroupBox("Маркеры разбиения")
        markers_layout = QVBoxLayout(markers_group)
        
        # Выбор предустановленного маркера
        markers_layout.addWidget(QLabel("Предустановленные маркеры:"))
        
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Цифры с точкой (1., 2., ...)", r'^\s*(\d+)\.\s*')
        self.preset_combo.addItem("Цифры с точкой и пробелом", r'^\s*(\d+)\.\s+')
        self.preset_combo.addItem("Римские цифры (I., II., ...)", r'^\s*([IVX]+)\.\s*')
        self.preset_combo.addItem("Буквы (А., Б., ...)", r'^\s*([А-Я])\.\s*')
        self.preset_combo.addItem("Произвольный regex", r'')
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        load_preset_btn = QPushButton("Применить")
        load_preset_btn.clicked.connect(self.apply_preset)
        preset_layout.addWidget(load_preset_btn)
        
        markers_layout.addLayout(preset_layout)
        
        # Редактирование шаблона
        markers_layout.addWidget(QLabel("Шаблон маркера (regex):"))
        self.marker_pattern_edit = QLineEdit()
        self.marker_pattern_edit.textChanged.connect(self.on_settings_changed)
        markers_layout.addWidget(self.marker_pattern_edit)
        
        # Описание маркера
        markers_layout.addWidget(QLabel("Описание:"))
        self.marker_desc_edit = QLineEdit()
        self.marker_desc_edit.textChanged.connect(self.on_settings_changed)
        markers_layout.addWidget(self.marker_desc_edit)
        
        layout.addWidget(markers_group)
        
        # Группа: Удаление содержимого
        brackets_group = QGroupBox("Удаление содержимого")
        brackets_layout = QVBoxLayout(brackets_group)
        
        self.remove_brackets_cb = QCheckBox("Удалять содержимое в скобках")
        self.remove_brackets_cb.setChecked(True)
        self.remove_brackets_cb.toggled.connect(self.on_settings_changed)
        brackets_layout.addWidget(self.remove_brackets_cb)
        
        # Горизонтальный сплиттер для скобок и символов
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть: пары скобок
        brackets_widget = QWidget()
        brackets_widget_layout = QVBoxLayout(brackets_widget)
        brackets_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        brackets_widget_layout.addWidget(QLabel("Пары скобок для удаления:"))
        
        brackets_list_layout = QHBoxLayout()
        
        self.brackets_list = QListWidget()
        self.brackets_list.setMaximumHeight(120)
        # Добавляем скобки по умолчанию
        item = QListWidgetItem("()")
        self.brackets_list.addItem(item)
        brackets_list_layout.addWidget(self.brackets_list)
        
        brackets_buttons_layout = QVBoxLayout()
        
        self.add_bracket_btn = QPushButton("+")
        self.add_bracket_btn.setMaximumWidth(30)
        self.add_bracket_btn.clicked.connect(self.add_bracket_pair)
        brackets_buttons_layout.addWidget(self.add_bracket_btn)
        
        self.remove_bracket_btn = QPushButton("-")
        self.remove_bracket_btn.setMaximumWidth(30)
        self.remove_bracket_btn.clicked.connect(self.remove_bracket_pair)
        brackets_buttons_layout.addWidget(self.remove_bracket_btn)
        
        brackets_list_layout.addLayout(brackets_buttons_layout)
        brackets_widget_layout.addLayout(brackets_list_layout)
        
        # Поле для добавления новой пары
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Добавить:"))
        self.new_bracket_pair = QLineEdit()
        self.new_bracket_pair.setPlaceholderText("например: []")
        add_layout.addWidget(self.new_bracket_pair)
        
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_bracket_pair)
        add_layout.addWidget(add_btn)
        
        brackets_widget_layout.addLayout(add_layout)
        
        # Правая часть: символы для удаления
        chars_widget = QWidget()
        chars_widget_layout = QVBoxLayout(chars_widget)
        chars_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        chars_widget_layout.addWidget(QLabel("Символы для удаления:"))
        
        self.chars_list = QListWidget()
        self.chars_list.setMaximumHeight(120)
        chars_widget_layout.addWidget(self.chars_list)
        
        chars_buttons_layout = QHBoxLayout()
        
        self.add_char_btn = QPushButton("+ Добавить символ")
        self.add_char_btn.clicked.connect(self.add_char)
        chars_buttons_layout.addWidget(self.add_char_btn)
        
        self.remove_char_btn = QPushButton("- Удалить")
        self.remove_char_btn.clicked.connect(self.remove_char)
        chars_buttons_layout.addWidget(self.remove_char_btn)
        
        chars_widget_layout.addLayout(chars_buttons_layout)
        
        # Поле для добавления символа
        char_add_layout = QHBoxLayout()
        char_add_layout.addWidget(QLabel("Символ:"))
        self.new_char = QLineEdit()
        self.new_char.setMaxLength(1)
        self.new_char.setPlaceholderText("один символ")
        char_add_layout.addWidget(self.new_char)
        
        char_add_btn = QPushButton("Добавить")
        char_add_btn.clicked.connect(self.add_char)
        char_add_layout.addWidget(char_add_btn)
        
        chars_widget_layout.addLayout(char_add_layout)
        
        # Добавляем оба виджета в сплиттер
        splitter.addWidget(brackets_widget)
        splitter.addWidget(chars_widget)
        
        # Устанавливаем пропорции (1:1 - одинаково)
        splitter.setSizes([200, 200])
        
        brackets_layout.addWidget(splitter)
        
        layout.addWidget(brackets_group)
        
        # Группа: Очистка текста
        cleaning_group = QGroupBox("Очистка текста")
        cleaning_layout = QVBoxLayout(cleaning_group)
        
        self.remove_spaces_cb = QCheckBox("Удалять лишние пробелы")
        self.remove_spaces_cb.setChecked(True)
        self.remove_spaces_cb.toggled.connect(self.on_settings_changed)
        cleaning_layout.addWidget(self.remove_spaces_cb)
        
        self.normalize_punctuation_cb = QCheckBox("Нормализовать знаки препинания")
        self.normalize_punctuation_cb.setChecked(True)
        self.normalize_punctuation_cb.toggled.connect(self.on_settings_changed)
        cleaning_layout.addWidget(self.normalize_punctuation_cb)
        
        self.remove_invisible_cb = QCheckBox("Удалять скрытые символы (невидимые, управляющие)")
        self.remove_invisible_cb.setChecked(True)
        self.remove_invisible_cb.toggled.connect(self.on_settings_changed)
        cleaning_layout.addWidget(self.remove_invisible_cb)
        
        layout.addWidget(cleaning_group)
        
        # Группа: Папка для результатов
        output_group = QGroupBox("Папка для результатов")
        output_layout = QVBoxLayout(output_group)
        
        output_path_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Папка для сохранения файлов...")
        self.output_dir_edit.textChanged.connect(self.on_settings_changed)
        output_path_layout.addWidget(self.output_dir_edit)
        
        browse_output_btn = QPushButton("Обзор...")
        browse_output_btn.clicked.connect(self.browse_output_dir)
        output_path_layout.addWidget(browse_output_btn)
        
        output_layout.addLayout(output_path_layout)
        
        layout.addWidget(output_group)
        
        # Группа: Профили
        profiles_group = QGroupBox("Профили")
        profiles_layout = QVBoxLayout(profiles_group)
        
        # Выбор профиля
        profile_select_layout = QHBoxLayout()
        profile_select_layout.addWidget(QLabel("Загрузить профиль:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        profile_select_layout.addWidget(self.profile_combo)
        
        profiles_layout.addLayout(profile_select_layout)
        
        # Кнопки управления профилями
        profile_buttons_layout = QHBoxLayout()
        
        self.save_profile_btn = QPushButton("Сохранить профиль")
        self.save_profile_btn.clicked.connect(self.save_profile)
        profile_buttons_layout.addWidget(self.save_profile_btn)
        
        self.delete_profile_btn = QPushButton("Удалить профиль")
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        profile_buttons_layout.addWidget(self.delete_profile_btn)
        
        profiles_layout.addLayout(profile_buttons_layout)
        
        layout.addWidget(profiles_group)
        
        layout.addStretch()
        
        # Загружаем список профилей
        self.load_profiles_list()
    
    def browse_output_dir(self):
        """Выбрать папку для результатов"""
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения результатов"
        )
        
        if output_dir:
            self.output_dir_edit.setText(output_dir)
    
    def on_preset_changed(self, index):
        """Обработчик выбора предустановки"""
        pattern = self.preset_combo.itemData(index)
        if pattern:
            self.marker_pattern_edit.setText(pattern)
    
    def apply_preset(self):
        """Применить выбранную предустановку"""
        self.on_settings_changed()
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        self.settings_changed.emit()
    
    def add_bracket_pair(self):
        """Добавить пару скобок"""
        new_pair = self.new_bracket_pair.text().strip()
        if new_pair and len(new_pair) == 2:
            # Проверяем, нет ли уже такой пары
            items = [self.brackets_list.item(i).text() for i in range(self.brackets_list.count())]
            if new_pair not in items:
                self.brackets_list.addItem(new_pair)
                self.new_bracket_pair.clear()
                self.on_settings_changed()
    
    def remove_bracket_pair(self):
        """Удалить пару скобок"""
        current_row = self.brackets_list.currentRow()
        if current_row >= 0:
            self.brackets_list.takeItem(current_row)
            self.on_settings_changed()
    
    def add_char(self):
        """Добавить символ для удаления"""
        new_char = self.new_char.text().strip()
        if new_char and len(new_char) == 1:
            # Проверяем, нет ли уже такого символа
            items = [self.chars_list.item(i).text() for i in range(self.chars_list.count())]
            if new_char not in items:
                self.chars_list.addItem(new_char)
                self.new_char.clear()
                self.on_settings_changed()
    
    def remove_char(self):
        """Удалить символ из списка"""
        current_row = self.chars_list.currentRow()
        if current_row >= 0:
            self.chars_list.takeItem(current_row)
            self.on_settings_changed()
    
    def get_settings(self):
        """Получить текущие настройки"""
        bracket_pairs = []
        for i in range(self.brackets_list.count()):
            bracket_pairs.append(self.brackets_list.item(i).text())
        
        chars_to_remove = []
        for i in range(self.chars_list.count()):
            chars_to_remove.append(self.chars_list.item(i).text())
        
        return {
            'marker_pattern': self.marker_pattern_edit.text(),
            'marker_description': self.marker_desc_edit.text(),
            'remove_brackets': self.remove_brackets_cb.isChecked(),
            'bracket_pairs': bracket_pairs,
            'remove_spaces': self.remove_spaces_cb.isChecked(),
            'normalize_punctuation': self.normalize_punctuation_cb.isChecked(),
            'chars_to_remove': chars_to_remove,
            'remove_invisible': self.remove_invisible_cb.isChecked(),
            'output_dir': self.output_dir_edit.text()
        }
    
    def set_settings(self, settings):
        """Установить настройки"""
        if 'marker_pattern' in settings:
            self.marker_pattern_edit.setText(settings['marker_pattern'])
        if 'marker_description' in settings:
            self.marker_desc_edit.setText(settings['marker_description'])
        if 'remove_brackets' in settings:
            self.remove_brackets_cb.setChecked(settings['remove_brackets'])
        if 'bracket_pairs' in settings:
            self.brackets_list.clear()
            for pair in settings['bracket_pairs']:
                self.brackets_list.addItem(pair)
        if 'remove_spaces' in settings:
            self.remove_spaces_cb.setChecked(settings['remove_spaces'])
        if 'normalize_punctuation' in settings:
            self.normalize_punctuation_cb.setChecked(settings['normalize_punctuation'])
        if 'chars_to_remove' in settings:
            self.chars_list.clear()
            for char in settings['chars_to_remove']:
                self.chars_list.addItem(char)
        if 'remove_invisible' in settings:
            self.remove_invisible_cb.setChecked(settings['remove_invisible'])
        if 'output_dir' in settings:
            self.output_dir_edit.setText(settings['output_dir'])
        
        self.on_settings_changed()
    
    def load_default_profile(self):
        """Загрузить профиль по умолчанию"""
        default_settings = {
            'marker_pattern': r'^\s*(\d+)\.\s*',
            'marker_description': 'Цифры с точкой (1., 2., ...)',
            'remove_brackets': True,
            'bracket_pairs': ['()'],
            'remove_spaces': True,
            'normalize_punctuation': True,
            'chars_to_remove': [],
            'remove_invisible': True,
            'output_dir': ''
        }
        self.set_settings(default_settings)
    
    def load_profiles_list(self):
        """Загрузить список профилей"""
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Выберите профиль --", "")
        
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
            return
        
        profiles = [f for f in os.listdir(self.profiles_dir) if f.endswith('.json')]
        for profile in sorted(profiles):
            profile_name = os.path.splitext(profile)[0]
            self.profile_combo.addItem(profile_name, os.path.join(self.profiles_dir, profile))
    
    def on_profile_selected(self, index):
        """Обработчик выбора профиля"""
        if index > 0:  # Пропускаем первый элемент "-- Выберите профиль --"
            profile_path = self.profile_combo.itemData(index)
            if profile_path and os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    self.set_settings(settings)
                    self.current_profile = profile_path
                    QMessageBox.information(
                        self, "Профиль загружен",
                        f"Профиль '{self.profile_combo.currentText()}' успешно загружен"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить профиль: {e}")
    
    def save_profile(self):
        """Сохранить профиль"""
        from PyQt5.QtWidgets import QInputDialog
        
        profile_name, ok = QInputDialog.getText(
            self, "Сохранить профиль",
            "Введите имя профиля:"
        )
        
        if ok and profile_name:
            if not os.path.exists(self.profiles_dir):
                os.makedirs(self.profiles_dir)
            
            profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            # Проверяем, существует ли уже такой профиль
            if os.path.exists(profile_path):
                reply = QMessageBox.question(
                    self, "Профиль существует",
                    f"Профиль '{profile_name}' уже существует. Перезаписать?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            try:
                settings = self.get_settings()
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                
                self.load_profiles_list()
                
                # Выбираем сохраненный профиль в списке
                for i in range(self.profile_combo.count()):
                    if self.profile_combo.itemText(i) == profile_name:
                        self.profile_combo.setCurrentIndex(i)
                        break
                
                QMessageBox.information(
                    self, "Профиль сохранен",
                    f"Профиль '{profile_name}' успешно сохранен"
                )
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить профиль: {e}")
    
    def delete_profile(self):
        """Удалить профиль"""
        current_index = self.profile_combo.currentIndex()
        if current_index > 0:  # Не удаляем заглушку
            profile_name = self.profile_combo.currentText()
            profile_path = self.profile_combo.itemData(current_index)
            
            reply = QMessageBox.question(
                self, "Удалить профиль",
                f"Вы уверены, что хотите удалить профиль '{profile_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    os.remove(profile_path)
                    self.load_profiles_list()
                    QMessageBox.information(
                        self, "Профиль удален",
                        f"Профиль '{profile_name}' успешно удален"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить профиль: {e}")
    
    def create_cleanup_profile(self):
        """Создать профиль для агрессивной очистки"""
        cleanup_settings = {
            'marker_pattern': r'^\s*(\d+)\.\s*',
            'marker_description': 'Цифры с точкой (1., 2., ...)',
            'remove_brackets': True,
            'bracket_pairs': ['()', '[]', '{}', '«»', '“”', '""', "''"],
            'remove_spaces': True,
            'normalize_punctuation': True,
            'chars_to_remove': ['¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '⁰', '†', '‡', '*'],
            'remove_invisible': True,
            'output_dir': ''
        }
        return cleanup_settings