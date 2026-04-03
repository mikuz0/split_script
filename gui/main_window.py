# -*- coding: utf-8 -*-

"""
Главное окно приложения
"""

import os
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QApplication,
    QButtonGroup, QRadioButton, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from core.file_splitter import FileSplitter
from core.text_processor import TextProcessor
from gui.widgets.preview_widget import PreviewWidget
from gui.widgets.settings_panel import SettingsPanel
from gui.widgets.log_widget import LogWidget
from gui.dialogs.about_dialog import AboutDialog
from gui.dialogs.manual_split_editor import ManualSplitEditor

class SplitWorker(QThread):
    """Рабочий поток для разбиения файла"""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, filepath, output_dir, settings, mode='split', manual_sections=None):
        super().__init__()
        self.filepath = filepath
        self.output_dir = output_dir
        self.settings = settings
        self.mode = mode
        self.manual_sections = manual_sections  # Предварительно отредактированные разделы
    
    def run(self):
        try:
            splitter = FileSplitter()
            
            splitter.set_processor_config(settings=self.settings)
            
            if self.mode == 'split':
                # Если есть вручную отредактированные разделы, используем их
                if self.manual_sections:
                    # Очищаем каждый раздел в соответствии с настройками
                    cleaned_sections = []
                    for i, (num, content) in enumerate(self.manual_sections):
                        cleaned_content = splitter.text_processor.clean_text_section(content, self.log.emit)
                        cleaned_sections.append((i + 1, cleaned_content))
                    
                    # Сохраняем разделы
                    created_files = splitter.save_sections(
                        cleaned_sections,
                        self.filepath,
                        self.output_dir,
                        self.progress.emit
                    )
                    self.finished.emit(created_files)
                    return
                
                # Иначе выполняем автоматическое разбиение
                split_config = self.settings.get('split_config', {})
                method = split_config.get('method', 'regex')
                
                if method == 'manual':
                    splitter.set_split_config(
                        method='manual',
                        markers=split_config.get('markers', []),
                        keep_markers=split_config.get('keep_markers', False),
                        case_sensitive=split_config.get('case_sensitive', False)
                    )
                elif method == 'length':
                    splitter.set_split_config(
                        method='length',
                        length=split_config.get('length', 5000),
                        unit=split_config.get('unit', 'chars'),
                        smart=split_config.get('smart', True),
                        keep_paragraphs=split_config.get('keep_paragraphs', True)
                    )
                else:
                    splitter.set_split_config(method='regex')
                
                text = splitter.load_file(self.filepath)
                
                processor = TextProcessor()
                processor.set_remove_invisible(True)
                invisible_info = processor.get_invisible_chars_info(text)
                
                if invisible_info['has_invisible']:
                    self.log.emit("⚠️ ВНИМАНИЕ: Обнаружены скрытые символы в тексте!")
                    for sample in invisible_info['samples']:
                        self.log.emit(f"   - {sample['name']} ({sample['code']})")
                
                sections = splitter.split_text(text, clean_callback=self.log.emit)
                
                if not sections:
                    self.error.emit("Не удалось разбить текст (нет разделителей)")
                    return
                
                created_files = splitter.save_sections(
                    sections,
                    self.filepath,
                    self.output_dir,
                    self.progress.emit
                )
                self.finished.emit(created_files)
                
            else:  # mode == 'clean'
                splitter.set_split_config(method='regex')
                text = splitter.load_file(self.filepath)
                
                processor = TextProcessor()
                processor.set_remove_invisible(True)
                invisible_info = processor.get_invisible_chars_info(text)
                
                if invisible_info['has_invisible']:
                    self.log.emit("⚠️ ВНИМАНИЕ: Обнаружены скрытые символы в тексте!")
                    for sample in invisible_info['samples']:
                        self.log.emit(f"   - {sample['name']} ({sample['code']})")
                
                cleaned_text = splitter.clean_whole_file(text, clean_callback=self.log.emit)
                output_file = splitter.save_cleaned_file(
                    cleaned_text,
                    self.filepath,
                    self.output_dir
                )
                self.progress.emit(1, 1, output_file)
                self.finished.emit([output_file])
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.output_dir = None
        self.worker = None
        self.current_mode = 'split'
        self.current_sections = None  # Хранит текущие разделы (авто или ручные)
        self.has_manual_edits = False  # Флаг, что были ручные правки
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Text Splitter - Разбиение и очистка текста")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        top_panel = self.create_top_panel()
        main_layout.addLayout(top_panel)
        
        mode_panel = self.create_mode_panel()
        main_layout.addLayout(mode_panel)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.preview_widget = PreviewWidget()
        splitter.addWidget(self.preview_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.on_settings_changed)
        right_layout.addWidget(self.settings_panel)
        
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        bottom_panel = self.create_bottom_panel()
        main_layout.addLayout(bottom_panel)
        
        self.statusBar().showMessage("Готов")
    
    def create_mode_panel(self):
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Режим работы:"))
        
        self.mode_group = QButtonGroup(self)
        
        self.split_radio = QRadioButton("Разбить на файлы")
        self.split_radio.setChecked(True)
        self.split_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.split_radio)
        layout.addWidget(self.split_radio)
        
        self.clean_radio = QRadioButton("Простая очистка (без разбиения)")
        self.clean_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.clean_radio)
        layout.addWidget(self.clean_radio)
        
        layout.addStretch()
        
        return layout
    
    def create_top_panel(self):
        layout = QHBoxLayout()
        
        self.open_btn = self.create_button("Открыть файл", self.open_file)
        layout.addWidget(self.open_btn)
        
        self.file_path_label = self.create_label("Файл не выбран")
        layout.addWidget(self.file_path_label)
        
        layout.addStretch()
        
        self.output_btn = self.create_button("Папка сохранения", self.select_output_dir)
        layout.addWidget(self.output_btn)
        
        self.output_path_label = self.create_label("Не выбрана")
        layout.addWidget(self.output_path_label)
        
        return layout
    
    def create_bottom_panel(self):
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        self.manual_edit_btn = self.create_button("✏️ Ручная корректировка границ", self.manual_edit)
        self.manual_edit_btn.setEnabled(False)
        layout.addWidget(self.manual_edit_btn)
        
        self.reset_manual_btn = self.create_button("🔄 Сбросить ручную разбивку", self.reset_manual_split)
        self.reset_manual_btn.setEnabled(False)
        layout.addWidget(self.reset_manual_btn)
        
        self.run_btn = self.create_button("Выполнить", self.run_split)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        
        cleanup_btn = self.create_button("🧹 Создать профиль очистки", self.create_cleanup_profile)
        layout.addWidget(cleanup_btn)
        
        about_btn = self.create_button("О программе", self.show_about)
        layout.addWidget(about_btn)
        
        return layout
    
    def create_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn
    
    def create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("QLabel { color: #666; }")
        return label
    
    def on_mode_changed(self):
        if self.split_radio.isChecked():
            self.current_mode = 'split'
            self.statusBar().showMessage("Режим: разбиение на файлы")
        else:
            self.current_mode = 'clean'
            self.statusBar().showMessage("Режим: простая очистка текста")
        
        if self.current_file:
            self.on_settings_changed()
    
    def manual_edit(self):
        """Открыть диалог ручной корректировки границ"""
        if not self.current_sections:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите файл и выполните предпросмотр")
            return
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            editor = ManualSplitEditor(original_text, self.current_sections, self)
            editor.sections_updated.connect(self.on_sections_updated)
            editor.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор: {e}")
    
    def on_sections_updated(self, new_sections):
        """Обработчик обновления разделов из редактора"""
        self.current_sections = new_sections
        self.has_manual_edits = True
        self.preview_widget.set_sections(new_sections)
        self.log_widget.add_message("Границы разделов обновлены вручную")
        self.reset_manual_btn.setEnabled(True)
    
    def reset_manual_split(self):
        """Сбросить ручную разбивку и вернуться к автоматической"""
        self.has_manual_edits = False
        self.on_settings_changed()  # Пересоздаем автоматические разделы
        self.log_widget.add_message("Ручная разбивка сброшена, используется автоматическая")
        self.reset_manual_btn.setEnabled(False)
    
    def create_cleanup_profile(self):
        profile_name = "Очистка от мусора"
        profiles_dir = "profiles"
        
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        
        profile_path = os.path.join(profiles_dir, f"{profile_name}.json")
        
        cleanup_settings = {
            'split_config': {
                'method': 'regex',
                'marker_pattern': r'^\s*(\d+)\.\s*',
                'marker_description': 'Цифры с точкой (1., 2., ...)'
            },
            'remove_brackets': True,
            'bracket_pairs': ['()', '[]', '{}', '«»', '“”', '""', "''"],
            'remove_spaces': True,
            'normalize_punctuation': True,
            'chars_to_remove': ['¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '⁰', '†', '‡', '*', '§', '¶'],
            'remove_invisible': True,
            'output_dir': ''
        }
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(cleanup_settings, f, ensure_ascii=False, indent=2)
            
            self.settings_panel.load_profiles_list()
            self.settings_panel.set_settings(cleanup_settings)
            
            QMessageBox.information(
                self,
                "Профиль создан",
                f"Профиль '{profile_name}' успешно создан!"
            )
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать профиль: {e}")
    
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите текстовый файл",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if filepath:
            self.current_file = filepath
            self.file_path_label.setText(os.path.basename(filepath))
            self.has_manual_edits = False
            self.reset_manual_btn.setEnabled(False)
            self.statusBar().showMessage(f"Загружен файл: {filepath}")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                processor = TextProcessor()
                invisible_info = processor.get_invisible_chars_info(text)
                
                if invisible_info['has_invisible']:
                    self.log_widget.add_message("⚠️ ВНИМАНИЕ: Обнаружены скрытые символы в тексте!")
                    for sample in invisible_info['samples']:
                        self.log_widget.add_message(
                            f"   - {sample['name']} ({sample['code']})"
                        )
                    
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Обнаружены скрытые символы")
                    msg.setText("В загруженном файле обнаружены скрытые символы!\n\n"
                                "Они могут мешать правильной обработке текста.\n\n"
                                "Рекомендуется использовать профиль 'Очистка от мусора'.")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                
                self.preview_widget.set_original_text(text)
                self.check_run_enabled()
                self.on_settings_changed()  # Запускаем предпросмотр
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")
    
    def select_output_dir(self):
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения"
        )
        
        if output_dir:
            self.output_dir = output_dir
            self.output_path_label.setText(output_dir)
            settings = self.settings_panel.get_settings()
            settings['output_dir'] = output_dir
            self.settings_panel.set_settings(settings)
            self.check_run_enabled()
    
    def check_run_enabled(self):
        enabled = self.current_file is not None and self.output_dir is not None
        self.run_btn.setEnabled(enabled)
        self.manual_edit_btn.setEnabled(enabled and self.current_mode == 'split' and self.current_sections is not None)
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        if self.current_file:
            try:
                # Если есть ручные правки, не пересоздаем автоматические разделы
                if self.has_manual_edits:
                    self.preview_widget.set_sections(self.current_sections)
                    self.manual_edit_btn.setEnabled(True)
                    return
                
                splitter = FileSplitter()
                settings = self.settings_panel.get_settings()
                
                if 'output_dir' in settings and settings['output_dir']:
                    self.output_dir = settings['output_dir']
                    self.output_path_label.setText(settings['output_dir'])
                    self.check_run_enabled()
                
                splitter.set_processor_config(settings=settings)
                
                split_config = settings.get('split_config', {})
                method = split_config.get('method', 'regex')
                
                if method == 'manual':
                    splitter.set_split_config(
                        method='manual',
                        markers=split_config.get('markers', []),
                        keep_markers=split_config.get('keep_markers', False),
                        case_sensitive=split_config.get('case_sensitive', False)
                    )
                elif method == 'length':
                    splitter.set_split_config(
                        method='length',
                        length=split_config.get('length', 5000),
                        unit=split_config.get('unit', 'chars'),
                        smart=split_config.get('smart', True),
                        keep_paragraphs=split_config.get('keep_paragraphs', True)
                    )
                else:
                    splitter.set_split_config(method='regex')
                
                text = splitter.load_file(self.current_file)
                
                if self.current_mode == 'split':
                    sections = splitter.split_text(text, clean_callback=self.log_widget.add_message)
                    self.current_sections = sections
                    self.preview_widget.set_sections(sections)
                    self.manual_edit_btn.setEnabled(len(sections) > 0)
                else:
                    cleaned_text = splitter.clean_whole_file(text, clean_callback=self.log_widget.add_message)
                    self.preview_widget.set_sections([("Очищенный текст", cleaned_text)])
                    self.manual_edit_btn.setEnabled(False)
                
            except Exception as e:
                self.log_widget.add_message(f"Ошибка предпросмотра: {e}")
    
    def run_split(self):
        if not self.current_file or not self.output_dir:
            return
        
        settings = self.settings_panel.get_settings()
        
        self.log_widget.clear()
        self.run_btn.setEnabled(False)
        self.manual_edit_btn.setEnabled(False)
        self.reset_manual_btn.setEnabled(False)
        self.statusBar().showMessage("Обработка...")
        
        # Передаем в рабочий поток текущие разделы (с учетом ручных правок)
        sections_to_use = self.current_sections if self.has_manual_edits else None
        
        self.worker = SplitWorker(
            self.current_file,
            self.output_dir,
            settings,
            mode=self.current_mode,
            manual_sections=sections_to_use
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.log.connect(self.log_widget.add_message)
        self.worker.start()
    
    def on_progress(self, current, total, filepath):
        self.log_widget.add_message(f"Создан файл: {os.path.basename(filepath)}")
        self.statusBar().showMessage(f"Обработано {current} из {total}...")
    
    def on_finished(self, created_files):
        self.run_btn.setEnabled(True)
        
        if self.current_mode == 'split':
            self.statusBar().showMessage(f"Готово! Создано файлов: {len(created_files)}")
            self.log_widget.add_message(f"Обработка завершена. Создано {len(created_files)} файлов.")
            message = f"Разбиение завершено!\nСоздано файлов: {len(created_files)}\nПапка: {self.output_dir}"
            self.manual_edit_btn.setEnabled(True)
            if self.has_manual_edits:
                self.reset_manual_btn.setEnabled(True)
        else:
            self.statusBar().showMessage(f"Готово! Очищенный текст сохранен")
            self.log_widget.add_message(f"Очистка завершена. Файл сохранен: {os.path.basename(created_files[0])}")
            message = f"Очистка текста завершена!\nФайл сохранен: {os.path.basename(created_files[0])}\nПапка: {self.output_dir}"
            self.manual_edit_btn.setEnabled(False)
        
        QMessageBox.information(self, "Завершено", message)
    
    def on_error(self, error_message):
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage("Ошибка")
        self.log_widget.add_message(f"ОШИБКА: {error_message}")
        QMessageBox.critical(self, "Ошибка", error_message)
    
    def show_about(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()