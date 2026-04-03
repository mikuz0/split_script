# -*- coding: utf-8 -*-

"""
Диалог для ручной корректировки границ разделов
"""

import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton,
    QLabel, QSpinBox, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor

class ManualSplitEditor(QDialog):
    """Диалог для ручной корректировки границ разделов"""
    
    sections_updated = pyqtSignal(list)
    
    def __init__(self, original_text, sections, parent=None):
        super().__init__(parent)
        self.original_text = original_text
        self.original_sections = sections.copy()
        self.sections = sections.copy()
        self.split_positions = []
        self.current_section_index = 0
        self.updating = False
        self.pending_update = False
        self.init_ui()
        self.update_display()
    
    def init_ui(self):
        self.setWindowTitle("Ручная корректировка границ разделов")
        self.setGeometry(200, 200, 1000, 700)
        
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Разделы:"))
        
        self.sections_list = QListWidget()
        self.sections_list.itemClicked.connect(self.on_section_selected)
        left_layout.addWidget(self.sections_list)
        
        buttons_layout = QHBoxLayout()
        self.merge_btn = QPushButton("Объединить с предыдущим")
        self.merge_btn.clicked.connect(self.merge_with_previous)
        buttons_layout.addWidget(self.merge_btn)
        
        self.merge_next_btn = QPushButton("Объединить со следующим")
        self.merge_next_btn.clicked.connect(self.merge_with_next)
        buttons_layout.addWidget(self.merge_next_btn)
        
        left_layout.addLayout(buttons_layout)
        splitter.addWidget(left_widget)
        
        # Правая панель
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("Текст (зеленые зоны - разделы, красные линии - границы):"))
        
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.text_edit)
        
        # Панель навигации
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("Перейти к разделу:"))
        
        self.section_spin = QSpinBox()
        self.section_spin.setMinimum(1)
        self.section_spin.valueChanged.connect(self.go_to_section)
        nav_layout.addWidget(self.section_spin)
        
        nav_layout.addStretch()
        
        self.add_boundary_btn = QPushButton("➕ Добавить границу в позиции курсора")
        self.add_boundary_btn.clicked.connect(self.add_boundary_at_cursor)
        nav_layout.addWidget(self.add_boundary_btn)
        
        right_layout.addLayout(nav_layout)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        # Нижняя панель
        bottom_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Сбросить изменения")
        self.reset_btn.clicked.connect(self.reset_changes)
        bottom_layout.addWidget(self.reset_btn)
        
        bottom_layout.addStretch()
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("Применить")
        self.ok_btn.clicked.connect(self.apply_changes)
        bottom_layout.addWidget(self.ok_btn)
        
        layout.addLayout(bottom_layout)
    
    def update_display(self):
        """Обновить отображение списка разделов и текста"""
        if self.updating:
            return
        
        self.updating = True
        
        # Обновляем список разделов
        self.sections_list.clear()
        for i, (num, content) in enumerate(self.sections):
            preview = content[:50] + "..." if len(content) > 50 else content
            preview = preview.replace('\n', ' ')
            preview = preview.replace('\r', '')
            item = QListWidgetItem(f"{i+1}. {preview}")
            self.sections_list.addItem(item)
        
        # Обновляем спин-бокс
        self.section_spin.blockSignals(True)
        self.section_spin.setMaximum(max(1, len(self.sections)))
        self.section_spin.setValue(min(self.current_section_index + 1, len(self.sections)))
        self.section_spin.blockSignals(False)
        
        # Обновляем текст в обычном режиме (не HTML)
        self.update_plain_text_display()
        
        self.updating = False
    
    def update_plain_text_display(self):
        """Обновить отображение текста в обычном режиме (без HTML)"""
        if not self.sections:
            self.text_edit.blockSignals(True)
            self.text_edit.setPlainText("Нет разделов для отображения")
            self.text_edit.blockSignals(False)
            return
        
        # Собираем весь текст с разделителями
        full_text_parts = []
        for i, (num, content) in enumerate(self.sections):
            full_text_parts.append(content)
            if i < len(self.sections) - 1:
                full_text_parts.append("\n\n══════ ГРАНИЦА РАЗДЕЛА ══════\n\n")
        
        full_text = ''.join(full_text_parts)
        
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(full_text)
        self.text_edit.blockSignals(False)
    
    def highlight_current_section(self):
        """Подсветить текущий раздел (без изменения текста)"""
        if not self.sections:
            return
        
        # Находим позиции
        start_pos = 0
        for i in range(self.current_section_index):
            start_pos += len(self.sections[i][1]) + 18
        
        end_pos = start_pos + len(self.sections[self.current_section_index][1])
        
        # Выделяем текст
        cursor = self.text_edit.textCursor()
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
        self.text_edit.setTextCursor(cursor)
    
    def on_section_selected(self, item):
        if self.updating:
            return
        index = self.sections_list.row(item)
        self.current_section_index = index
        self.update_display()
        # После обновления выделяем текущий раздел
        QTimer.singleShot(100, self.highlight_current_section)
    
    def go_to_section(self, value):
        if self.updating:
            return
        self.current_section_index = value - 1
        self.sections_list.setCurrentRow(self.current_section_index)
        self.update_display()
        QTimer.singleShot(100, self.highlight_current_section)
    
    def on_text_changed(self):
        """Обработчик изменения текста пользователем"""
        if self.updating:
            return
        
        # Получаем текст
        plain_text = self.text_edit.toPlainText()
        
        # Разбиваем по разделителям
        parts = plain_text.split("══════ ГРАНИЦА РАЗДЕЛА ══════")
        
        new_sections = []
        for i, part in enumerate(parts):
            content = part.strip()
            if content:
                new_sections.append((i + 1, content))
        
        if new_sections and new_sections != self.sections:
            self.updating = True
            self.sections = new_sections
            # Обновляем нумерацию
            for i, (num, content) in enumerate(self.sections):
                self.sections[i] = (i + 1, content)
            
            # Обновляем список
            self.sections_list.clear()
            for i, (num, content) in enumerate(self.sections):
                preview = content[:50] + "..." if len(content) > 50 else content
                preview = preview.replace('\n', ' ')
                preview = preview.replace('\r', '')
                item = QListWidgetItem(f"{i+1}. {preview}")
                self.sections_list.addItem(item)
            
            # Обновляем спин-бокс
            self.section_spin.blockSignals(True)
            self.section_spin.setMaximum(max(1, len(self.sections)))
            if self.current_section_index >= len(self.sections):
                self.current_section_index = max(0, len(self.sections) - 1)
            self.section_spin.setValue(self.current_section_index + 1)
            self.section_spin.blockSignals(False)
            
            self.updating = False
    
    def add_boundary_at_cursor(self):
        """Добавить границу в позиции курсора"""
        if self.updating:
            return
        
        cursor = self.text_edit.textCursor()
        cursor.insertText("\n\n══════ ГРАНИЦА РАЗДЕЛА ══════\n\n")
        
        # Обновляем разделы
        plain_text = self.text_edit.toPlainText()
        parts = plain_text.split("══════ ГРАНИЦА РАЗДЕЛА ══════")
        
        new_sections = []
        for i, part in enumerate(parts):
            content = part.strip()
            if content:
                new_sections.append((i + 1, content))
        
        if new_sections:
            self.updating = True
            self.sections = new_sections
            for i, (num, content) in enumerate(self.sections):
                self.sections[i] = (i + 1, content)
            
            self.sections_list.clear()
            for i, (num, content) in enumerate(self.sections):
                preview = content[:50] + "..." if len(content) > 50 else content
                preview = preview.replace('\n', ' ')
                preview = preview.replace('\r', '')
                item = QListWidgetItem(f"{i+1}. {preview}")
                self.sections_list.addItem(item)
            
            self.section_spin.blockSignals(True)
            self.section_spin.setMaximum(max(1, len(self.sections)))
            self.section_spin.setValue(min(self.current_section_index + 1, len(self.sections)))
            self.section_spin.blockSignals(False)
            
            self.updating = False
    
    def merge_with_previous(self):
        if self.updating:
            return
        
        if self.current_section_index > 0:
            self.updating = True
            
            prev_content = self.sections[self.current_section_index - 1][1]
            curr_content = self.sections[self.current_section_index][1]
            merged_content = prev_content + "\n\n" + curr_content
            
            new_sections = self.sections[:self.current_section_index - 1]
            new_sections.append((self.current_section_index, merged_content))
            new_sections.extend(self.sections[self.current_section_index + 1:])
            
            for i, (num, content) in enumerate(new_sections):
                new_sections[i] = (i + 1, content)
            
            self.sections = new_sections
            self.current_section_index = max(0, self.current_section_index - 1)
            self.update_display()
            
            self.updating = False
    
    def merge_with_next(self):
        if self.updating:
            return
        
        if self.current_section_index < len(self.sections) - 1:
            self.updating = True
            
            curr_content = self.sections[self.current_section_index][1]
            next_content = self.sections[self.current_section_index + 1][1]
            merged_content = curr_content + "\n\n" + next_content
            
            new_sections = self.sections[:self.current_section_index]
            new_sections.append((self.current_section_index + 1, merged_content))
            new_sections.extend(self.sections[self.current_section_index + 2:])
            
            for i, (num, content) in enumerate(new_sections):
                new_sections[i] = (i + 1, content)
            
            self.sections = new_sections
            self.update_display()
            
            self.updating = False
    
    def reset_changes(self):
        if self.updating:
            return
        
        self.updating = True
        self.sections = self.original_sections.copy()
        self.current_section_index = 0
        self.update_display()
        self.updating = False
        
        QMessageBox.information(self, "Сброшено", "Изменения сброшены к исходному состоянию")
    
    def apply_changes(self):
        self.sections_updated.emit(self.sections)
        self.accept()