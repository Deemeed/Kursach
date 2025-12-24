import os
import traceback
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QPushButton,
    QMessageBox, QInputDialog, QApplication
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QUrl

from kursach.ui.search_dialog import SearchDialog
from kursach.ui.file_panel import FilePanel
from kursach.core import file_ops
from kursach.ui.preview_dialog import PreviewDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Manager")
        self.resize(1200, 700)

        self.active_panel = None
        self.clipboard_paths = []

        # Шапка
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.path_label = QLabel()

        toolbar.addAction(QAction("←", self, triggered=self.go_back))
        toolbar.addAction(QAction("Создать", self, triggered=self.create_item))
        toolbar.addAction(QAction("Удалить", self, triggered=self.delete_item))
        toolbar.addAction(QAction("Переименовать", self, triggered=self.rename_item))
        toolbar.addAction(QAction("Копировать", self, triggered=self.copy_to_clipboard))
        toolbar.addAction(QAction("Свойства", self, triggered=self.show_properties))
        toolbar.addAction(QAction("Поиск", self, triggered=self.open_search))
        toolbar.addSeparator()
        toolbar.addWidget(self.path_label)

        # Две файлов
        self.left_panel = FilePanel(os.path.expanduser("~"))
        self.right_panel = FilePanel("D:/" if os.path.exists("D:/") else os.path.expanduser("~"))

        self.left_panel.mousePressEvent = lambda e: self.panel_clicked(self.left_panel, e)
        self.right_panel.mousePressEvent = lambda e: self.panel_clicked(self.right_panel, e)

        # Средняя плашка
        middle = QVBoxLayout()
        btn_copy = QPushButton("▶")
        btn_move = QPushButton("↔")
        btn_preview = QPushButton("p")
        btn_copy.clicked.connect(self.copy_between)
        btn_move.clicked.connect(self.move_between)
        btn_preview.clicked.connect(self.show_preview)

        btn_copy.setFixedWidth(30)
        btn_move.setFixedWidth(30)
        btn_preview.setFixedWidth(30)

        middle.addStretch()
        middle.addWidget(btn_copy)
        middle.addWidget(btn_move)
        middle.addWidget(btn_preview)
        middle.addStretch()

        center = QHBoxLayout()
        center.addWidget(self.left_panel)
        center.addLayout(middle)
        center.addWidget(self.right_panel)

        container = QWidget()
        container.setLayout(center)
        self.setCentralWidget(container)

        self.set_active(self.left_panel)

    def panel_clicked(self, panel, event):
        self.set_active(panel)
        panel.mousePressEventOriginal(event)

    def set_active(self, panel):
        if self.active_panel != panel:
            if self.active_panel:
                self.active_panel.setStyleSheet("")

            self.active_panel = panel
            self.path_label.setText(panel.current_path())
            panel.setStyleSheet("border: 2px solid #0078d7;")

    def passive_panel(self):
        return self.right_panel if self.active_panel == self.left_panel else self.left_panel

    def go_back(self):
        try:
            path = self.active_panel.current_path()
            parent = os.path.dirname(path)
            if parent:
                self.active_panel.set_directory(parent)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось перейти назад: {str(e)}")

    def create_item(self):
        try:
            name, ok = QInputDialog.getText(self, "Создать", "Имя файла или папки:")
            if ok and name:
                forbidden_chars = '<>:"/\\|?*'
                for char in forbidden_chars:
                    if char in name:
                        QMessageBox.warning(self, "Ошибка",
                                            f"Имя содержит запрещенный символ: '{char}'\n"
                                            f"Запрещенные символы: {forbidden_chars}")
                        return

                path = os.path.join(self.active_panel.current_path(), name)

                if os.path.exists(path):
                    QMessageBox.warning(self, "Ошибка", "Файл или папка с таким именем уже существует")
                    return

                if "." in name:
                    open(path, 'w').close()
                else:
                    os.makedirs(path)

                self.active_panel.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать: {str(e)}")

    def delete_item(self):
        try:
            paths = self.active_panel.selected_paths()
            if paths:
                reply = QMessageBox.question(self, "Удалить", f"Удалить {len(paths)} объектов?")
                if reply == QMessageBox.StandardButton.Yes:
                    for path in paths:
                        file_ops.delete_item(path)
                    self.active_panel.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить: {str(e)}")

    def rename_item(self):
        try:
            path = self.active_panel.selected_path()
            if path:
                name = os.path.basename(path)
                new, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", text=name)
                if ok and new:
                    forbidden_chars = '<>:"/\\|?*'
                    for char in forbidden_chars:
                        if char in new:
                            QMessageBox.warning(self, "Ошибка",
                                                f"Имя содержит запрещенный символ: '{char}'")
                            return

                    parent = os.path.dirname(path)
                    new_path = os.path.join(parent, new)
                    if os.path.exists(new_path):
                        QMessageBox.warning(self, "Ошибка", "Файл с таким именем уже существует")
                        return

                    file_ops.rename_item(path, new)
                    self.active_panel.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось переименовать: {str(e)}")

    def copy_to_clipboard(self):
        try:
            paths = self.active_panel.selected_paths()
            if paths:
                self.clipboard_paths = paths.copy()

                mime_data = QApplication.clipboard().mimeData()
                urls = [QUrl.fromLocalFile(p) for p in paths]
                mime_data.setUrls(urls)

                count = len(paths)
                names = ", ".join([os.path.basename(p) for p in paths[:3]])
                if count > 3:
                    names += f" и еще {count - 3}"
                QMessageBox.information(self, "Копирование", f"Скопировано {count} объектов: {names}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось скопировать: {str(e)}")

    def paste_from_clipboard(self):
        try:
            if self.clipboard_paths:
                target_dir = self.active_panel.current_path()

                for src in self.clipboard_paths:
                    if os.path.exists(src):
                        file_ops.copy_item(src, target_dir)

                self.active_panel.refresh()
                QMessageBox.information(self, "Вставка", f"Вставлено {len(self.clipboard_paths)} объектов")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось вставить: {str(e)}")

    def show_properties(self):
        try:
            path = self.active_panel.selected_path()
            if path:
                info = file_ops.get_properties(path)

                text = f"Путь: {info['path']}\nТип: {info['type']}\nРазмер: {info['size']} байт\nИзменён: {info['modified']}"

                if 'signature' in info and info['signature']:
                    text += f"\n\nЦифровая подпись: {info['signature']}"

                QMessageBox.information(self, "Свойства", text)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось показать свойства: {str(e)}")

    def copy_between(self):
        try:
            paths = self.active_panel.selected_paths()
            if paths:
                file_ops.copy_items(paths, self.passive_panel().current_path())
                self.passive_panel().refresh()
                QMessageBox.information(self, "Копирование", f"Скопировано {len(paths)} объектов")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось скопировать: {str(e)}")

    def move_between(self):
        try:
            paths = self.active_panel.selected_paths()
            if paths:
                file_ops.move_items(paths, self.passive_panel().current_path())
                self.active_panel.refresh()
                self.passive_panel().refresh()
                QMessageBox.information(self, "Перемещение", f"Перемещено {len(paths)} объектов")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось переместить: {str(e)}")

    def show_preview(self):
        try:
            path = self.active_panel.selected_path()
            if path:
                dlg = PreviewDialog(path)
                dlg.exec()
            else:
                QMessageBox.information(self, "Предпросмотр", "Выберите файл для предпросмотра")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть предпросмотр: {str(e)}")

    def open_search(self):
        try:
            dlg = SearchDialog(self.active_panel.current_path())
            if dlg.exec():
                if dlg.selected_path and os.path.exists(dlg.selected_path):
                    target_dir = os.path.dirname(dlg.selected_path)
                    self.active_panel.set_directory(target_dir)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить поиск: {str(e)}")

    def keyPressEvent(self, event):
        if event.modifiers() == self.keyboardModifiers().ControlModifier and event.key() == 86:
            self.paste_from_clipboard()
        else:
            super().keyPressEvent(event)