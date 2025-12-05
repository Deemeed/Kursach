import os
import platform
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeView, QTableView, QToolBar,
    QLineEdit, QLabel, QPushButton, QFileDialog,
    QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtGui import QFileSystemModel, QAction
from PyQt6.QtCore import QDir, QModelIndex, Qt, QSortFilterProxyModel, QRegularExpression

from kursach.core import file_ops


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Файловый менеджер")
        self.resize(1200, 750)

        self.current_path = "C:/"

        # Шапка
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # кнопка назад
        back_action = QAction("← Назад", self)
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)

        create_action = QAction("+ Создать", self)
        create_action.triggered.connect(self.action_create_folder)
        toolbar.addAction(create_action)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Путь:"))

        # адресная строка
        self.address_edit = QLineEdit()
        self.address_edit.setText(self.current_path)
        self.address_edit.returnPressed.connect(self.on_address_entered)
        self.address_edit.setMaximumWidth(700)
        toolbar.addWidget(self.address_edit)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Поиск:"))

        # строка поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Найти…")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.setMaximumWidth(300)
        toolbar.addWidget(self.search_edit)

        # Основное окно
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Кнопки
        buttons_widget = QWidget()
        btn_layout = QHBoxLayout(buttons_widget)
        btn_layout.setContentsMargins(4, 4, 4, 4)

        self.btn_rename = QPushButton("Переименовать")
        self.btn_copy = QPushButton("Копировать")
        self.btn_delete = QPushButton("Удалить")
        self.btn_props = QPushButton("Свойства")

        for b in (self.btn_rename, self.btn_copy, self.btn_delete, self.btn_props):
            b.setEnabled(False)
            btn_layout.addWidget(b)

        # действия кнопок
        self.btn_rename.clicked.connect(self.action_rename)
        self.btn_copy.clicked.connect(self.action_copy)
        self.btn_delete.clicked.connect(self.action_delete)
        self.btn_props.clicked.connect(self.action_properties)

        # Левое окно
        self.dir_model = QFileSystemModel()
        self.dir_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self.dir_model.setRootPath("C:/")

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index("C:/"))
        self.tree_view.setColumnWidth(0, 300)

        for i in range(1, 4):
            self.tree_view.hideColumn(i)

        self.tree_view.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)

        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.on_tree_context_menu)

        # Правое окно
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.file_model.setRootPath(self.current_path)

        # Поиск
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setRootIndex(
            self.proxy_model.mapFromSource(self.file_model.index(self.current_path))
        )

        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(self.table_view.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(self.table_view.SelectionMode.SingleSelection)

        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # контекстное меню
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_table_context_menu)

        left_right = QHBoxLayout()
        left_right.addWidget(self.tree_view, 1)
        left_right.addWidget(self.table_view, 3)

        wrapper = QVBoxLayout()
        wrapper.addWidget(buttons_widget)
        wrapper.addLayout(left_right)

        main_layout.addLayout(wrapper)
        self.update_address(self.current_path)

    def update_address(self, path: str):
        self.current_path = path
        self.address_edit.setText(path)

        source_index = self.file_model.index(path)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        self.table_view.setRootIndex(proxy_index)

        # обновляется слева
        try:
            dir_index = self.dir_model.index(path)
            if dir_index.isValid():
                self.tree_view.setCurrentIndex(dir_index)
        except Exception:
            pass

    def go_back(self):
        new_path = os.path.dirname(self.current_path.rstrip("/"))

        if new_path.endswith(":"):
            new_path += "/"

        if len(new_path) > 2:
            self.update_address(new_path)

    # обновляется справа
    def on_tree_selection_changed(self, s, d):
        index = self.tree_view.currentIndex()
        path = self.dir_model.filePath(index)

        if os.path.isdir(path):
            self.update_address(path)

    # двойной клик
    def on_table_double_clicked(self, proxy_index):
        src_index = self.proxy_model.mapToSource(proxy_index)
        path = self.file_model.filePath(src_index)

        if os.path.isdir(path):
            self.update_address(path)
            return

        try:
            os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    # поиск
    def on_search_text_changed(self, text: str):
        text = text.strip()
        if text == "":
            self.proxy_model.setFilterRegularExpression(QRegularExpression())
            return

        # Экранируем текст и формируем "contains" регулярное выражение
        escaped = QRegularExpression.escape(text)
        pattern = QRegularExpression(f".*{escaped}.*", QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(pattern)

        # ВАЖНО: после смены фильтра убедимся, что rootIndex proxy всё ещё указывает на текущую директорию
        src_index = self.file_model.index(self.current_path)
        proxy_index = self.proxy_model.mapFromSource(src_index)
        if proxy_index.isValid():
            self.table_view.setRootIndex(proxy_index)

    # ввод пути в адресную строку
    def on_address_entered(self):
        path = self.address_edit.text()
        if os.path.isdir(path):
            self.update_address(file_ops.normalize(path))
        else:
            QMessageBox.warning(self, "Ошибка", "Путь не существует.")

    # выделение
    def on_selection_changed(self, s, d):
        selected = self.get_selected_paths()
        enable = len(selected) > 0
        for b in (self.btn_rename, self.btn_copy, self.btn_delete, self.btn_props):
            b.setEnabled(enable)

    # получает пути выделенных элементов
    def get_selected_paths(self):
        rows = self.table_view.selectionModel().selectedRows()
        paths = []
        for proxy_index in rows:
            src = self.proxy_model.mapToSource(proxy_index)
            paths.append(self.file_model.filePath(src))
        return paths

    # Действия:
    def action_rename(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        path = paths[0]
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Переименование", "Новое имя:", text=old_name)
        if not ok or not new_name:
            return

        try:
            file_ops.rename_item(path, new_name)
            self.update_address(self.current_path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def action_copy(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        dst_dir = QFileDialog.getExistingDirectory(self, "Куда копировать?")
        if not dst_dir:
            return

        for p in paths:
            try:
                file_ops.copy_item(p, dst_dir)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))

        self.update_address(self.current_path)

    def action_delete(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить {len(paths)} элемент(ов)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        for p in paths:
            try:
                file_ops.delete_item(p)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))

        self.update_address(self.current_path)

    def action_properties(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        props = file_ops.get_properties(paths[0])
        msg = (f"Путь: {props['path']}\n"
               f"Тип: {'Папка' if props['is_dir'] else 'Файл'}\n"
               f"Размер (байт): {props['size']}\n"
               f"Дата изменения: {props['modified']}")
        QMessageBox.information(self, "Свойства", msg)

    def action_create_folder(self):
        name, ok = QInputDialog.getText(self, "Создать папку", f"Создание новой папки в {self.current_path}:", text="Новая папка")
        if not ok or not name:
            return
        try:
            new_path = file_ops.create_folder(self.current_path, name)
            self.update_address(self.current_path)
            QMessageBox.information(self, "Создано", f"Папка создана: {new_path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка создания папки", str(e))

    # контекстное меню
    def on_table_context_menu(self, point):
        if not self.get_selected_paths():
            return
        menu = QMenu(self)
        menu.addAction("Переименовать", self.action_rename)
        menu.addAction("Копировать", self.action_copy)
        menu.addAction("Удалить", self.action_delete)
        menu.addAction("Свойства", self.action_properties)
        menu.exec(self.table_view.mapToGlobal(point))

    def on_tree_context_menu(self, point):
        index = self.tree_view.indexAt(point)
        if not index.isValid():
            return

        self.tree_view.setCurrentIndex(index)
        self.current_path = self.dir_model.filePath(index)

        menu = QMenu(self)
        menu.addAction("Переименовать", self.action_rename)
        menu.addAction("Копировать", self.action_copy)
        menu.addAction("Удалить", self.action_delete)
        menu.addAction("Свойства", self.action_properties)
        menu.exec(self.tree_view.mapToGlobal(point))
