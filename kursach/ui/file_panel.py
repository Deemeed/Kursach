from PyQt6.QtWidgets import QTreeView, QMenu, QApplication, QMessageBox
from PyQt6.QtGui import QFileSystemModel, QDrag
from PyQt6.QtCore import QDir, Qt, QMimeData, QUrl
import os

from kursach.core.file_ops import open_item


class FilePanel(QTreeView):
    def __init__(self, start_path: str):
        super().__init__()

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.model.setRootPath(start_path)

        self.setModel(self.model)
        self.setRootIndex(self.model.index(start_path))

        self.mousePressEventOriginal = super().mousePressEvent
        self.setSelectionMode(self.SelectionMode.ExtendedSelection)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self.doubleClicked.connect(self.on_double_click)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setColumnWidth(0, 250)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 100)

    def set_directory(self, path: str):
        try:
            self.setRootIndex(self.model.index(path))
        except:
            pass

    def refresh(self):
        try:
            path = self.current_path()
            if os.path.exists(path):
                self.model.setRootPath("")
                self.model.setRootPath(path)
        except:
            pass

    def current_path(self):
        return self.model.filePath(self.rootIndex())

    def selected_paths(self):
        return [self.model.filePath(idx) for idx in self.selectionModel().selectedRows()]

    def selected_path(self):
        paths = self.selected_paths()
        return paths[0] if paths else None

    def on_double_click(self, index):
        try:
            path = self.model.filePath(index)
            if self.model.isDir(index):
                self.set_directory(path)
            else:
                open_item(path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть: {str(e)}")

    def startDrag(self, supportedActions):
        try:
            paths = self.selected_paths()
            if paths:
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
                drag = QDrag(self)
                drag.setMimeData(mime)
                drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        except:
            pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                target_dir = self.current_path()

                drop_ok = True
                for url in urls:
                    src = url.toLocalFile()
                    src_dir = os.path.dirname(src)
                    if src_dir == target_dir:
                        drop_ok = False
                        break

                if drop_ok:
                    for url in urls:
                        src = url.toLocalFile()
                        if os.path.exists(src):
                            from kursach.core.file_ops import copy_item
                            copy_item(src, target_dir)

                    self.refresh()

                event.acceptProposedAction()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось вставить файлы: {str(e)}")

    def show_context_menu(self, pos):
        try:
            menu = QMenu()
            paths = self.selected_paths()

            if paths:
                menu.addAction("Открыть", lambda: self.on_double_click(self.currentIndex()))
                menu.addSeparator()
                menu.addAction("Копировать", self.copy_to_clipboard)
                menu.addAction("Копировать как путь", self.copy_path)
                menu.addSeparator()
                menu.addAction("Вставить", self.paste_from_clipboard)
                menu.addSeparator()
                menu.addAction("Удалить", self.delete_selected)
                menu.addAction("Переименовать", self.rename_selected)
                menu.addAction("Свойства", self.show_properties)
                menu.addAction("Предпросмотр", self.show_preview)
            else:
                menu.addAction("Создать папку", self.create_folder)
                menu.addAction("Вставить", self.paste_from_clipboard)
                menu.addSeparator()
                menu.addAction("Обновить", self.refresh)

            menu.exec(self.viewport().mapToGlobal(pos))
        except:
            pass

    def copy_to_clipboard(self):
        main_window = self.window()
        if hasattr(main_window, 'copy_to_clipboard'):
            main_window.copy_to_clipboard()

    def copy_path(self):
        try:
            paths = self.selected_paths()
            if paths:
                QApplication.clipboard().setText("\n".join(paths))
        except:
            pass

    def paste_from_clipboard(self):
        main_window = self.window()
        if hasattr(main_window, 'paste_from_clipboard'):
            main_window.paste_from_clipboard()

    def create_folder(self):
        main_window = self.window()
        if hasattr(main_window, 'create_item'):
            main_window.create_item()

    def delete_selected(self):
        main_window = self.window()
        if hasattr(main_window, 'delete_item'):
            main_window.delete_item()

    def rename_selected(self):
        main_window = self.window()
        if hasattr(main_window, 'rename_item'):
            main_window.rename_item()

    def show_properties(self):
        main_window = self.window()
        if hasattr(main_window, 'show_properties'):
            main_window.show_properties()

    def show_preview(self):
        main_window = self.window()
        if hasattr(main_window, 'show_preview'):
            main_window.show_preview()