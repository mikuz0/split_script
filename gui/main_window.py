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

class SplitWorker(QThread):
    """Рабочий поток для разбиения файла"""
    
    progress = pyqtSignal(int, int, str)  # current, total, filepath
    finished = pyqtSignal(list)  # created_files
    error = pyqtSignal(str)  # error_message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, filepath, output_dir, settings, mode='split'):
        super().__init__()
        self.filepath = filepath
        self.output_dir = output_dir
        self.settings = settings
        self.mode = mode  # 'split' или 'clean'
    
    def run(self):
        """Запуск обработки"""
        try:
            splitter = FileSplitter()
            
            # Настраиваем процессор
            splitter.set_processor_config(settings=self.settings)
            
            # Загружаем файл
            text = splitter.load_file(self.filepath)
            
            # Проверяем наличие скрытых символов
            processor = TextProcessor()
            processor.set_remove_invisible(True)
            invisible_info = processor.get_invisible_chars_info(text)
            
            if invisible_info['has_invisible']:
                self.log.emit("⚠️ ВНИМАНИЕ: Обнаружены скрытые символы в тексте!")
                for sample in invisible_info['samples']:
                    self.log.emit(f"   - {sample['name']} ({sample['code']})")
            
            if self.mode == 'split':
                # Режим разбиения на файлы
                sections = splitter.split_text(text)
                
                if not sections:
                    self.error.emit("В тексте не найдено маркеров")
                    return
                
                # Сохраняем разделы
                created_files = splitter.save_sections(
                    sections,
                    self.filepath,
                    self.output_dir,
                    self.progress.emit
                )
                self.finished.emit(created_files)
                
            else:  # mode == 'clean'
                # Режим простой очистки
                cleaned_text = splitter.clean_whole_file(text)
                
                # Сохраняем очищенный текст
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
        self.current_mode = 'split'  # 'split' или 'clean'
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Text Splitter - Разбиение и очистка текста")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель (управление файлами)
        top_panel = self.create_top_panel()
        main_layout.addLayout(top_panel)
        
        # Панель выбора режима
        mode_panel = self.create_mode_panel()
        main_layout.addLayout(mode_panel)
        
        # Основной сплиттер (горизонтальный)
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - предпросмотр
        self.preview_widget = PreviewWidget()
        splitter.addWidget(self.preview_widget)
        
        # Правая панель - настройки и лог
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.on_settings_changed)
        right_layout.addWidget(self.settings_panel)
        
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget)
        
        splitter.addWidget(right_widget)
        
        # Устанавливаем пропорции
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        # Нижняя панель (кнопки действий)
        bottom_panel = self.create_bottom_panel()
        main_layout.addLayout(bottom_panel)
        
        # Статус бар
        self.statusBar().showMessage("Готов")
    
    def create_mode_panel(self):
        """Создание панели выбора режима"""
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Режим работы:"))
        
        # Группа радио-кнопок
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
        """Создание верхней панели"""
        layout = QHBoxLayout()
        
        # Кнопка открыть файл
        self.open_btn = self.create_button("Открыть файл", self.open_file)
        layout.addWidget(self.open_btn)
        
        # Путь к файлу
        self.file_path_label = self.create_label("Файл не выбран")
        layout.addWidget(self.file_path_label)
        
        layout.addStretch()
        
        # Кнопка выбрать папку
        self.output_btn = self.create_button("Папка сохранения", self.select_output_dir)
        layout.addWidget(self.output_btn)
        
        # Путь к папке
        self.output_path_label = self.create_label("Не выбрана")
        layout.addWidget(self.output_path_label)
        
        return layout
    
    def create_bottom_panel(self):
        """Создание нижней панели"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        # Кнопка запуска
        self.run_btn = self.create_button("Выполнить", self.run_split)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        
        # Кнопка создания профиля очистки
        cleanup_btn = self.create_button("🧹 Создать профиль очистки", self.create_cleanup_profile)
        layout.addWidget(cleanup_btn)
        
        # Кнопка о программе
        about_btn = self.create_button("О программе", self.show_about)
        layout.addWidget(about_btn)
        
        return layout
    
    def create_button(self, text, callback):
        """Создание кнопки"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn
    
    def create_label(self, text):
        """Создание метки"""
        label = QLabel(text)
        label.setStyleSheet("QLabel { color: #666; }")
        return label
    
    def on_mode_changed(self):
        """Обработчик изменения режима"""
        if self.split_radio.isChecked():
            self.current_mode = 'split'
            self.statusBar().showMessage("Режим: разбиение на файлы по маркерам")
        else:
            self.current_mode = 'clean'
            self.statusBar().showMessage("Режим: простая очистка текста (без разбиения)")
        
        # Обновляем предпросмотр
        if self.current_file:
            self.on_settings_changed()
    
    def create_cleanup_profile(self):
        """Создать профиль агрессивной очистки"""
        profile_name = "Очистка от мусора"
        profiles_dir = "profiles"
        
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        
        profile_path = os.path.join(profiles_dir, f"{profile_name}.json")
        
        # Настройки для агрессивной очистки
        cleanup_settings = {
            'marker_pattern': r'^\s*(\d+)\.\s*',
            'marker_description': 'Цифры с точкой (1., 2., ...)',
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
            
            # Обновляем список профилей
            self.settings_panel.load_profiles_list()
            
            # Загружаем созданный профиль
            self.settings_panel.set_settings(cleanup_settings)
            
            QMessageBox.information(
                self,
                "Профиль создан",
                f"Профиль '{profile_name}' успешно создан!\n\n"
                "Настройки профиля:\n"
                "• Удаление всех видов скобок\n"
                "• Удаление скрытых символов\n"
                "• Удаление надстрочных символов (¹²³)\n"
                "• Удаление спецсимволов (†‡*§¶)\n"
                "• Агрессивная очистка текста"
            )
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать профиль: {e}")
    
    def open_file(self):
        """Открыть файл"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите текстовый файл",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if filepath:
            self.current_file = filepath
            self.file_path_label.setText(os.path.basename(filepath))
            self.statusBar().showMessage(f"Загружен файл: {filepath}")
            
            # Загружаем и отображаем текст
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Проверяем наличие скрытых символов
                processor = TextProcessor()
                invisible_info = processor.get_invisible_chars_info(text)
                
                if invisible_info['has_invisible']:
                    # Выводим предупреждение в лог
                    self.log_widget.add_message("⚠️ ВНИМАНИЕ: Обнаружены скрытые символы в тексте!")
                    for sample in invisible_info['samples']:
                        self.log_widget.add_message(
                            f"   - {sample['name']} ({sample['code']}) - '{sample['char']}'"
                        )
                    
                    # Показываем диалог с предупреждением
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Обнаружены скрытые символы")
                    msg.setText("В загруженном файле обнаружены скрытые символы!\n\n"
                                "Они могут мешать правильной обработке текста.\n\n"
                                f"Найдено:\n")
                    for sample in invisible_info['samples'][:5]:
                        msg.setText(msg.text() + f"• {sample['name']} ({sample['code']})\n")
                    if len(invisible_info['samples']) > 5:
                        msg.setText(msg.text() + f"и еще {len(invisible_info['samples']) - 5}...\n")
                    msg.setText(msg.text() + "\nРекомендуется использовать профиль 'Очистка от мусора'.")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                
                self.preview_widget.set_original_text(text)
                self.check_run_enabled()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")
    
    def select_output_dir(self):
        """Выбрать папку для сохранения"""
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения"
        )
        
        if output_dir:
            self.output_dir = output_dir
            self.output_path_label.setText(output_dir)
            # Обновляем настройки
            settings = self.settings_panel.get_settings()
            settings['output_dir'] = output_dir
            self.settings_panel.set_settings(settings)
            self.check_run_enabled()
    
    def check_run_enabled(self):
        """Проверить, можно ли запустить обработку"""
        enabled = self.current_file is not None and self.output_dir is not None
        self.run_btn.setEnabled(enabled)
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        if self.current_file:
            # Обновляем предпросмотр
            try:
                splitter = FileSplitter()
                
                # Получаем настройки
                settings = self.settings_panel.get_settings()
                
                # Если в настройках есть output_dir, обновляем его в интерфейсе
                if 'output_dir' in settings and settings['output_dir']:
                    self.output_dir = settings['output_dir']
                    self.output_path_label.setText(settings['output_dir'])
                    self.check_run_enabled()
                
                # Применяем настройки
                splitter.set_processor_config(settings=settings)
                
                # Загружаем текст
                text = splitter.load_file(self.current_file)
                
                if self.current_mode == 'split':
                    # Разбиваем и показываем предпросмотр
                    sections = splitter.split_text(text)
                    self.preview_widget.set_sections(sections)
                else:
                    # Простая очистка - показываем очищенный текст
                    cleaned_text = splitter.clean_whole_file(text)
                    # Создаем временный список для отображения
                    self.preview_widget.set_sections([("Очищенный текст", cleaned_text)])
                
            except Exception as e:
                self.log_widget.add_message(f"Ошибка предпросмотра: {e}")
    
    def run_split(self):
        """Запуск обработки"""
        if not self.current_file or not self.output_dir:
            return
        
        # Получаем настройки
        settings = self.settings_panel.get_settings()
        
        # Очищаем лог
        self.log_widget.clear()
        
        # Блокируем кнопку
        self.run_btn.setEnabled(False)
        self.statusBar().showMessage("Обработка...")
        
        # Создаем и запускаем рабочий поток
        self.worker = SplitWorker(
            self.current_file, 
            self.output_dir, 
            settings,
            mode=self.current_mode
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.log.connect(self.log_widget.add_message)
        self.worker.start()
    
    def on_progress(self, current, total, filepath):
        """Обработчик прогресса"""
        self.log_widget.add_message(f"Создан файл: {os.path.basename(filepath)}")
        self.statusBar().showMessage(f"Обработано {current} из {total}...")
    
    def on_finished(self, created_files):
        """Обработчик завершения"""
        self.run_btn.setEnabled(True)
        
        if self.current_mode == 'split':
            self.statusBar().showMessage(f"Готово! Создано файлов: {len(created_files)}")
            self.log_widget.add_message(f"Обработка завершена. Создано {len(created_files)} файлов.")
            message = f"Разбиение завершено!\nСоздано файлов: {len(created_files)}\nПапка: {self.output_dir}"
        else:
            self.statusBar().showMessage(f"Готово! Очищенный текст сохранен")
            self.log_widget.add_message(f"Очистка завершена. Файл сохранен: {os.path.basename(created_files[0])}")
            message = f"Очистка текста завершена!\nФайл сохранен: {os.path.basename(created_files[0])}\nПапка: {self.output_dir}"
        
        QMessageBox.information(
            self,
            "Завершено",
            message
        )
    
    def on_error(self, error_message):
        """Обработчик ошибки"""
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage("Ошибка")
        self.log_widget.add_message(f"ОШИБКА: {error_message}")
        QMessageBox.critical(self, "Ошибка", error_message)
    
    def show_about(self):
        """Показать окно 'О программе'"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()