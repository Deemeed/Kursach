import os
import hashlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget,
    QMessageBox, QCheckBox, QLabel
)
from PyQt6.QtCore import QTimer


class SearchDialog(QDialog):
    def __init__(self, start_dir: str):
        super().__init__()
        self.setWindowTitle("Поиск файлов и дубликатов")
        self.resize(600, 500)
        self.start_dir = start_dir
        self.selected_path = None
        self.duplicate_mode = False

        layout = QVBoxLayout(self)

        search_panel = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Имя файла или папки")

        self.btn_search = QPushButton("Найти по имени")
        self.btn_search.clicked.connect(lambda: self.search_by_name())

        self.btn_duplicates = QPushButton("Найти дубликаты")
        self.btn_duplicates.clicked.connect(lambda: self.find_duplicates())

        search_panel.addWidget(self.input)
        search_panel.addWidget(self.btn_search)
        search_panel.addWidget(self.btn_duplicates)

        options_panel = QHBoxLayout()

        self.chk_subfolders = QCheckBox("Искать в подпапках")
        self.chk_subfolders.setChecked(True)

        self.chk_by_size = QCheckBox("Сравнивать по размеру")
        self.chk_by_size.setChecked(True)

        self.chk_by_content = QCheckBox("Сравнивать по содержимому")
        self.chk_by_content.setChecked(True)

        options_panel.addWidget(self.chk_subfolders)
        options_panel.addStretch()
        options_panel.addWidget(self.chk_by_size)
        options_panel.addWidget(self.chk_by_content)

        self.list = QListWidget()

        self.status_label = QLabel("Готов к поиску")

        self.btn_goto = QPushButton("Перейти к файлу")
        self.btn_goto.clicked.connect(self.goto_selected)

        layout.addLayout(search_panel)
        layout.addLayout(options_panel)
        layout.addWidget(self.list)
        layout.addWidget(self.status_label)
        layout.addWidget(self.btn_goto)

        self.input.returnPressed.connect(self.search_by_name)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)

    def search_by_name(self):
        self.duplicate_mode = False
        self.list.clear()
        text = self.input.text().lower()

        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите текст для поиска")
            return

        if not os.path.exists(self.start_dir):
            QMessageBox.warning(self, "Ошибка", f"Директория не существует: {self.start_dir}")
            return

        self.status_label.setText("Идет поиск...")
        found = 0

        if self.chk_subfolders.isChecked():
            for root, dirs, files in os.walk(self.start_dir):
                for name in dirs + files:
                    if text in name.lower():
                        self.list.addItem(os.path.join(root, name))
                        found += 1
        else:
            try:
                items = os.listdir(self.start_dir)
                for name in items:
                    full_path = os.path.join(self.start_dir, name)
                    if os.path.exists(full_path) and text in name.lower():
                        self.list.addItem(full_path)
                        found += 1
            except:
                pass

        self.status_label.setText(f"Найдено: {found} объектов")
        self.setWindowTitle(f"Поиск файлов ({found} найдено)")

    def find_duplicates(self):
        self.duplicate_mode = True
        self.list.clear()

        if not os.path.exists(self.start_dir):
            QMessageBox.warning(self, "Ошибка", f"Директория не существует: {self.start_dir}")
            return

        self.status_label.setText("Поиск дубликатов...")
        self.btn_duplicates.setEnabled(False)

        duplicates = self._find_duplicates_simple(self.start_dir)

        total_files = 0
        total_groups = 0

        for group in duplicates:
            if len(group) > 1:
                total_groups += 1

                self.list.addItem(f"────────── Группа {total_groups} ({len(group)} файлов) ──────────")

                for filepath in group:
                    self.list.addItem(f"  📄 {filepath}")
                    total_files += 1

        if total_groups == 0:
            self.list.addItem("Дубликаты не найдены")
            self.status_label.setText("Дубликаты не найдены")
        else:
            self.status_label.setText(f"Найдено {total_groups} групп дубликатов ({total_files} файлов)")
            self.setWindowTitle(f"Дубликаты ({total_groups} групп)")

        self.btn_duplicates.setEnabled(True)

    def _find_duplicates_simple(self, directory):
        files_by_size = {}

        walk_dir = directory if self.chk_subfolders.isChecked() else [directory]

        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                try:
                    filepath = os.path.join(root, filename)
                    size = os.path.getsize(filepath)

                    if size < 1024:
                        continue

                    if size not in files_by_size:
                        files_by_size[size] = []
                    files_by_size[size].append(filepath)
                except:
                    continue

        potential_duplicates = []

        for size, filepaths in files_by_size.items():
            if len(filepaths) > 1:
                if self.chk_by_content.isChecked():
                    hash_groups = {}
                    for filepath in filepaths:
                        try:
                            with open(filepath, 'rb') as f:
                                # первые 4KB
                                first_bytes = f.read(4096)
                                file_hash = hashlib.md5(first_bytes).hexdigest()

                                if file_hash not in hash_groups:
                                    hash_groups[file_hash] = []
                                hash_groups[file_hash].append(filepath)
                        except:
                            continue

                    for filepaths_group in hash_groups.values():
                        if len(filepaths_group) > 1:
                            potential_duplicates.append(filepaths_group)
                else:
                    potential_duplicates.append(filepaths)

        return potential_duplicates

    def update_status(self):
        current_text = self.status_label.text()
        if current_text.endswith("..."):
            self.status_label.setText(current_text[:-3])
        else:
            self.status_label.setText(current_text + ".")

    def goto_selected(self):
        item = self.list.currentItem()
        if item:
            text = item.text()

            if "──────────" in text:
                return

            if text.startswith("  📄 "):
                text = text[5:]

            if os.path.exists(text):
                self.selected_path = text
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Файл не найден")

    def closeEvent(self, event):
        self.status_timer.stop()
        super().closeEvent(event)